import socket

CRLF = "\r\n"
def run_client():
    # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_ip = "127.0.0.1"
    server_port = 2525
    # establish connection with server
    client.connect((server_ip, server_port))

    try:
        greeting = client.recv(1024)  # Read the server's greeting
        print(greeting.decode('utf-8'))

        while True:
            # get input message from user and send it to the server
            msg = input("")
            client.send(f"{msg} {CRLF}".encode("utf-8")[:1024])

            # receive message from the server
            response = client.recv(1024)
            if not response:
                print('servre closed unexpected!')
                break
            response = response.decode("utf-8")
            print(f"{response}")
            splittedResponse = response.split(" ")

            closeCode = 221

            if int(splittedResponse[0]) == closeCode:
                break


            successDataCode = 354
            if int(splittedResponse[0]) == int(f'{successDataCode}'):
                while True:
                    dataLine = input("")
                    if dataLine == ".":
                        dataLineWithCRLF = f'{dataLine}{CRLF}'
                        client.send(dataLineWithCRLF.encode("utf-8"))
                        break

                    dataLineWithCRLF = f'{dataLine} {CRLF}'
                    client.send(dataLineWithCRLF.encode("utf-8"))

                response = client.recv(1024)
                response = response.decode("utf-8")
                print(f'{response}')


    except Exception as e:
        print(f"Error: {e}")
    finally:
        # close client socket (connection to the server)
        client.close()


run_client()
