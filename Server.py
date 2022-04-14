import socket
import select
import Protocol
import random
import json

IP = socket.gethostbyname(socket.gethostname())
PORT = 6853

users = {}
questions = {}
logged_users = {}
messages_to_send = []
data_queue = {}
CORRECT_ANSWER_POINTS = 5
WRONG_ANSWER_POINTS = 0


def build_and_send_message(conn, code, msg):
    """
    Builds a new message using Protocol, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), msg (str)
    Returns: Nothing
    """
    message = Protocol.build_message(code, msg)
    conn.sendall(message.encode())


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket.
    Prints debug info, then parses the message using Protocol.
    Parameters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occurred, will return None, None
    """
    try:
        data = conn.recv(10021).decode()
        cmd, msg = Protocol.parse_message(data)
        if cmd != Protocol.ERROR_RETURN or msg != Protocol.ERROR_RETURN:
            return cmd, msg
        else:
            return Protocol.ERROR_RETURN, Protocol.ERROR_RETURN
    except ConnectionResetError:
        return Protocol.ERROR_RETURN, Protocol.ERROR_RETURN


def setup_socket():
    """
    Creates new listening socket and returns it
    Receives: -
    Returns: the socket object
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Server is up on {IP} on port {PORT}")
    sock.bind((IP, PORT))
    sock.listen(20)
    return sock


def send_error(conn, error_msg):
    """
    Send error message with given message
    Receives: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, Protocol.PROTOCOL_SERVER["error_msg"], error_msg)


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print('\t', c.getpeername())


def load_questions():
    """
    Loads questions bank from file
    Receives: -
    Returns: questions dictionary
    """
    with open('Questions.txt') as f:
        qstns = json.loads(f.read())
        new_qstns = {int(key): value for key, value in qstns.items()}
        return new_qstns


def load_user_database():
    """
    Loads users list from file
    Receives: -
    Returns: user dictionary
    """
    with open('Users.txt') as f:
        return json.loads(f.read())


def handle_getscore_message(conn, username):
    """
    Sends to the socket YOURSCORE message with the user's score.
    Receives: socket and username (str)
    Returns: None (sends answer to client)
    """
    score = users[username]['score']
    build_and_send_message(conn, Protocol.PROTOCOL_SERVER['your_score_msg'], str(score))


def handle_logout_message(conn):
    """
    Closes the given socket
    Receives: socket
    Returns: None
    """
    client_hostname = conn.getpeername()
    if client_hostname in logged_users.keys():
        del logged_users[client_hostname]
    for user_attributes in users.values():
        if client_hostname in user_attributes.values():
            user_attributes["connected_ip"] = ""
    conn.close()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Receives: socket, message code and data
    Returns: None (sends answer to client)
    """
    client_hostname = conn.getpeername()
    username, password = data[:data.find("#")], data[data.find("#")+1:]
    if username not in users.keys():
        send_error(conn, 'The username you entered does not exist')
        return
    if users[username]['password'] != password:
        send_error(conn, 'Wrong password')
        return
    if users[username]['connected_ip'] != "":
        send_error(conn, 'User already connected')
        return
    logged_users[client_hostname] = username
    users[username]['connected_ip'] = client_hostname
    build_and_send_message(conn, Protocol.PROTOCOL_SERVER['login_ok_msg'], '')


def handle_question_message(conn):
    global questions
    dont_ask = []
    for user_attributes in users.values():
        if conn.getpeername() in user_attributes.values():
            dont_ask = user_attributes["questions_asked"]

    all_questions = list(set(questions.keys())-set(dont_ask))
    if not all_questions:
        build_and_send_message(conn, Protocol.PROTOCOL_SERVER['no_qstn_msg'], "")
    else:
        rand_question_id = random.choice(all_questions)
        for user_attributes in users.values():
            if conn.getpeername() in user_attributes.values():
                user_attributes["questions_asked"].append(rand_question_id)
        chosen_question = questions[rand_question_id]
        question_text, answers = chosen_question['question'], chosen_question['answers']
        question_str = '#'.join([str(rand_question_id), question_text, answers[0], answers[1], answers[2], answers[3]])
        build_and_send_message(conn, Protocol.PROTOCOL_SERVER['your_qstn_msg'], question_str)


