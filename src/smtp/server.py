import socket
from threading import Thread

# import mysql.connector
# from email_validator import EmailNotValidError, validate_email

# from src.smtp.exceptions import QuitLoopException
# from src.smtp.db.config import connPool
from src.smtp.logger.setuplog import logger
from src.smtp.setuthread import ESMTPSession



class ESMTPServer:

    def __init__(self, addressFamily=socket.AF_INET, stream=socket.SOCK_STREAM):
        self.stream = stream
        self.addressFamily = addressFamily

    def run(self, HOST="127.0.0.1", PORT=2525):
        logger.info(f"Starting server on {HOST}:{PORT}")
        with socket.socket(self.addressFamily, self.stream) as server:
            logger.debug("Connection Socket is created")
            server.bind((HOST, PORT))
            # listen for one incoming connections
            server.listen(5)
            while True:
                clientSocket, clientAddress = server.accept()
                logger.debug(f"Connected to client {clientAddress} ")

                # create a new thread session object
                Session = ESMTPSession(
                    clientSocket=clientSocket,
                    clientAddress=clientAddress
                )

                #start the thread for newly connected to service
                thread = Thread(
                    target = Session.startThread,
                    daemon=True
                )
                thread.start()

if __name__ == "__main__":
    richmail = ESMTPServer()
    richmail.run()
