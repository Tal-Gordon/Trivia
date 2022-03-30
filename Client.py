import socket
import Protocol as chatlib

IP = '127.0.0.1'
# PORT = 6853
PORT = 5678


def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), msg (str)
    Returns: Nothing
    """
    message = chatlib.build_message(code, msg)
    conn.sendall(message.encode())
    print("The server was sent the following: ")
    print(f"Command: {code}, message: {msg}")


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket.
    Prints debug info, then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    data = conn.recv(4096).decode()
    cmd, msg = chatlib.parse_message(data)
    if cmd is not chatlib.ERROR_RETURN or msg is not chatlib.ERROR_RETURN:
        print(f"The server sent: {data}")
        print(f"Interpretation:\nCommand: {cmd}, message: {msg}")
        return cmd, msg
    else:
        return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN


def connect():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))
    return client


def error_and_exit(msg):
    print("The script was terminated because of the following: ")
    print(msg)
    exit()


def login(conn):
    login_bool = False
    while not login_bool:
        username = input("Username: ")
        password = input("Password: ")
        list_login_data = [username, password]
        login_info = chatlib.join_msg(list_login_data)
        message = chatlib.build_message(chatlib.PROTOCOL_CLIENT["login_msg"], login_info)
        conn.sendall(message.encode())
        print(f"Attempting login with username '{username}' and password '{password}'...")
        command, message = recv_message_and_parse(conn)
        if command is chatlib.ERROR_RETURN or message is chatlib.ERROR_RETURN:
            error_and_exit("Unexpected error")
        else:
            if command is chatlib.PROTOCOL_SERVER["login_failed_msg"]:
                if message is not "":
                    print("The server refused connection because of the following: ")
                    print(message)
                else:
                    print("The server refused connection without specifying why.")
            elif command is chatlib.PROTOCOL_SERVER["login_ok_msg"]:
                login_bool = True
    print("Login successful.")


def logout(conn):
    logout_msg = chatlib.build_message(chatlib.PROTOCOL_CLIENT["logout_msg"], "")
    error_and_exit("Logged out.")


def main():

    login(connect())
    pass


if __name__ == '__main__':
    main()
