from email import policy
from email.message import EmailMessage
from email.parser import Parser
import json


class MIMEParser:
    def __init__(self, email_string: str):
            self.message = Parser(policy=policy.default).parsestr(email_string)
            self.parsedData = {
                'levels':{},
            }


    def parse(self) -> dict:
        # Extract headers
        self._extractHeaders()

        # Parse body and attachments
        # if self.message.is_multipart():
        self._parseMultipart(msg = self.message)
        # else:
        #     self._parsePlain()

        # return self.parsedData

    def _extractHeaders(self):
        if '0' not in self.parsedData['levels'].keys():
            self.parsedData['levels']['0'] = {
                'headers':[]
            }
        for key, value in self.message.items():
            if hasattr(value, 'params'):
                headerInfo = {
                    'name':key,
                    'value':value,
                    'params': [dict(value.params)]
                }
            else:
                headerInfo = {
                    'name':key,
                    'value':value
                }

            self.parsedData['levels']['0']['headers'].append(headerInfo)

        print(self.parsedData)

    def _parseMultipart(self, msg: EmailMessage):

        if msg.is_multipart():
            for newLevel, part in enumerate(msg.iter_parts(), 1):
                # Extract all headers specific to this sub-part
                for header, value in part.items():
                    if hasattr(value, 'params'):
                        self._addHeaders(
                            level=newLevel,
                            name=header,
                            value=value,
                            params = dict(value.params)
                        )
                    else:
                        self._addHeaders(
                            level=newLevel,
                            name = header,
                            value=value
                        )

                content = part.get_content()
                # handle the decoding of octet-stream
                # if isinstance(content, bytes):
                #     try:
                #         encodedContent = content.decode("utf-8")
                #         self._addContent(newLevel, encodedContent)
                #     except UnicodeDecodeError as e:
                #         print(str(e))

                # else:

                self._addContent(newLevel, str(content))

            # print(self.parsedData)

    def _addHeaders(self, level, name, value, params= None):
        if params:
            headerObject = {
                'name':name,
                'value':value,
                'params':[
                    params
                ]
            }
        else:
            headerObject = {
                'name':name,
                'value':value,
                'params':params
            }

        if level not in self.parsedData['levels'].keys():
                self.parsedData['levels'][level] = {'headers': [headerObject]}
        else:
            if 'headers' not in self.parsedData['levels'][level].keys():
                self.parsedData['levels'][level]['headers'] = [headerObject]
            else:
                self.parsedData['levels'][level]['headers'].append(headerObject)
        with open("./value.json", "w") as f:
            json.dump(self.parsedData, indent=2, fp =f)


    def _addContent(self, level:int, content):
        self.parsedData['levels'][level]['content'] = content
        with open("./value.json", "w") as f:
            json.dump(self.parsedData, indent=2, fp =f)
