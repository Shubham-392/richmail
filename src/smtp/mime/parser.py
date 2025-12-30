from email import policy
from email.message import EmailMessage, MIMEPart
from email.parser import Parser
import json
from pathlib import Path

# from src.smtp.mime.data import Persons
# {
#     "message_id": "<unique-id-from-header>",
#     "metadata": {
#         "subject": "Project Update",
#         "from": "sender@example.com",
#         "to": ["receiver@example.com"],
#         "date": "2023-10-27T10:00:00Z",
#         "common_headers": [
#             {"name": "X-Priority", "value": "3"},
#             {"name": "Reply-To", "value": "support@example.com"}
#         ]
#     },
#     "structure": {
#         "main_type": "multipart",
#         "sub_type": "mixed",
#         "parts": [
#             {
#                 "type": "text/plain",
#                 "disposition": "inline",
#                 "content": "Hello, please find the report attached.",
#                 "charset": "utf-8"
#             },
#             {
#                 "type": "text/html",
#                 "disposition": "inline",
#                 "content": "<html><body><p>Hello, please find the <b>report</b> attached.</p></body></html>",
#                 "charset": "utf-8"
#             },
#             {
#                 "type": "application/pdf",
#                 "disposition": "attachment",
#                 "filename": "report_2023.pdf",
#                 "file_path": "./emls/attachments/eml_report_2023.pdf",
#                 "content_id": None
#             },
#             {
#                 "type": "image/png",
#                 "disposition": "inline",
#                 "filename": "signature.png",
#                 "file_path": "./emls/inlines/eml_signature.png",
#                 "content_id": "<sig123@example.com>"
#             }
#         ]
#     }
# }


class MIMEParser:

    def __init__(self, email_string: str):
            self.message = Parser(policy=policy.default).parsestr(email_string)
            self.parsedData = {
                "message_id": "",
                "metadata": {},
                "structure": {
                    "main_type": "",
                    "sub_type": "",
                    "nodes": []
                }
        }


    def parse(self) -> dict:
        
        # get the main headers first
        self.parsedData["message_id"] = str(self.message.get("Message-ID", ""))
        self.parsedData["metadata"] = {
            "subject": str(self.message.get("subject", "")),
            "from": str(self.message.get("from", "")),
            "to": str(self.message.get("to", "")),
            "date": str(self.message.get("date", "")),
            "common_headers": self._extractHeaders()
        }

        # 2. Extract Structure info
        self.parsedData["structure"]["main_type"] = self.message.get_content_maintype()
        self.parsedData["structure"]["sub_type"] = self.message.get_content_subtype()

        # Parse body and attachments
        # if self.message.is_multipart():
        self._parseMultipart(msg = self.message)
        # else:
        #     self._parsePlain()

        # return self.parsedData
        with open("./value.json", "w") as f:
            json.dump(self.parsedData, indent=2, default=str ,fp =f)
            
        return self.parsedData

    def _extractHeaders(self):
        headers = []
        # get most general headers first 
        skip_header = {'subject', 'from', 'to', 'date', 'message-id'}
        for key, value in self.message.items():
            if key.lower() not in skip_header:
                headers.append({"name": key, "value": str(value)})
        return headers

    def _parseMultipart(self, msg: EmailMessage):

        if msg.is_multipart():
            for _ , part in enumerate(msg.iter_parts(), 1):
                # multipart/* are just containers
                if part.get_content_maintype() == 'multipart':
                    continue

                content_type = part.get_content_type()
                filename = part.get_filename()
                content_id = part.get("Content-ID")
                contentSubtype = part.get_content_subtype()
                contentDisposition = part.get_content_disposition()
                
                partInfo = {
                    "type": content_type,
                    "filename": filename,
                    "content_id": content_id,
                    "charset": part.get_content_charset()
                }
                

                if contentSubtype.lower() == "html":
                    try:
                        htmlContent = part.get_content()
                        # charset = part.get_content_charset
                        encodedHTMLContent = htmlContent
                        sender = self.parsedData['metadata']['from']
                        # content is not in bytes
                        if not isinstance(encodedHTMLContent, bytes):
                            # content may be string.
                            if isinstance(encodedHTMLContent, str):
                                # finally save the html content successfully.
                                partInfo['content'] = encodedHTMLContent
                                
                                saved, storedPath = self._saveHTMLorTEXT(
                                    buffer=encodedHTMLContent,
                                    type='html',
                                    fname = (sender.split('@')[0] + ".html")
                                )
                                
                                if saved and storedPath:
                                    partInfo['storedPath'] = storedPath 
                                    print('saved html content')
                                else:
                                    print('problem got while saving')
                                
                    except Exception as e:
                        print(str(e))

                elif contentSubtype.lower() == 'plain':
                    try:
                        textContent = part.get_content()
                        sender = self.parsedData['metadata']['from']
                        # content is not in bytes
                        if not isinstance(textContent, bytes):
                            # content may be string.
                            if isinstance(textContent, str):
                                # finally save the html content successfully.
                                partInfo['content'] = textContent
                                saved, savedPath = self._saveHTMLorTEXT(
                                    buffer=textContent,
                                    type='plain',
                                    fname = (sender.split('@')[0] + ".txt")
                                )
                                
                                if saved and savedPath:
                                    partInfo['storedPath'] = savedPath
                                    print('saved plain text content')
                                else:
                                    print('problem got while saving')
                    except Exception as e:
                        print(str(e))


                elif contentDisposition is not None:
                    partInfo['disposition'] = contentDisposition
                    content = self._cleanContent(part)
                    disposition = contentDisposition.lower()
                    if isinstance(content, bytes):
                            # filename already contains the extension in name.
                            # write to server file as eml_{filename} 
                            
                            partInfo['content'] = content
                            savedPath = self._saveAttachment(buffer=content, fname=filename, disposition=disposition)
                            if savedPath is not None:
                                partInfo['storedPath'] = savedPath
                            
                # save the information finally in dictionary
                self.parsedData['structure']['nodes'].append(partInfo)

    def _saveAttachment(self, buffer:bytes, fname:str, disposition:str):
        
        filename = f'eml_{fname}'
        if disposition == 'inline':
            inlinedir = "./emls/inlines/"
            inlinePath = Path(inlinedir)
            inlinePath.mkdir(parents=True, exist_ok=True)
            
            with open(f'{inlinedir}/{filename}', "wb") as writable:
                writable.write(buffer)
                
            return f'{inlinedir}/{filename}'
            
        elif disposition == 'attachment':
            
            attachdir = "./emls/attachments/"
            dirPath = Path(attachdir)
            
            dirPath.mkdir(parents=True, exist_ok=True)
        
            with open(f'{attachdir}/{filename}', "wb") as writable:
                writable.write(buffer)
            
            return f'{attachdir}/{filename}'
        
        return None
   
                
    def _saveHTMLorTEXT(self, buffer:str, fname:str, type:str=None):
        templatesPath = "./templates/"
        textPath = "./texts/"
        if type == 'html':
            Path(templatesPath).mkdir(parents=True, exist_ok=True)
            
            with open(f'{templatesPath}/{fname}', "w", encoding='utf-8') as html:
                html.write(buffer)
                
            return True, f'{textPath}/{fname}'
        
        elif type == 'plain':
            Path(textPath).mkdir(parents=True, exist_ok=True)
            
            with open(f'{textPath}/{fname}', "w", encoding='utf-8') as html:
                html.write(buffer)
                
            return True, f'{textPath}/{fname}'
                
        else:
            return False, ""
            
            
            

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
        