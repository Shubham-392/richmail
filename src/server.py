import socket

from email_validator import EmailNotValidError, validate_email

from src.smtpd import CommandSpecifier

version = "1.0.0"
softwareAndVersion = f"richmail {version}"

# < stateIndependentCommands >
# these commands can be used at any time during a session,
# or without previously initializing a session.

stateIndependentCommands = ["NOOP", "HELP", "EXPN", "VRFY", "RSET"]

class QuitLoopException(Exception):
    pass


class ESMTPServer:
    # {"command":"command_DONE"}
    transcationState = "INIT"

    preCommandStates = {
        "EHLO": "EHLO_DONE",
        "MAIL": "MAIL_DONE",
        "RCPT": "RCPT_DONE",
        "DATA": "DATA_DONE",
    }

    mailTranscationObjs = [
        "senderMail",  # only one is strictly allowed
        "recipientMail",  # can be more than one recipient mails with RCPT command
        "dataBuffer",  # message body of mail
    ]

    # Transcation detail for adding in message queue and for logging
    mailTranscation = {}

    def __init__(self, addressFamily=socket.AF_INET, stream=socket.SOCK_STREAM):
        self.stream = stream
        self.addressFamily = addressFamily

    def sendGreet(self, greetCode=220, softwareAndVersion=softwareAndVersion) -> bytes:
        """return greeting in bytes"""
        greeting = f"{greetCode} {softwareAndVersion} Service ready"
        greeting = greeting.encode(encoding="utf-8")
        return greeting

    def run(self, HOST="127.0.0.1", PORT=2525):
        with socket.socket(self.addressFamily, self.stream) as server:
            server.bind((HOST, PORT))
            # listen for one incoming connections
            server.listen(0)
            clientSocket, clientAddress = server.accept()
            with clientSocket:
                greeting = self.sendGreet()
                clientSocket.send(greeting)
                try:

                    while True:
                        request = clientSocket.recv(2**10)
                        request = request.decode(encoding="utf-8")

                        requestStripped = request.strip()
                        print(f"Received: {requestStripped}")

                        commandChunk = requestStripped.split(" ")
                        commandInfo = CommandSpecifier(COMMAND=commandChunk[0])
                        identifiedCommand = commandInfo.identiCommand()

                        self.CommandHandler(
                            command = identifiedCommand,
                            commandChunk = commandChunk,
                            connSocket = clientSocket
                    )
                except QuitLoopException:
                    pass


    def CommandHandler(
        self,
        command:str,
        commandChunk:dict,
        connSocket:socket.socket
    ):
        if   command == 'EHLO':
            self.EhloCmdHandler(
                command       = command,
                commandTokens = commandChunk,
                connSocket    = connSocket
            )
        elif command == 'MAIL':
            self.MailCmdHandler(
                command       = command,
                commandTokens = commandChunk,
                connSocket    = connSocket
            )
        elif command == 'RCPT':
            self.RcptCmdHandler(
                command=command,
                commandTokens=commandChunk,
                connSocket=connSocket
            )
        elif command == 'DATA':
            self.DataCmdHandler(
                command=command,
                commandTokens=commandChunk,
                connSocket=connSocket
            )
        elif command == 'QUIT':
            self.QuitCmdHanlder(
                command=command,
                commandTokens=commandChunk,
                connSocket=connSocket
            )
        else:
            errorMsg = command
            connSocket.send(errorMsg.encode("utf-8"))


    def EhloCmdHandler(self,
        command:str,
        commandTokens:dict,
        connSocket:socket.socket,
        timeout:int= 0,

    ):
        if len(commandTokens) != 2:
            self.SendError(errorCode=501, clientSocket=connSocket)

        self.SendSuccess(successCode=250,clientSocket=connSocket)
        self.UpdateState(command = command)

    def  MailCmdHandler(self,
        command:str,
        commandTokens:dict,
        connSocket: socket.socket,
        timeout:int = 5,
    ):
        if len(commandTokens) != 3:
            self.SendError(errorCode = 555, clientSocket = connSocket)
        else:
            if (commandTokens[1].lower()) != "from:":
                self.SendError(errorCode = 555, clientSocket = connSocket)
            else:
                senderMailAddress = commandTokens[2]
                if (senderMailAddress.startswith("<")) and (
                    senderMailAddress.endswith(">")
                ):
                    senderMailAddress = senderMailAddress[1:-1]

                    if senderMailAddress:
                        try:
                            validSenderAddress = validate_email(
                                senderMailAddress,
                                check_deliverability=True,
                            )

                            print(f"{validSenderAddress.normalized}")
                            # normalise email for session use
                            normalizedSenderAddress = (
                                validSenderAddress.normalized
                            )

                            # start the session
                            if (
                                self.mailTranscationObjs[0]
                                not in self.mailTranscation.keys()
                            ):
                                self.mailTranscation[
                                    self.mailTranscationObjs[0]
                                ] = normalizedSenderAddress

                            # send SMTP reply and after initializing the transcation
                            self.SendSuccess(successCode=250, clientSocket=connSocket)

                            # update the transcation state for the next command in series
                            self.UpdateState(command=command)

                        except EmailNotValidError:
                            self.SendError(errorCode= 550, clientSocket = connSocket)

                        except Exception:
                            self.SendError(errorCode= 550, clientSocket = connSocket)

                    else:
                        self.SendError(errorCode=553, clientSocket = connSocket )

    def  RcptCmdHandler(
        self,
        command: str,
        commandTokens: dict,
        connSocket: socket.socket,
        timeout:int = 5,
    ):
        if (self.transcationState == self.preCommandStates["MAIL"]) or (
            self.mailTranscationObjs[1] in self.mailTranscation
        ):
            if len(commandTokens) != 3:
                self.SendError(errorCode=500, clientSocket=connSocket)
            else:
                if (commandTokens[1].lower()) != "to:":
                    self.SendError(errorCode=500, clientSocket=connSocket)
                else:
                    recipientMailAddress = commandTokens[2]
                    if (recipientMailAddress.startswith("<")) and (
                        recipientMailAddress.endswith(">")
                    ):
                        recipientMailAddress = recipientMailAddress[
                            1:-1
                        ]

                        if recipientMailAddress:
                            try:
                                validRecipientAddress = validate_email(
                                    recipientMailAddress,
                                    check_deliverability=True,
                                )

                                print(
                                    f"{validRecipientAddress.normalized}"
                                )
                                normalizedRecipientAddress = (
                                    validRecipientAddress.normalized
                                )

                                if (self.mailTranscationObjs[1] not in self.mailTranscation):

                                    self.mailTranscation[self.mailTranscationObjs[1]] = [normalizedRecipientAddress]
                                else:
                                    self.mailTranscation[self.mailTranscationObjs[1]].append(normalizedRecipientAddress)

                                print(
                                    f"Transcation Session Detail:{self.mailTranscation}"
                                )
                                self.SendSuccess(successCode=250, clientSocket=connSocket)

                                self.UpdateState(command=command)

                            except EmailNotValidError:
                                self.SendError(errorCode=550, clientSocket=connSocket)

                            except Exception:
                                self.SendError(errorCode=550, clientSocket=connSocket)
                        else:
                            self.SendError(errorCode=553, clientSocket=connSocket)


        else:
            self.SendError(errorCode=503, clientSocket=connSocket)


    def DataCmdHandler(self,
        command:str,
        commandTokens:dict,
        connSocket:socket.socket,
        timeout:int= 10,
        ):
        if self.transcationState == self.preCommandStates["RCPT"]:
            DataCommandBuffer = ""
            if len(commandTokens) != 1 :
                self.SendError(errorCode=455, clientSocket=connSocket)
            else:
                self.SendSuccess(successCode=354, clientSocket=connSocket)

                self.UpdateState(command=command)
                print(f"Transcation State:{self.transcationState}")

                notDataCommandEnd = True
                while notDataCommandEnd:
                    # Receive every line from Data Command loop before <CRLF>.<CRLF>
                    DataLineWithCrlf = connSocket.recv(2**10)
                    DataLineWithCrlf = DataLineWithCrlf.decode(
                        encoding="utf-8"
                    )
                    # extract text before CRLF
                    cleanDataLineWithCrlf = DataLineWithCrlf.strip()

                    if cleanDataLineWithCrlf == ".":
                        # break DATA input lines and
                        # enter in transmission channel for next command
                        print(f"{DataCommandBuffer}")
                        notDataCommandEnd = False

                    else:
                        # update data-buffer after receiving every line
                        DataCommandBuffer += (
                            f"{str(cleanDataLineWithCrlf)}\n"
                        )

                if (self.mailTranscationObjs[2] not in self.mailTranscation):
                    self.mailTranscation[self.mailTranscationObjs[2]] = DataCommandBuffer
                else:
                    self.mailTranscation[self.mailTranscationObjs[2]] = DataCommandBuffer

                print(self.mailTranscation)

                # clear all the buffers for next transcation
                self.mailTranscation = {}
                self.SendSuccess(successCode=250, clientSocket=connSocket)


        else:
            self.SendError(errorCode=503, clientSocket=connSocket)

    def QuitCmdHanlder(self,
        command: str,
        commandTokens: dict,
        connSocket: socket,
        timeout: int = 10
    ) -> bool:
        # send response to the client which acknowledges that the
        # connection should be closed and break out of the loop
        if len(commandTokens) != 1:
            self.SendError(errorCode=455, clientSocket=connSocket)

        else:
            self.SendSuccess(successCode=221, clientSocket=connSocket)
            raise QuitLoopException



    def SendError(self, errorCode:int, clientSocket:socket.socket):

        if errorCode == 455:
            errorMsg = f"{errorCode} Server unable to accommodate parameters"
            clientSocket.send(errorMsg.encode("utf-8"))

        if errorCode == 500:
            errorMsg = f"{errorCode} Syntax error, command unrecognized"
            clientSocket.send(errorMsg.encode("utf-8"))

        if errorCode == 501:
            errorMsg = f"{errorCode} Syntax error in parameters or arguments"
            clientSocket.send(errorMsg.encode("utf-8"))

        if errorCode == 503:
            errorMsg = f'{errorCode} Bad sequence of command(s)'
            clientSocket.send(errorMsg.encode('utf-8'))

        if errorCode == 550:
            errorMsg = f"{errorCode} Requested action not taken: mailbox unavailable"
            clientSocket.send(errorMsg.encode("utf-8"))

        if errorCode == 553:
            errorMsg = f"{errorCode} Requested action not taken: mailbox name not allowed"
            clientSocket.send(errorMsg.encode("utf-8"))

        if errorCode == 555:
            errorMsg = f"{errorCode} Syntax error, command unrecognized"
            clientSocket.send(errorMsg.encode("utf-8"))

    def SendSuccess(self, successCode:int, clientSocket:socket.socket):

        if successCode == 221:
            successMsg = f"{successCode} OK Closing transmission channel"
            clientSocket.send(successMsg.encode("utf-8"))

        if successCode == 250:
            successMsg = f'{successCode} OK Requested mail action okay, completed'
            clientSocket.send(successMsg.encode("utf-8"))

        if successCode == 354:
            successMsg = f"{successCode} Start mail input; end with <CRLF>.<CRLF>"
            clientSocket.send(successMsg.encode("utf-8"))

    def UpdateState(self, command:str):
        self.transcationState = self.preCommandStates[command]

if __name__ == "__main__":
    richmail = ESMTPServer()
    richmail.run()
