from src.smtp.db.config import connPool


class MIMEStore:
    def __init__(self, MIMEInfo):
        self.MIMEInfo = MIMEInfo
        
    def storeMeta(self):
        metadata:dict = self.MIMEInfo['metadata']
        nodes:list = self.MIMEInfo['structure']['nodes']
        
        message_id:str = self.MIMEInfo['msg_id'].strip("<>")
        has_attachment:bool = False
        subject:str = metadata['subject']
        sender:str = metadata['from']
        receiver:str = metadata['to']
        
        try:
            sql = (
                "SELECT "
                "user_id "
                "FROM users "
                "WHERE email=%s "
            )
            
            result = connPool.execute(sql=sql, args=(receiver,), dictionary=True)
            if not result:
                print(f"There are no result for the email :{receiver}")
                return None
                
            user_id = result[0]['user_id']
            
            for node in nodes:
                if node['type'].lower() == 'text/plain':
                    body = node['content']
                    
                if node['type'].lower() == 'text/html':
                    html = node['content']
                
            insertSQL = (
                "INSERT INTO "
                "inbox_emails( "
                "user_id, message_id, sender, subject, body, html)  VALUES "
                "( %s, %s, %s, %s, %s, %s) "
            )
            
            args = (user_id, message_id, sender, subject, body, html)
                
            connPool.execute(sql=insertSQL, args= args, commit=True)
                
        except Exception as e:
            print(f'Got problem in DB operation: {str(e)}')
            
        
        
    