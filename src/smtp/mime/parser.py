
from src.smtp.mime.headers import (
    CONTENT_TYPE,
    FROM, SUBJECT, TO,
    MIMEVersion, MIMEVersionDefault,
    TYPES
)
from src.smtp.mime.utils import extractComments, extractMediaTypes
# from src.smtp.logger.setup import logger
#
# If boundary is null, we assume that *f is positioned on the start of
# headers (for example, at the very beginning of a message.  If a boundary is
# given, we must first advance to it to reach the start of the next header
# block.

#  NOTE -- there's an error here -- RFC2046 specifically says to
#  check for outer boundaries.  This code doesn't do that, and
#  I haven't fixed this.
#
#

class MIMEParser:
    def __init__(self):
        self.MIMEInfo = {}

    def unfoldHeaders(self, lines:list) -> list:
        currentLine = ""
        unfoldLines = []
        for line in lines:
            if line and (line[0]== " " or line[0] == "\t"):
                # this is continuation of `currentLine`
                currentLine += " " + line.strip()
            else:
                # New line
                if currentLine:
                    unfoldLines.append(currentLine)
                currentLine = line

        # check if currentLine is inserted appropirately
        if currentLine:
            unfoldLines.append(currentLine)
        return unfoldLines

    def parse(self, dataBuffer: str):
        # split per '\n' as in server.py after successfull
        # CRLF is replaced with '\n' for every new line.
        lines = dataBuffer.split("\n")
        lines = self.unfoldHeaders(lines=lines)
        for line in lines:
            # ':' indicates header as per syntax of headers in RFC
            if ":" in line:
                rawHeader, rawValue = line.split(":", 1)
                header, value = rawHeader.strip(), rawValue.strip()

                if header.upper() == CONTENT_TYPE:
                    Type, SubType, attributes= extractMediaTypes(header_value=value)
                    if Type.upper() in TYPES:

                        self.StoreHeaderInfo(
                            header=header,
                            value=value,
                            type=Type,
                            subType=SubType,
                            attributes=attributes
                        )

                elif header.upper() == MIMEVersion:
                    if value == MIMEVersionDefault:
                        self.StoreHeaderInfo(header=header, value=value)
                    comments, version = extractComments(header_value=value)
                    self.StoreHeaderInfo(header=header, value=version, comments=comments)

                elif header.upper() == FROM:
                    self.StoreHeaderInfo(header=header, value=value)
                elif header.upper() == TO:
                    self.StoreHeaderInfo(header=header, value=value)
                elif header.upper() == SUBJECT:
                    self.StoreHeaderInfo(header=header, value=value)



    def StoreHeaderInfo(
        self,
        header:str,
        value:str = None,
        comments:list = None,
        type:str = "plain",
        subType:str = "text",
        attributes:list = None,
    ):
        # Initialize headers dict only if it doesn't exist
        if 'headers' not in self.MIMEInfo:
            self.MIMEInfo['headers'] = {}

        if header.upper() == MIMEVersion:
            self.MIMEInfo['headers']['MIME-Version']= {}
            self.MIMEInfo['headers']['MIME-Version']['name'] = header
            self.MIMEInfo['headers']['MIME-Version']['version'] = value
            if comments is not None:
                self.MIMEInfo['headers']['MIME-Version']['comments'] = comments

        elif header.upper() == FROM:
            self.MIMEInfo['headers']['From'] = value

        elif header.upper() == TO:
            self.MIMEInfo['headers']['To'] = value
        elif header.upper() == SUBJECT:
            self.MIMEInfo['headers']['Subject'] = value

        elif header.upper() == CONTENT_TYPE:
            self.MIMEInfo['headers']['Content-Type'] = {
                'media':{},
            }
            self.MIMEInfo['headers']['Content-Type']['media']['type'] = type
            self.MIMEInfo['headers']['Content-Type']['media']['subtype'] = subType

            # store attributes information
            if attributes:
                self.MIMEInfo['headers']['Content-Type']['attributes'] = attributes
