from src.smtp.mime.headers import mime_version, mime_version_value
from src.smtp.logger.setup import logger

class MIMEParser:
    def __init__(self):
        self.MIMEInfo = {}

    def parse(self, dataBuffer: str):
        lines = dataBuffer.split("\n")
        for line in lines:
            if ":" in line:
                rawHeader, rawValue = line.split(":", 1)
                header, value = rawHeader.strip(), rawValue.strip()
                if header.upper() == mime_version:
                    logger.debug(f"Found MIME-Version header: {value}")
                    if value == mime_version_value:
                        self.StoreHeaderInfo(header=header, value=value)

    def StoreHeaderInfo(self, header, value):
        # Initialize headers dict only if it doesn't exist
        if 'headers' not in self.MIMEInfo:
            self.MIMEInfo['headers'] = {}

        if header.upper() == mime_version.upper():
            self.MIMEInfo['headers']['MIME-Version']= {}
            self.MIMEInfo['headers']['MIME-Version']['name'] = mime_version
            self.MIMEInfo['headers']['MIME-Version']['value'] = value
            logger.info(f'MIME Info: {self.MIMEInfo}')
