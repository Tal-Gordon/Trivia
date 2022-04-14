import socket
import Protocol
# import pygame
# from pygame.locals import *
# import sys


# pygame.init()
# pygame.mixer.init()
# screen = pygame.display.set_mode((800, 600))
# clock = pygame.time.Clock()


def build_and_send_message(conn, code, msg):
    """
    Builds a new message using Protocol, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), msg (str)
    Returns: Nothing
    """
    message = Protocol.build_message(code, msg)
    conn.sendall(message.encode())
    # print("The server was sent the following: ")
    # print(f"Command: {code}, message: {msg}")


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket.
    Prints debug info, then parses the message using Protocol.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    data = conn.recv(10021).decode()
    cmd, msg = Protocol.parse_message(data)
    if cmd != Protocol.ERROR_RETURN or msg != Protocol.ERROR_RETURN:
        # print(f"The server sent: {data}")
        # print(f"Interpretation:\nCommand: {cmd}, message: {msg}")
        return cmd, msg
    else:
        return Protocol.ERROR_RETURN, Protocol.ERROR_RETURN


def build_send_recv_parse(conn, cmd, msg):
    build_and_send_message(conn, cmd, msg)
    command, message = recv_message_and_parse(conn)
    return command, message


def connect():
    conn_confirm = False
    client = None
    while not conn_confirm:
        ip = input("IP address: ")
        port = input("Port: ")
        print(f"Attempting to connect to ({ip}, {port})...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        try:
            client.connect((ip, int(port)))
            print("Connection successful.")
            conn_confirm = True
        except:
            print("Error connecting.")
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
        login_info = "#".join(list_login_data)
        message = Protocol.build_message(Protocol.PROTOCOL_CLIENT["login_msg"], login_info)
        conn.sendall(message.encode())
        print(f"Attempting login with username '{username}' and password '{password}'...")
        command, message = recv_message_and_parse(conn)
        if command == Protocol.ERROR_RETURN or message == Protocol.ERROR_RETURN:
            error_and_exit("Unexpected error.")
        else:
            if command == Protocol.PROTOCOL_SERVER["login_failed_msg"]:
                if message != "":
                    print(f"The server refused connection because of the following: {message}")
                else:
                    print("The server refused connection without specifying why.")
            elif command == Protocol.PROTOCOL_SERVER["login_ok_msg"]:
                login_bool = True
            else:
                print(f"The server sent an unexpected message: \n{command}\n{message}")
    print("Login successful.")


def logout(conn):
    build_and_send_message(conn, Protocol.PROTOCOL_CLIENT["logout_msg"], "")
    error_and_exit("Logged out.")


def split_by_hash(msg):
    return msg.split("#")


def do_question(conn):
    do_another = True
    ans = ""
    while do_another:
        command, message = build_send_recv_parse(conn, Protocol.PROTOCOL_CLIENT["get_qstn_msg"], "")
        if command == Protocol.PROTOCOL_SERVER["your_qstn_msg"]:
            qstn_id, qstn, ans1, ans2, ans3, ans4 = split_by_hash(message)
            print(f"Question {qstn_id}: {qstn}")
            print(f"1. {ans1}\n2. {ans2}\n3. {ans3}\n4. {ans4}\n")
            satisfactory = False
            while not satisfactory:
                ans = input("Answer: ")
                if (ans[0] == '-' and ans[1:].isdigit()) or (ans.isdigit() and int(ans) > 4) or not ans.isdigit():
                    print("Unaccaptable answer. Answer must be 1-4\n")
                else:
                    satisfactory = True
            build_and_send_message(conn, Protocol.PROTOCOL_CLIENT["send_ans_msg"], f"{qstn_id}#{ans}")
            cmd, msg = recv_message_and_parse(conn)
            if cmd == Protocol.PROTOCOL_SERVER["correct_ans_msg"]:
                print("Correct!")
            elif cmd == Protocol.PROTOCOL_SERVER["wrong_ans_msg"]:
                print(f"Wrong! Correct answer was {msg}")
            answered = False
            while not answered:
                another = input("Want to do one more? [y/n] ")
                if another.lower() == "y":
                    answered = True
                elif another.lower() == "n":
                    do_another = False
                    answered = True
                else:
                    print("Unexpected input. Try again.\n")
        elif command == Protocol.PROTOCOL_SERVER["no_qstn_msg"]:
            print("No more questions left.")
            print(get_highscore(conn))
            do_another = False


def get_score(conn):
    cmd, msg = build_send_recv_parse(conn, Protocol.PROTOCOL_CLIENT["my_score_msg"], "")
    if cmd == Protocol.PROTOCOL_SERVER["your_score_msg"]:
        print(f"Your score: {msg}")


def get_highscore(conn):
    cmd, msg = build_send_recv_parse(conn, Protocol.PROTOCOL_CLIENT["highscore_msg"], "")
    if cmd == Protocol.PROTOCOL_SERVER["all_score_msg"]:
        print(f"High score table: \n{msg}")


def get_logged_players(conn):
    cmd, msg = build_send_recv_parse(conn, Protocol.PROTOCOL_CLIENT["logged_msg"], "")
    if cmd == Protocol.PROTOCOL_SERVER["logged_ans_msg"]:
        print(f"Logged players: \n{msg}")


def get_help():
    print("List of available commands: ")
    print("question - get a question from the game\nlogged - see logged users\nscore - see your personal score\n"
          "highscore - see a highscore table\nlogout - log off the game\nhelp - see available commands")


def main():
    exit_bool = False
    conn = connect()
    login(conn)
    get_help()
    while not exit_bool:
        action = input(">>>").lower().strip()

        if action == "logout":
            logout(conn)
            exit_bool = True
        elif action == "question":
            do_question(conn)
        elif action == "score":
            get_score(conn)
        elif action == "highscore":
            get_highscore(conn)
        elif action == "help":
            get_help()
        elif action == "logged":
            get_logged_players(conn)
        else:
            print("Unknown command. Please try again.")


if __name__ == '__main__':
    main()
