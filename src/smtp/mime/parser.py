from src.smtp.mime.headers import (
    CONTENT_TYPE,
    FROM, SUBJECT, TO,
    MIMEVersion, MIMEVersionDefault
)
from src.smtp.mime.utils import extractComments, extractMediaTypes
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

                if header.upper() == CONTENT_TYPE:
                    Type, SubType, CORRUPTED, attribute, attributeValue = extractMediaTypes(header_value=value)

                    attributeInfo = {}
                    if not CORRUPTED and attribute and attributeValue:
                        attributeInfo = {
                            'name': attribute,
                            'value': attributeValue
                        }
                    self.StoreHeaderInfo(
                        header=header,
                        value=value,
                        type=Type,
                        subType=SubType,
                        attribute=attributeInfo
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

        print(self.MIMEInfo)


    def StoreHeaderInfo(
        self,
        header:str,
        value:str = None,
        comments:list = None,
        type:str = "plain",
        subType:str = "text",
        attribute:dict = None,
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
                'attributes':[],
            }
            self.MIMEInfo['headers']['Content-Type']['media']['type'] = type
            self.MIMEInfo['headers']['Content-Type']['media']['subtype'] = subType

            attributeContainer = self.MIMEInfo['headers']['Content-Type']['attributes']
            if attribute:
                attributeContainer.append(attribute)
