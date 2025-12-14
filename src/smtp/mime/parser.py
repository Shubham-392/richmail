from src.smtp.mime.headers import FROM, TO,content_type, MIMEVersion,MIMEVersionDefault
from src.smtp.mime.utils import extractComments
# from src.smtp.logger.setup import logger

class MIMEParser:
    def __init__(self):
        self.MIMEInfo = {}

    def parse(self, dataBuffer: str):
        lines = dataBuffer.split("\n")
        for line in lines:
            if ":" in line:
                rawHeader, rawValue = line.split(":", 1)
                header, value = rawHeader.strip(), rawValue.strip()

                if header.upper() == content_type:
                    ...

                elif header.upper() == MIMEVersion:
                    if value == MIMEVersionDefault:
                        self.StoreHeaderInfo(header=header, value=value)
                    comments, version = extractComments(header_value=value)
                    self.StoreHeaderInfo(header=header, value=version, comments=comments)

                elif header.upper() == FROM:
                    self.StoreHeaderInfo(header=header, value=value)
                elif header.upper() == TO:
                    self.StoreHeaderInfo(header=header, value=value)


    def StoreHeaderInfo(self, header:str, value:str, comments:list = None):
        # Initialize headers dict only if it doesn't exist
        if 'headers' not in self.MIMEInfo:
            self.MIMEInfo['headers'] = {}

        if header.upper() == MIMEVersion:
            self.MIMEInfo['headers']['MIME-Version']= {}
            self.MIMEInfo['headers']['MIME-Version']['name'] = MIMEVersion
            self.MIMEInfo['headers']['MIME-Version']['version'] = value
            if comments is not None:
                self.MIMEInfo['headers']['MIME-Version']['comments'] = comments

        elif header.upper() == FROM:
            self.MIMEInfo['headers']['From'] = value

        elif header.upper() == TO:
            self.MIMEInfo['headers']['To'] = value

        print(self.MIMEInfo)
