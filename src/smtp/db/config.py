import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()


DB_NAME= os.environ.get('DB_NAME')
DB_USER= os.environ.get('DB_USER')
DB_PASSWORD= os.environ.get('DB_PASSWORD')
DB_HOST= os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT= os.environ.get('DB_PORT', '3306')


class DBConnection:

    def __init__(self,
        NAME,
        USER,
        PASSWORD,
        HOST,
        PORT
    ):
        self.NAME = NAME
        self.USER = USER
        self.PASSWORD = PASSWORD
        self.HOST = HOST
        self.PORT = PORT


    def connect(self):

        connection = mysql.connector.connect(
            host = self.HOST,
            port = self.PORT,
            user = self.USER,
            password = self.PASSWORD,
            database = self.NAME,
        )

        return connection

conn = DBConnection(
    NAME=DB_NAME,
    USER=DB_USER,
    PASSWORD=DB_PASSWORD,
    HOST=DB_HOST,
    PORT=DB_PORT
)