def handle_highscore_message(conn):
    """
    Sends to the socket HIGHSCORE message.
    Receives: socket
    Returns: None (sends answer to client)
    """
    global users
    highscore_str = ''
    users_and_scores = []
    for user in users.keys():
        users_and_scores.append((user, users[user]['score']))

    users_and_scores.sort(key=(lambda x: x[1]), reverse=True)
    for user, score in users_and_scores:
        highscore_str += '%s: %d\n' % (user, score)

    build_and_send_message(conn, Protocol.PROTOCOL_SERVER['all_score_msg'], highscore_str)


def handle_logged_message(conn):
    """
    Sends to the socket LOGGED message with all the logged users
    Receives: socket and username (str)
    Returns: None (sends answer to client)
    """
    global logged_users
    all_logged_users = logged_users.values()
    logged_str = ','.join(all_logged_users)
    build_and_send_message(conn, Protocol.PROTOCOL_SERVER['logged_ans_msg'], logged_str)


def handle_answer_message(conn, username, data):
    splitted = data.split("#")
    if not splitted:
        send_error(conn, "Error: got empty answer")
    try:
        qstn_id, answer = int(splitted[0]), int(splitted[1])
        answer_is_correct = questions[qstn_id]['correct'] == answer
        if answer_is_correct:
            users[username]['score'] += CORRECT_ANSWER_POINTS
            build_and_send_message(conn, Protocol.PROTOCOL_SERVER['correct_ans_msg'], '')
        else:
            users[username]['score'] += WRONG_ANSWER_POINTS
            build_and_send_message(conn, Protocol.PROTOCOL_SERVER['wrong_ans_msg'], str(questions[qstn_id]['correct']))
    except ValueError:
        send_error(conn, "Error: unacceptable input")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Receives: socket, message code and data
    Returns: None
    """
    hostname = conn.getpeername()
    if hostname not in logged_users.keys():
        pass
    if cmd == Protocol.PROTOCOL_CLIENT['login_msg']:
        handle_login_message(conn, data)
    else:
        username = logged_users[hostname]
        if cmd == Protocol.PROTOCOL_CLIENT['logout_msg']:
            handle_logout_message(conn)
        elif cmd == Protocol.PROTOCOL_CLIENT['my_score_msg']:
            handle_getscore_message(conn, username)
        elif cmd == Protocol.PROTOCOL_CLIENT['highscore_msg']:
            handle_highscore_message(conn)
            pass
        elif cmd == Protocol.PROTOCOL_CLIENT['logged_msg']:
            handle_logged_message(conn)
            pass
        elif cmd == Protocol.PROTOCOL_CLIENT['get_qstn_msg']:
            handle_question_message(conn)
        elif cmd == Protocol.PROTOCOL_CLIENT['send_ans_msg']:
            handle_answer_message(conn, username, data)
            pass
        else:
            send_error(conn, 'Error: Unsupported command')
            return


def main():
    global users
    global questions
    users = load_user_database()
    questions = load_questions()
    server = setup_socket()
    client_sockets = [server]

    while True:
        read_list, write_list, exceptional_list = select.select(client_sockets, client_sockets, [])
        for conn in read_list:
            if conn is server:
                client, address = server.accept()
                print(f'Client {address} connected')
                client_sockets.append(client)
            else:
                cmd, data = recv_message_and_parse(conn)
                if cmd is None or cmd == Protocol.PROTOCOL_CLIENT['logout_msg']:
                    handle_logout_message(conn)
                    client_sockets.remove(conn)
                    print(f'Connection terminated')
                else:
                    handle_client_message(conn, cmd, data)

        for message in messages_to_send:
            conn, data = message
            if conn in write_list:
                while conn in client_sockets:
                    conn.sendall(data.encode())

                messages_to_send.clear()


if __name__ == '__main__':
    main()
