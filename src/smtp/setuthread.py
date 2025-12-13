import socket
import mysql.connector
from email_validator import EmailNotValidError, validate_email

from src.smtp.db.config import connPool
from src.smtp.exceptions import QuitLoopException
from src.smtp.mime.parser import MIMEParser

from src.smtp.logger.setup import logger
from src.smtp.smtpd import CommandSpecifier


version = "1.0.0"
softwareAndVersion = f"richmail {version}"

# < stateIndependentCommands >
# these commands can be used at any time during a session,
# or without previously initializing a session.

stateIndependentCommands = ["NOOP", "HELP", "EXPN", "VRFY", "RSET"]

class ESMTPSession:
    # Recipients Limit
    RECIPIENTS_LIMIT:int = 100

    # {"command":"command_DONE"}
    preCommandStates = {
        "EHLO": "EHLO_DONE",
        "MAIL": "MAIL_DONE",
        "RCPT": "RCPT_DONE",
        "DATA": "DATA_DONE",
        "RSET":"RSET_DONE",
    }

    def __init__(
        self,
        clientSocket,
        clientAddress
    ):
        self.conn = clientSocket
        self.addr = clientAddress
        self.transcationState = "INIT"
        self.mailTranscationObjs = [
            "senderMail",  # only one is strictly allowed
            "recipientMail",  # can be more than one recipient (atmost 100) mails with RCPT command
            "dataBuffer",  # message body of mail
        ]

        # Transcation detail for adding in message queue & for logging
        self.mailTranscation = {}

    def sendGreet(self, greetCode=220, softwareAndVersion=softwareAndVersion) -> bytes:
        """return greeting in bytes"""
        greeting = f"{greetCode} {softwareAndVersion} Service ready\r\n"
        greeting = greeting.encode(encoding="utf-8")
        return greeting

    def startThread(self):
        with self.conn:
            try:
                greeting = self.sendGreet()
                self.conn.send(greeting)
                logger.debug(f"S:{greeting}")
                # set timeout after sending greeting and
                #  waiting for the next command
                # clientSocket.settimeout(10)
                while True:
                    request = self.conn.recv(2**10)
                    request = request.decode(encoding="utf-8")
                    if not request:  # Client disconnected
                        logger.debug(f"Client {self.addr} disconnected")
                        break

                    requestStripped = request.strip()
                    logger.debug(f"C: {requestStripped}")

                    commandChunk = requestStripped.split(" ")
                    commandInfo = CommandSpecifier(COMMAND=commandChunk[0])
                    identifiedCommand = commandInfo.identiCommand()

                    self.CommandHandler(
                        command=identifiedCommand,
                        commandChunk=commandChunk,
                        connSocket=self.conn,
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
        elif command == "RSET":
            logger.debug(f'Command Identified is : {command}')
            self.RsetCmdHanlder(
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

                except Exception :
                    logger.exception("Exception Occured")
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
                logger.debug(f'Unable to recognize these parts: {" ".join(commandTokens[1:])}')
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
                    logger.debug(f'Received body chunk as: "{chunk}"')
                    receiveBuffer += chunk

                    # process complete lines (split by \r\n)
                    while "\r\n" in receiveBuffer:
                        line, receiveBuffer = receiveBuffer.split("\r\n", 1)
                        logger.debug(f'Processing line : "{line}"')

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
                # create object for MIME parser initialization
                parser = MIMEParser()
                # parse message to look if msg is formatted in MIME format
                logger.debug("Now parsing the message for MIME support")
                parser.parse(dataBuffer=DataCommandBuffer)


                logger.debug('Inserting the mail transcation in DB')
                try:
                    self.Insert(
                        sender=self.mailTranscation[self.mailTranscationObjs[0]],
                        receiver=self.mailTranscation[self.mailTranscationObjs[1]],
                        data=self.mailTranscation[self.mailTranscationObjs[2]],
                    )

                    # clear buffers for next transaction
                    self.mailTranscation = {}

                    self.SendSuccess(successCode=250, clientSocket=connSocket)
                except mysql.connector.PoolError :
                    logger.debug("Conenction pool is at it's max")
                    self.SendError(errorCode=451, clientSocket=connSocket)

                    # Clear transaction so it doesn't interfere with next attempt
                    self.mailTranscation = {}

                except Exception :
                    # Other database errors - send 451 (temporary failure)
                    logger.exception("Database Error")
                    self.SendError(errorCode=451, clientSocket=connSocket)
                    self.mailTranscation = {}
        else:
            logger.debug(f'Command out of Order, current state is {self.transcationState}')
            self.SendError(errorCode=503, clientSocket=connSocket)

    def QuitCmdHanlder(
        self, command: str, commandTokens: dict, connSocket: socket.socket, timeout: int = 10
    ) -> bool:
        # send response to the client which acknowledges that the
        # connection should be closed and break out of the loop
        if len(commandTokens) != 1:
            logger.debug(f'Unable to recognize these parts: {" ".join(commandTokens[1:])}')
            self.SendError(errorCode=455, clientSocket=connSocket)

        else:
            self.SendSuccess(successCode=221, clientSocket=connSocket)
            raise QuitLoopException

    def RsetCmdHanlder(
        self, command: str, commandTokens: dict, connSocket: socket, timeout: int = 10
    ) -> bool:

        """
        RSET

        This command specifies that the current mail transcation will be aborted.

        Any stored sender, recipients, and mail data MUST be discarded, and all buffers and state tables cleared.

        MUST send a `250 OK ` reply to a RSET command with no arguments.


        """
        if len(commandTokens) != 1:
            logger.debug(f'Unable to recognize these parts: {" ".join(commandTokens[1:])}')
            self.SendError(errorCode=455, clientSocket=connSocket)

        else:
            self.mailTranscation = {}
            self.UpdateState(command=command)
            logger.debug("Cleared all transcation buffers and state updated to 'INIT'")
            self.SendSuccess(successCode=250, clientSocket=connSocket)


    def SendError(self,
        errorCode: int,
        clientSocket: socket.socket,
        errorMsg = None,
    ):
        if errorCode == 451:
            if not errorMsg:
                errorMsg = f"{errorCode} Requested action aborted: local error in processing\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 455:
            if not errorMsg:
                errorMsg = f"{errorCode} Server unable to accommodate parameters\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 500:
            if not errorMsg:
                errorMsg = f"{errorCode} Syntax error, command unrecognized\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 501:
            if not errorMsg:
                errorMsg = f"{errorCode} Syntax error in parameters or arguments\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 503:
            if not errorMsg:
                errorMsg = f"{errorCode} Bad sequence of command(s)\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 550:
            errorMsg = f"{errorCode} Requested action not taken: mailbox unavailable\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 553:
            if not errorMsg:
                errorMsg = (
                    f"{errorCode} Requested action not taken: mailbox name not allowed\r\n"
                )
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

        elif errorCode == 555:
            # syntax error in command
            if not errorMsg:
                errorMsg = f"{errorCode} Syntax error, command unrecognized\r\n"
            clientSocket.send(errorMsg.encode("utf-8"))
            logger.debug(f'S: {errorMsg}')

    def SendSuccess(self, successCode: int, clientSocket: socket.socket, successMsg=None):
        if successCode == 221:
            if not successMsg:
                successMsg = f"{successCode} OK Closing transmission channel\r\n"
            clientSocket.send(successMsg.encode("utf-8"))
            logger.debug(f'S: {successMsg}')

        elif successCode == 250:
            if not successMsg:
                successMsg = f"{successCode} OK Requested mail action okay, completed\r\n"
            clientSocket.send(successMsg.encode("utf-8"))
            logger.debug(f'S: {successMsg}')

        elif successCode == 354:
            if not successMsg:
                successMsg = f"{successCode} Start mail input; end with <CRLF>.<CRLF>\r\n"
            clientSocket.send(successMsg.encode("utf-8"))
            logger.debug(f'S: {successMsg}')

    def UpdateState(self, command: str):
        self.transcationState = self.preCommandStates[command]
        logger.debug(f'State is updated to: {self.transcationState}')

    def Insert(self, sender, receiver, data):
        add_mail = "INSERT INTO setu_outbox(sender, receiver, data) VALUES "
        receiverList = len(receiver)
        for recv in range(receiverList):
            if recv < (receiverList - 1):
                add_mail += "('%s', '%s', '%s')," % (sender, receiver[recv],data)
            else:
                add_mail += "('%s', '%s', '%s')" % (sender, receiver[recv], data)

        logger.debug(f'SQL query for Inserting data: {add_mail}')

        try:
            connPool.execute(add_mail, commit=True)
        except mysql.connector.PoolError :
            raise
