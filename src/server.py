import socket

from email_validator import EmailNotValidError, validate_email

from src.smtpd import CommandSpecifier

version = "1.0.0"
softwareAndVersion = f"richmail {version}"

# < stateIndependentCommands >
# these commands can be used at any time during a session,
# or without previously initializing a session.

stateIndependentCommands = [
                        "NOOP",
                        "HELP",
                        "EXPN",
                        "VRFY",
                        "RSET"
                ]



class ESMTPServer:

    # {"command":"command_DONE"}
    transcationState = 'INIT'

    preCommandStates = {
        "EHLO":"EHLO_DONE",
        "MAIL": "MAIL_DONE",
        "RCPT":"RCPT_DONE",
        "DATA":"DATA_DONE"
    }

    mailTranscationObjs = [
        'senderMail', # only one is strictly allowed
        'recipientMail', # can be more than one recipient mails with RCPT command
        'dataBuffer' # message body of mail
    ]

    # Transcation detail for adding in message queue and for logging
    mailTranscation = {}

    def __init__(
        self,
        addressFamily = socket.AF_INET,
        stream = socket.SOCK_STREAM
    ):
        self.stream = stream
        self.addressFamily = addressFamily


    def sendGreet(self,
        greetCode=220,
        softwareAndVersion= softwareAndVersion
    ) -> bytes :
        """ return greeting in bytes"""
        greeting = f"{greetCode} {softwareAndVersion} Service ready"
        greeting = greeting.encode(encoding="utf-8")
        return greeting

    def run(self, HOST='127.0.0.1', PORT=2525):

        with socket.socket(self.addressFamily, self.stream) as server:
            server.bind((HOST, PORT))
            # listen for one incoming connections
            server.listen(0)
            clientSocket, clientAddress = server.accept()
            with clientSocket:
                greeting = self.sendGreet()
                clientSocket.send(greeting)
                while True:

                    request = clientSocket.recv(2**10)
                    request = request.decode(encoding="utf-8")
                    cleanrequest  = request.strip()

                    if cleanrequest.lower() == 'close':
                        # send response to the client which acknowledges that the
                        # connection should be closed and break out of the loop
                        clientSocket.send("closed".encode("utf-8"))
                        print(f"Connection closed for {clientAddress}")
                        break


                    requestStripped = request.strip()
                    print(f"Received: {requestStripped}")

                    commandChunk = requestStripped.split(" ")
                    commandInfo = CommandSpecifier(COMMAND=commandChunk[0])
                    identifiedCommand = commandInfo.identiCommand()

                    if identifiedCommand == 'EHLO':
                        if len(commandChunk) != 2:
                            errorCode = 501
                            error = f"{errorCode} Syntax error in parameters or arguments"
                            clientSocket.send(error.encode("utf-8"))


                        okaycode = 250
                        msg = f"{okaycode} Requested mail action okay, completed"

                        clientSocket.send(msg.encode("utf-8"))
                        self.transcationState = self.preCommandStates[identifiedCommand]
                        print(f"Transcation State:{self.transcationState}")

                    elif identifiedCommand == 'MAIL':
                        if len(commandChunk) == 3:
                            if (commandChunk[1].lower()) != 'from:':
                                errorCode = 500
                                error = f"{errorCode} Syntax error, command unrecognized"
                                clientSocket.send(error.encode("utf-8"))

                            else:
                                senderMailAddress = commandChunk[2]
                                if (
                                    (senderMailAddress.startswith("<"))
                                    and
                                    (senderMailAddress.endswith(">"))
                                ):

                                    senderMailAddress = senderMailAddress[1:-1]

                                    if senderMailAddress :
                                        try:
                                            validSenderAddress = validate_email(
                                                                    senderMailAddress,
                                                                    check_deliverability=True
                                                                )

                                            print(f"{validSenderAddress.normalized}")
                                            # normalise email for session use
                                            normalizedSenderAddress = validSenderAddress.normalized

                                            # start the session
                                            if  self.mailTranscationObjs[0] not in self.mailTranscation.keys():
                                                self.mailTranscation[self.mailTranscationObjs[0]] = normalizedSenderAddress

                                            # send SMTP reply and after initializing the transcation
                                            successCode = 250
                                            successMsg = f'{successCode} OK Requested mail action okay, completed'
                                            clientSocket.send(successMsg.encode("utf-8"))

                                            self.transcationState = self.preCommandStates[identifiedCommand]
                                            print(f"Transcation State:{self.transcationState}")
                                            print(f"Transcation Session Detail:{self.mailTranscation}")

                                        except EmailNotValidError :
                                            errorCode = 550
                                            errorMsg = f'{errorCode} Requested action not taken: mailbox unavailable'

                                            clientSocket.send(errorMsg.encode("utf-8"))

                                        except Exception :
                                            errorCode = 550
                                            errorMsg = f'{errorCode} Requested action not taken: mailbox unavailable'

                                            clientSocket.send(errorMsg.encode("utf-8"))


                                    else:
                                        errorCode = 553
                                        errorMsg = f'{errorCode} Requested action not taken: mailbox name not allowed'
                                        clientSocket.send(errorMsg.encode("utf-8"))


                        else:
                            error_code = 500
                            errorMsg = f'{error_code} Syntax error, command unrecognized'
                            clientSocket.send(errorMsg.encode("utf-8"))


                    elif identifiedCommand == 'RCPT':
                        if (
                            (self.transcationState == self.preCommandStates['MAIL'])
                            or
                            (self.mailTranscationObjs[1] in self.mailTranscation)
                        ):

                            if len(commandChunk) == 3:
                                if (commandChunk[1].lower()) != 'to:':
                                    errorCode = 500
                                    error = f"{errorCode} Syntax error, command unrecognized"
                                    clientSocket.send(error.encode("utf-8"))

                                else:
                                    recipientMailAddress = commandChunk[2]
                                    if (
                                        (recipientMailAddress.startswith("<"))
                                        and
                                        (recipientMailAddress.endswith(">"))
                                    ):

                                        recipientMailAddress = recipientMailAddress[1:-1]

                                        if recipientMailAddress :
                                            try:
                                                validRecipientAddress = validate_email(
                                                                        recipientMailAddress,
                                                                        check_deliverability=True
                                                                    )

                                                print(f"{validRecipientAddress.normalized}")
                                                normalizedRecipientAddress = validRecipientAddress.normalized

                                                if self.mailTranscationObjs[1] not in self.mailTranscation:
                                                    self.mailTranscation[self.mailTranscationObjs[1]] = [normalizedRecipientAddress]
                                                else:
                                                    self.mailTranscation[self.mailTranscationObjs[1]].append(normalizedRecipientAddress)


                                                print(f"Transcation Session Detail:{self.mailTranscation}")
                                                successCode = 250
                                                successMsg = f'{successCode} OK Requested mail action okay, completed'
                                                clientSocket.send(successMsg.encode("utf-8"))

                                                self.transcationState = self.preCommandStates[identifiedCommand]
                                                print(f"Transcation State:{self.transcationState}")

                                            except EmailNotValidError :
                                                errorCode = 550
                                                errorMsg = f'{errorCode} Requested action not taken: mailbox {normalizedRecipientAddress} unavailable'

                                                clientSocket.send(errorMsg.encode("utf-8"))

                                            except Exception :
                                                errorCode = 550
                                                errorMsg = f'{errorCode} Requested action not taken: mailbox {normalizedRecipientAddress} unavailable'

                                                clientSocket.send(errorMsg.encode("utf-8"))


                                        else:
                                            errorCode = 553
                                            errorMsg = f'{errorCode} Requested action not taken: mailbox name not allowed'
                                            clientSocket.send(errorMsg.encode("utf-8"))


                            else:
                                error_code = 500
                                errorMsg = f'{error_code} Syntax error, command unrecognized'
                                clientSocket.send(errorMsg.encode("utf-8"))

                        else:
                            errorCode = 503
                            errorMsg = f'{errorCode} Bad sequence of command(s)'
                            clientSocket.send(errorMsg.encode("utf-8"))


                    elif identifiedCommand == 'DATA':
                        if self.transcationState == self.preCommandStates['RCPT']:

                            DataCommandBuffer = ""
                            if len(commandChunk) != 1:
                                errorCode = 455
                                errorMsg = f'{errorCode} Server unable to accommodate parameters'
                                clientSocket.send(errorMsg.encode("utf-8"))


                            else:
                                successCode = 354
                                successMsg = f'{successCode} Start mail input; end with <CRLF>.<CRLF>'
                                clientSocket.send(successMsg.encode("utf-8"))

                                self.transcationState = self.preCommandStates[identifiedCommand]
                                print(f"Transcation State:{self.transcationState}")

                                notDataCommandEnd = True
                                while notDataCommandEnd :
                                    # Receive every line from Data Command loop before <CRLF>.<CRLF>
                                    DataLineWithCrlf = clientSocket.recv(2**10)
                                    DataLineWithCrlf = DataLineWithCrlf.decode(encoding="utf-8")
                                    # extract text before CRLF
                                    cleanDataLineWithCrlf  = DataLineWithCrlf.strip()

                                    if cleanDataLineWithCrlf == ".":
                                        # break DATA input lines and
                                        # enter in transmission channel for next command
                                        print(f"{DataCommandBuffer}")
                                        notDataCommandEnd = False

                                    else:
                                        # update data-buffer after receiving every line
                                        DataCommandBuffer += f'{str(cleanDataLineWithCrlf)}\n'

                                if self.mailTranscationObjs[2] not in self.mailTranscation:
                                    self.mailTranscation[self.mailTranscationObjs[2]] = DataCommandBuffer
                                else:
                                    self.mailTranscation[self.mailTranscationObjs[2]] = DataCommandBuffer

                                print(self.mailTranscation)
                                successCode = 250
                                successMsg  = f'{successCode} OK'

                                # store the details of the transcation for further processing


                                # clear all the buffers for next transcation
                                self.mailTranscation = {}
                                clientSocket.send(successMsg.encode("utf-8"))

                        else:
                            errorCode = 503
                            errorMsg = f'{errorCode} Bad sequence of command(s)'
                            clientSocket.send(errorMsg.encode("utf-8"))


                    else:
                        errorMsg = identifiedCommand
                        clientSocket.send(errorMsg.encode("utf-8"))



if __name__=="__main__":
    richmail = ESMTPServer()
    richmail.run()
