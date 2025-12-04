import socket

import mysql.connector
from email_validator import EmailNotValidError, validate_email
from mysql.connector import errorcode

from src.smtp.db.config import conn
from src.smtp.smtpd import CommandSpecifier
from src.smtp.log_hierarchy import transc
from src.smtp.transc_log import setup_logger

# Setup logging module 'transcations'
log_file = transc.create_log()
logger = setup_logger(log_filepath=log_file)

version = "1.0.0"
softwareAndVersion = f"richmail {version}"

# < stateIndependentCommands >
# these commands can be used at any time during a session,
# or without previously initializing a session.

stateIndependentCommands = ["NOOP", "HELP", "EXPN", "VRFY", "RSET"]


class QuitLoopException(Exception):
    pass


class SMTPTimeoutError(Exception):
    pass



class ESMTPServer:
    # Recipients Limit
    RECIPIENTS_LIMIT:int = 100
    transcationState = "INIT"
    # {"command":"command_DONE"}
    preCommandStates = {
        "EHLO": "EHLO_DONE",
        "MAIL": "MAIL_DONE",
        "RCPT": "RCPT_DONE",
        "DATA": "DATA_DONE",
    }

    mailTranscationObjs = [
        "senderMail",  # only one is strictly allowed
        "recipientMail",  # can be more than one recipient (atmost 100) mails with RCPT command
        "dataBuffer",  # message body of mail
    ]

    # Transcation detail for adding in message queue and for logging
    mailTranscation = {}

    def __init__(self, addressFamily=socket.AF_INET, stream=socket.SOCK_STREAM):
        self.stream = stream
        self.addressFamily = addressFamily

    def sendGreet(self, greetCode=220, softwareAndVersion=softwareAndVersion) -> bytes:
        """return greeting in bytes"""
        greeting = f"{greetCode} {softwareAndVersion} Service ready\r\n"
        greeting = greeting.encode(encoding="utf-8")
        return greeting

    def timeout_raise(self):
        raise SMTPTimeoutError("Client did not respond in time")

    def run(self, HOST="127.0.0.1", PORT=2525):
        logger.info(f"Starting server on {HOST}:{PORT}")
        with socket.socket(self.addressFamily, self.stream) as server:
            logger.debug("Connection Socket is created")
            server.bind((HOST, PORT))
            # listen for one incoming connections
            server.listen(0)

            clientSocket, clientAddress = server.accept()
            logger.debug(f"Connected to client {clientAddress} ")
            with clientSocket:
                try:
                    greeting = self.sendGreet()
                    clientSocket.send(greeting)
                    logger.debug(f"S:{greeting}")
                    # set timeout after sending greeting and
                    #  waiting for the next command
                    # clientSocket.settimeout(10)
                    while True:
                        request = clientSocket.recv(2**10)
                        request = request.decode(encoding="utf-8")

                        requestStripped = request.strip()
                        logger.debug(f"C: {requestStripped}")

                        commandChunk = requestStripped.split(" ")
                        commandInfo = CommandSpecifier(COMMAND=commandChunk[0])
                        identifiedCommand = commandInfo.identiCommand()

                        self.CommandHandler(
                            command=identifiedCommand,
                            commandChunk=commandChunk,
                            connSocket=clientSocket,
                        )

                except QuitLoopException:
                    pass

    def CommandHandler(
        self, command: str, commandChunk: dict, connSocket: socket.socket
    ):
        if command == "EHLO":
            logger.debug(f'Command Identified is : {command}')
            self.EhloCmdHandler(
                command=command, commandTokens=commandChunk, connSocket=connSocket
            )
        elif command == "MAIL":
            logger.debug(f'Command Identified is : {command}')
            self.MailCmdHandler(
                command=command, commandTokens=commandChunk, connSocket=connSocket
            )
        elif command == "RCPT":
            logger.debug(f'Command Identified is : {command}')
            self.RcptCmdHandler(
                command=command, commandTokens=commandChunk, connSocket=connSocket
            )
        elif command == "DATA":
            logger.debug(f'Command Identified is : {command}')
            self.DataCmdHandler(
                command=command, commandTokens=commandChunk, connSocket=connSocket
            )
        elif command == "QUIT":
            logger.debug(f'Command Identified is : {command}')
            self.QuitCmdHanlder(
                command=command, commandTokens=commandChunk, connSocket=connSocket
            )
        else:
            errorMsg = command
            logger.debug(f'Command not recognised: "{errorMsg}"')
            connSocket.send(errorMsg.encode("utf-8"))

    def EhloCmdHandler(
        self,
        command: str,
        commandTokens: dict,
        connSocket: socket.socket,
        timeout: int = 10,
    ):
        if len(commandTokens) > 2:
            logger.debug(f'Unrecognised part from command is: {' '.join(commandTokens[2:])}')
            self.SendError(errorCode=501, clientSocket=connSocket)

        else:
            self.SendSuccess(successCode=250, clientSocket=connSocket)
            self.UpdateState(command=command)

    def MailCmdHandler(
        self,
        command: str,
        commandTokens: dict,
        connSocket: socket.socket,
        timeout: int = 10,
    ):
        commandTokensCount= len(commandTokens)

        if commandTokensCount == 2:
            normalizedCommandToken = commandTokens[1].lower()
            if normalizedCommandToken.startswith("from:"):
                reversePath = normalizedCommandToken[len("from:"):]
                self.HandleReversePath(
                    command=command,
                    reversePath=reversePath,
                    connSocket=connSocket
                )
            else:
                logger.debug(f'Unrecognised part: {normalizedCommandToken}')
                self.SendError(errorCode=555, clientSocket=connSocket)
        elif commandTokensCount == 3:
            normalizedCommandToken = commandTokens[1].lower()
            if not normalizedCommandToken.startswith("from:"):
                logger.debug(f'Unrecognised part: {normalizedCommandToken}')
                self.SendError(errorCode=555, clientSocket=connSocket)
            else:
                reversePath = commandTokens[2]
                self.HandleReversePath(
                    command=command,
                    reversePath=reversePath,
                    connSocket=connSocket
                )
        else:
            logger.debug(f"Unrecognised part is: {" ".join(commandTokens)}")
            self.SendError(errorCode=555, clientSocket=connSocket)


    def HandleReversePath(
        self,
        command:str,
        reversePath:str,
        connSocket: socket.socket,
    ):
        if (reversePath.startswith("<")) and (
            reversePath.endswith(">")
        ):
            senderMailAddress = reversePath[1:-1]
            logger.debug(f'Reverse-Path from Command is: {reversePath}')

            if senderMailAddress:
                try:
                    validSenderAddress = validate_email(
                        senderMailAddress,
                        check_deliverability=True,
                    )


                    # normalise email for session use
                    normalizedSenderAddress = validSenderAddress.normalized
                    logger.debug(f"Normalised Reverse-Path: {normalizedSenderAddress}")

                    # start the session
                    if (
                        self.mailTranscationObjs[0]
                        not in self.mailTranscation.keys()
                    ):
                        self.mailTranscation[self.mailTranscationObjs[0]] = (
                            normalizedSenderAddress
                        )

                    # send SMTP reply and after initializing the transcation
                    self.SendSuccess(successCode=250, clientSocket=connSocket)

                    # update the transcation state for the next command in series
                    self.UpdateState(command=command)

                except EmailNotValidError:
                    self.SendError(errorCode=550, clientSocket=connSocket)

                except Exception:
                    self.SendError(errorCode=550, clientSocket=connSocket)

            else:
                self.SendError(errorCode=553, clientSocket=connSocket)
        else:
            self.SendError(errorCode=555, clientSocket=connSocket)



    def RcptCmdHandler(
        self,
        command: str,
        commandTokens: dict,
        connSocket: socket.socket,
        timeout: int = 5,
    ):
        if (self.transcationState == self.preCommandStates["MAIL"]) or (
            self.mailTranscationObjs[1] in self.mailTranscation
        ):
            commandTokensCount = len(commandTokens)
            if commandTokensCount == 2:
                normalizedCommandToken = commandTokens[1].lower()
                if normalizedCommandToken.startswith("to:"):
                    forwardPath = normalizedCommandToken[len("to:"):]
                    self.HandleForwardPath(
                        command=command,
                        forwardPath=forwardPath,
                        connSocket=connSocket
                    )
                else:
                    logger.debug(f'Unrecognised part: {normalizedCommandToken}')
                    self.SendError(errorCode=501, clientSocket=connSocket)
            elif commandTokensCount == 3:
                normalizedCommandToken = commandTokens[1].lower()
                if not normalizedCommandToken.startswith("to:"):
                    logger.debug(f'Unrecognised part: {normalizedCommandToken}')
                    self.SendError(errorCode=555, clientSocket=connSocket)
                else:
                    forwardPath = commandTokens[2]
                    self.HandleForwardPath(
                        command=command,
                        forwardPath=forwardPath,
                        connSocket=connSocket
                    )
            else:
                logger.debug(f"Unrecognised part is: {" ".join(commandTokens)}")
                self.SendError(errorCode=555, clientSocket=connSocket)


        else:
            logger.debug(f'Command out of order, previous state:{self.transcationState}')
            self.SendError(errorCode=503, clientSocket=connSocket)


    def HandleForwardPath(
        self,
        command:str,
        forwardPath:str,
        connSocket: socket.socket,

    ):
        recipientsListKey = self.mailTranscationObjs[1]
        if recipientsListKey in self.mailTranscation:
            recipientsList = self.mailTranscation[self.mailTranscationObjs[1]]
            # check if recipient list is full
            if len(recipientsList) >= self.RECIPIENTS_LIMIT :
                logger.debug(f'Recipient list is full so bouncing address:{forwardPath}')
                self.SendError(errorCode=452, clientSocket=connSocket)
                return   # don't process ideally after temporary error

        if (forwardPath.startswith("<")) and (
            forwardPath.endswith(">")
        ):
            recipientMailAddress = forwardPath[1:-1]
            logger.debug(f'Forward-Path from Command is: {forwardPath}')

            if recipientMailAddress:
                try:
                    validRecipientAddress = validate_email(
                        recipientMailAddress,
                        check_deliverability=True,
                    )

                    normalizedRecipientAddress = (
                        validRecipientAddress.normalized
                    )
                    logger.debug(f"Normalised Forward-Path: {normalizedRecipientAddress}")

                    if (
                        recipientsListKey
                        not in self.mailTranscation
                    ):
                        self.mailTranscation[
                            recipientsListKey
                        ] = [normalizedRecipientAddress]
                    else:
                        logger.debug(f'Adding more recipients to the mail: {self.mailTranscation[recipientsListKey]}')
                        self.mailTranscation[
                            recipientsListKey
                        ].append(normalizedRecipientAddress)

                    logger.debug(
                        f"Transcation Session Detail: {self.mailTranscation}"
                    )
                    self.SendSuccess(
                        successCode=250, clientSocket=connSocket
                    )

                    self.UpdateState(command=command)

                except EmailNotValidError:
                    logger.debug(f'Email Not Valid: {recipientMailAddress}')
                    self.SendError(errorCode=550, clientSocket=connSocket)

                except Exception as e:
                    logger.exception(f"Exception Occured: {str(e)}")
                    self.SendError(errorCode=550, clientSocket=connSocket)
            else:
                logger.debug("Empty recipient forward path")
                self.SendError(errorCode=553, clientSocket=connSocket)

        else:
            logger.debug(f'Not valid way to enter Forward Path: {forwardPath}')
            self.SendError(errorCode=501, clientSocket=connSocket)


    def DataCmdHandler(
        self,
        command: str,
        commandTokens: dict,
        connSocket: socket.socket,
        timeout: int = 10,
    ):
        if self.transcationState == self.preCommandStates["RCPT"]:
            if len(commandTokens) != 1:
                self.SendError(errorCode=455, clientSocket=connSocket)
            else:
                self.SendSuccess(successCode=354, clientSocket=connSocket)
                self.UpdateState(command=command)

                DataCommandBuffer = ""
                receiveBuffer = ""  # buffer for incomplete lines
                notDataCommandEnd = True

                while notDataCommandEnd:
                    chunk = connSocket.recv(2**10)
                    chunk = chunk.decode(encoding="utf-8")
                    receiveBuffer += chunk

                    # process complete lines (split by \r\n)
                    while "\r\n" in receiveBuffer:
                        line, receiveBuffer = receiveBuffer.split("\r\n", 1)

                        # check for end of data
                        if line == ".":
                            notDataCommandEnd = False
                            break

                        # check for dot stuffing (transparency): removing leading dot
                        elif  line.startswith("."):
                            line = line[len("."):]

                        # add line to buffer
                        DataCommandBuffer += line + "\n"

                # store in transaction
                self.mailTranscation[self.mailTranscationObjs[2]] = DataCommandBuffer

                print(self.mailTranscation)

                self.Insert(
                    sender=self.mailTranscation[self.mailTranscationObjs[0]],
                    receiver=self.mailTranscation[self.mailTranscationObjs[1]],
                    data=self.mailTranscation[self.mailTranscationObjs[2]],
                )

                # clear buffers for next transaction
                self.mailTranscation = {}
                self.SendSuccess(successCode=250, clientSocket=connSocket)
        else:
            self.SendError(errorCode=503, clientSocket=connSocket)

    def QuitCmdHanlder(
        self, command: str, commandTokens: dict, connSocket: socket, timeout: int = 10
    ) -> bool:
        # send response to the client which acknowledges that the
        # connection should be closed and break out of the loop
        if len(commandTokens) != 1:
            self.SendError(errorCode=455, clientSocket=connSocket)

        else:
            self.SendSuccess(successCode=221, clientSocket=connSocket)
            raise QuitLoopException

    def SendError(self, errorCode: int, clientSocket: socket.socket):

        if errorCode == 455:
            errorMsg = f"{errorCode} Server unable to accommodate parameters\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        if errorCode == 500:
            errorMsg = f"{errorCode} Syntax error, command unrecognized\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        if errorCode == 501:
            errorMsg = f"{errorCode} Syntax error in parameters or arguments\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        if errorCode == 503:
            errorMsg = f"{errorCode} Bad sequence of command(s)\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        if errorCode == 550:
            errorMsg = f"{errorCode} Requested action not taken: mailbox unavailable\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        if errorCode == 553:
            errorMsg = (
                f"{errorCode} Requested action not taken: mailbox name not allowed\r\n"
            )
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        if errorCode == 555:
            # syntax error in command
            errorMsg = f"{errorCode} Syntax error, command unrecognized\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

    def SendSuccess(self, successCode: int, clientSocket: socket.socket):
        if successCode == 221:
            successMsg = f"{successCode} OK Closing transmission channel\r\n"
            clientSocket.send(successMsg.encode("utf-8"))
            logger.debug(f'S: {successMsg}')

        if successCode == 250:
            successMsg = f"{successCode} OK Requested mail action okay, completed\r\n"
            clientSocket.send(successMsg.encode("utf-8"))
            logger.debug(f'S: {successMsg}')

        if successCode == 354:
            successMsg = f"{successCode} Start mail input; end with <CRLF>.<CRLF>\r\n"
            clientSocket.send(successMsg.encode("utf-8"))
            logger.debug(f'S: {successMsg}')

    def UpdateState(self, command: str):
        self.transcationState = self.preCommandStates[command]
        logger.debug(f'State is updated to: {self.transcationState}')

    def Insert(self, sender, receiver, data):
        add_mail = "INSERT INTO setu_outbox(sender, receiver, data)VALUES "
        receiverList = len(receiver)
        for recv in range(receiverList):
            if recv < (receiverList - 1):
                add_mail += f"('{sender}', '{receiver[recv]}', '{data}'),"
            else:
                add_mail += f"('{sender}', '{receiver[recv]}', '{data}')"

        try:
            with conn.connect() as cnx:
                conn_cursor = cnx.cursor()
                conn_cursor.execute(add_mail)
                cnx.commit()
                conn_cursor.close()

        except mysql.connector.ProgrammingError as err:
            if err.errno == errorcode.ER_SYNTAX_ERROR:
                print("Check your syntax!")
            else:
                print("Error: {}".format(err))
        except Exception as error:
            print("ERROR: ", str(error))


if __name__ == "__main__":
    richmail = ESMTPServer()
    richmail.run()
