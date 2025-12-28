from email import policy
from email.message import EmailMessage, MIMEPart
from email.parser import Parser
import json
from pathlib import Path


class MIMEParser:

    def __init__(self, email_string: str):
            self.message = Parser(policy=policy.default).parsestr(email_string)
            self.parsedData = {
                'levels':{},
            }
            self._spamIndicate:bool = False


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
                # multipart/* are just containers
                if part.get_content_maintype() == 'multipart':
                    continue

                # # Extract all headers specific to this sub-part
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

                contentSubtype = part.get_content_subtype()
                contentDisposition = part.get_content_disposition()

                if contentSubtype.lower() == "html":
                    htmlContent = part.get_content()
                    try:
                        # charset = part.get_content_charset
                        encodedHTMLContent = htmlContent
                        with open("./content.html", "w") as f:
                            f.write(encodedHTMLContent)
                    except Exception as e:
                        print(str(e))

                elif contentSubtype.lower() == 'plain':
                    try:
                        textContent = part.get_content()
                        with open("./content.txt", "w") as f:
                            f.write(textContent)
                    except Exception as e:
                        print(str(e))


                elif contentDisposition is not None:
                    if contentDisposition.lower() == "attachment":
                        filename = part.get_filename()
                        content = self._cleanContent(part)
                        
                        if isinstance(content, bytes):
                            # filename already contains the extension in name.
                            # write to server file as eml_{filename} 
                            self._saveAttachment( buffer=content, fname=filename, disposition="attachment")
                            
                    if contentDisposition.lower() == "inline":
                        filename = part.get_filename()
                        content = self._cleanContent(part)
                        
                        if isinstance(content, bytes):
                            # filename already contains the extension in name.
                            # write to server file as eml_{filename} 
                            self._saveAttachment( buffer=content, fname=filename)
                            

    def _saveAttachment(self, buffer:bytes, fname:str, disposition:str):
        
        filename = f'eml_{fname}'
        if disposition == 'inline':
            inlinedir = "./emls/inlines/"
            inlinePath = Path(inlinedir)
            inlinePath.mkdir(parents=True, exist_ok=True)
            
            with open(f'{inlinedir}/{filename}', "wb") as writable:
                writable.write(buffer)
            
        elif disposition == 'attachment':
            
            attachdir = "./emls/attachments/"
            dirPath = Path(attachdir)
            
            dirPath.mkdir(parents=True, exist_ok=True)
        
            with open(f'{attachdir}/{filename}', "wb") as writable:
                writable.write(buffer)

    def _cleanContent(self, part:MIMEPart):
        # this method is highly RFC Compliant
        # means it trusts the header
        # there is no HANDLING FOR MIME sniffing or deep MIME sniffing

        try:
            rawContent = part.get_content()

            if isinstance(rawContent, str):
                return rawContent

            elif isinstance(rawContent, bytes):
                return rawContent

        except Exception :
            return part.get_payload(decode=True)



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
