import socket
from threading import Thread

from src.smtp.logger.setup import logger
from src.smtp.setuthread import ESMTPSession
#/*     The SMTP server is moderately security-sensitive. It talks to SMTP
#/*	    clients and to DNS servers on the network. The SMTP server can be
#/* 	run chrooted at fixed low privilege.
# /*    STANDARDS
# /*	RFC 821 (SMTP protocol)
# /*	RFC 1123 (Host requirements)
# /*	RFC 1652 (8bit-MIME transport)
# /*	RFC 1869 (SMTP service extensions)
# /*	RFC 1870 (Message size declaration)
# /*	RFC 1985 (ETRN command)
# /*	RFC 2034 (SMTP enhanced status codes)
# /*	RFC 2554 (AUTH command)
# /*	RFC 2821 (SMTP protocol)
# /*	RFC 2920 (SMTP pipelining)
# /*	RFC 3030 (CHUNKING without BINARYMIME)
# /*	RFC 3207 (STARTTLS command)
# /*	RFC 3461 (SMTP DSN extension)
# /*	RFC 3463 (Enhanced status codes)
# /*	RFC 3848 (ESMTP transmission types)
# /*	RFC 4409 (Message submission)
# /*	RFC 4954 (AUTH command)
# /*	RFC 5321 (SMTP protocol)
# /*	RFC 6531 (Internationalized SMTP)
# /*	RFC 6533 (Internationalized Delivery Status Notifications)
# /*	RFC 7505 ("Null MX" No Service Resource Record)
# /*	RFC 8689 (SMTP REQUIRETLS extension)


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

                # start the thread for newly connected to server
                thread = Thread(
                    target = Session.startThread,
                    daemon=True
                )
                thread.start()

if __name__ == "__main__":
    richmail = ESMTPServer()
    richmail.run()
