from src.smtp.mime.headers import content_type, mime_version, mime_version_value
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
                print(rawHeader,rawValue)
                header, version = rawHeader.strip(), rawValue.strip()

                if header.upper() == content_type:
                    ...

                elif header.upper() == mime_version:
                    if version == mime_version_value:
                        self.StoreHeaderInfo(header=header, version=version)
                    comments = extractComments(header_value=version)
                    self.StoreHeaderInfo(header=header, version=version, comments=comments)


    def StoreHeaderInfo(self, header:str, version:str, comments:list = None):
        # Initialize headers dict only if it doesn't exist
        if 'headers' not in self.MIMEInfo:
            self.MIMEInfo['headers'] = {}

        if header.upper() == mime_version.upper():
            self.MIMEInfo['headers']['MIME-Version']= {}
            self.MIMEInfo['headers']['MIME-Version']['name'] = mime_version
            self.MIMEInfo['headers']['MIME-Version']['version'] = version
            if comments is not None:
                self.MIMEInfo['headers']['MIME-Version']['comments'] = comments
