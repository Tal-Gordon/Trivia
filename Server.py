import random
import socket
import select
import Protocol as chatlib

IP = '127.0.0.1'
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
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), msg (str)
    Returns: Nothing
    """
    message = chatlib.build_message(code, msg)
    conn.sendall(message.encode())


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket.
    Prints debug info, then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    data = conn.recv(4096).decode()
    cmd, msg = chatlib.parse_message(data)
    if cmd != chatlib.ERROR_RETURN or msg != chatlib.ERROR_RETURN:
        return cmd, msg
    else:
        return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN


def build_send_recv_parse(conn, cmd, msg):
    build_and_send_message(conn, cmd, msg)
    command, message = recv_message_and_parse(conn)
    return command, message


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
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], error_msg)


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print('\t', c.getpeername())


def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    questions = {
        2313: {"question": "How much is 2+2", "answers": ["3", "4", "2", "1"], "correct": 2},
        4122: {"question": "What is the capital of France?", "answers": ["Lion", "Marseille", "Paris", "Montpellier"],
               "correct": 3}
    }

    return questions


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    users = {
        "test"	:	{"password" :"test" ,"score" :0 ,"questions_asked" :[]},
        "yossi"		:	{"password" :"123" ,"score" :50 ,"questions_asked" :[]},
        "master"	:	{"password" :"master" ,"score" :200 ,"questions_asked" :[]}
    }
    return users


def handle_getscore_message(conn, username):
    """
    Sends to the socket YOURSCORE message with the user's score.
    Recieves: socket and username (str)
    Returns: None (sends answer to client)
    """
    score = users[username]['score']
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER['your_score_msg'], str(score))


def handle_logout_message(conn):
    """
    Closes the given socket (in laster chapters, also remove user from logged_users dictionary)
    Receives: socket
    Returns: None
    """
    client_hostname = conn.getpeername()
    if client_hostname in logged_users.keys():
        del logged_users[client_hostname]
    conn.close()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Receives: socket, message code and data
    Returns: None (sends answer to client)
    """
    client_hostname = conn.getpeername()
    username, password = data.split("#")
    if username not in users.keys():
        send_error(conn, 'The username you entered does not exist')
        return
    if users[username]['password'] != password:
        send_error(conn, 'Wrong password')
        return
    logged_users[client_hostname] = username
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_ok_msg'], '')


def handle_question_message(conn):
    global questions
    all_questions = list(questions.keys())
    rand_question_id = random.choice(all_questions)
    chosen_question = questions[rand_question_id]
    question_text, answers = chosen_question['question'], chosen_question['answers']
    question_str = '#'.join([str(rand_question_id), question_text, answers[0], answers[1], answers[2], answers[3]])
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER['your_qstn_msg'], question_str)


def handle_highscore_message(conn):
    """
    Sends to the socket HIGHSCORE message.
    Recieves: socket
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

    build_and_send_message(conn, chatlib.PROTOCOL_SERVER['all_score_msg'], highscore_str)


def handle_logged_message(conn):
    """
    Sends to the socket LOGGED message with all the logged users
    Recieves: socket and username (str)
    Returns: None (sends answer to client)
    """
    global logged_users
    all_logged_users = logged_users.values()
    logged_str = ','.join(all_logged_users)
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER['logged_ans_msg'], logged_str)


def handle_answer_message(conn, username, data):
    splitted = data.split("#")
    if not splitted:
        send_error(conn, "Error: got empty answer")
    try:
        qstn_id, answer = int(splitted[0]), int(splitted[1])
        answer_is_correct = questions[qstn_id]['correct'] == answer
    except ValueError as e:
        qstn_id, answer = int(splitted[0]), splitted[1]
        answer_is_correct = questions[qstn_id]['correct'] == questions[qstn_id]["answers"].index(answer)+1

    if answer_is_correct:
        users[username]['score'] += CORRECT_ANSWER_POINTS
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER['correct_ans_msg'], '')
    else:
        users[username]['score'] += WRONG_ANSWER_POINTS
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER['wrong_ans_msg'], str(questions[qstn_id]['correct']))


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Receives: socket, message code and data
    Returns: None
    """
    hostname = conn.getpeername()
    hostname_logged_in = hostname in logged_users.keys()
    if not hostname_logged_in:
        pass
    if cmd == chatlib.PROTOCOL_CLIENT['login_msg']:
        handle_login_message(conn, data)
    else:
        username = logged_users[hostname]
        if cmd == chatlib.PROTOCOL_CLIENT['logout_msg']:
            handle_logout_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT['my_score_msg']:
            handle_getscore_message(conn, username)
        elif cmd == chatlib.PROTOCOL_CLIENT['highscore_msg']:
            handle_highscore_message(conn)
            pass
        elif cmd == chatlib.PROTOCOL_CLIENT['logged_msg']:
            handle_logged_message(conn)
            pass
        elif cmd == chatlib.PROTOCOL_CLIENT['get_qstn_msg']:
            handle_question_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT['send_ans_msg']:
            handle_answer_message(conn, username, data)
            pass
        else:
            send_error(conn, 'Error: Unsupported command')
            return


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions
    users = load_user_database()
    questions = load_questions()
    server = setup_socket()
    clients = [server]

    while True:
        read_list, write_list, exceptional_list = select.select(clients, clients, [])
        for conn in read_list:
            if conn is server:
                client, address = server.accept()
                print(f'Client {address} joined')
                clients.append(client)
            else:
                cmd, data = recv_message_and_parse(conn)
                if cmd is None or cmd == chatlib.PROTOCOL_CLIENT['logout_msg']:
                    handle_logout_message(conn)
                    clients.remove(conn)
                    print('Connection terminated')
                else:
                    handle_client_message(conn, cmd, data)

        for message in messages_to_send:
            conn, data = message
            if conn in write_list:
                while conn in clients:
                    conn.sendall(data.encode())

                messages_to_send.clear()


if __name__ == '__main__':
    main()
