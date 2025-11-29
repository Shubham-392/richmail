# Extended HELLO or HELLO (HELO) COMMAND
# EHLO COMMAND
# Standards
# RFC 5321


class CommandSpecifier:

    featuredCommands = [
        "EHLO",
        "MAIL",
        "RCPT",
        "DATA",
        "QUIT"
    ]

    def __init__(self, COMMAND: str):
        self.COMMAND = COMMAND

    def checkCommand(self):
        # clean the command first
        command = self.COMMAND.strip()
        command = self.COMMAND.upper()

        return command in self.featuredCommands

    def identiCommand(self):
        if self.checkCommand():
            for availcommand in self.featuredCommands:
                if availcommand == self.COMMAND.upper():
                    return availcommand

        else:
            errorCode = 502
            return f"{errorCode} Command not implemented"
