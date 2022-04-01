# uncompyle6 version 3.5.0
# Python bytecode 3.8 (3413)
# Decompiled from: Python 2.7.5 (default, Nov 16 2020, 22:23:17)
# [GCC 4.8.5 20150623 (Red Hat 4.8.5-44)]
# Embedded file name: c:\users\yahel\desktop\server_test.py
# Size of source mod 2**32: 16237 bytes
import socket, random, select
CMD_FIELD_LENGTH = 16
LENGTH_FIELD_LENGTH = 4
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH
DELIMITER = '|'
DATA_DELIMITER = '#'
PROTOCOL_CLIENT = {'login_msg':'LOGIN',
 'logout_msg':'LOGOUT',
 'getscore_msg':'MY_SCORE',
 'getlogged_msg':'LOGGED',
 'gethighscore_msg':'HIGHSCORE',
 'getquestion_msg':'GET_QUESTION',
 'sendanswer_msg':'SEND_ANSWER'}
PROTOCOL_SERVER = {'login_ok_msg':'LOGIN_OK',
 'login_failed_msg':'ERROR',
 'yourscore_msg':'YOUR_SCORE',
 'highscore_msg':'ALL_SCORE',
 'logged_msg':'LOGGED_ANSWER',
 'correct_msg':'CORRECT_ANSWER',
 'wrong_msg':'WRONG_ANSWER',
 'question_msg':'YOUR_QUESTION',
 'error_msg':'ERROR',
 'noquestions_msg':'NO_QUESTIONS'}
ERROR_RETURN = None

def build_message(cmd, data):
    """
        Gets command name (str) and data field (str) and creates a valid protocol message
        Returns: str, or None if error occured
        """
    data_length = len(data)
    cmd_length = len(cmd)
    if data_length > MAX_DATA_LENGTH:
        return ERROR_RETURN
    elif cmd_length > CMD_FIELD_LENGTH:
        return ERROR_RETURN
    else:
        padded_cmd = cmd.strip().ljust(CMD_FIELD_LENGTH)
        padded_length = str(data_length).zfill(LENGTH_FIELD_LENGTH)
        full_msg = f"{padded_cmd}{DELIMITER}{padded_length}{DELIMITER}{data}"
        return full_msg


def parse_message(full_msg):
    """
        Parses protocol message and returns command name and data field
        Returns: cmd (str), data (str). If some error occured, returns None, None
        """
    if len(full_msg) < CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1:
        return (
         ERROR_RETURN, ERROR_RETURN)
    cmd_str = full_msg[0:CMD_FIELD_LENGTH]
    length = full_msg[CMD_FIELD_LENGTH + 1:CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH]
    if full_msg[CMD_FIELD_LENGTH] != DELIMITER or full_msg[(CMD_FIELD_LENGTH + LENGTH_FIELD_LENGTH + 1)] != DELIMITER:
        return (ERROR_RETURN, ERROR_RETURN)
    elif not length.strip().isdigit():
        return (ERROR_RETURN, ERROR_RETURN)
    length = int(length)
    data_str = full_msg[MSG_HEADER_LENGTH:MSG_HEADER_LENGTH + length]
    if not len(data_str) == length:
        return (ERROR_RETURN, ERROR_RETURN)
    else:
        return (
         cmd_str.strip(), data_str)


def split_data(msg, expected_fields):
    """
        Helper method. gets a string and number of expected fields in it. Splits the string
        using protocol's data field delimiter (|#) and validates that there are correct number of fields.
        Returns: list of fields if all ok. If some error occured, returns None
        """
    splitted = msg.split(DATA_DELIMITER)
    if len(splitted) == expected_fields:
        return splitted
    else:
        return


def join_data(msg_fields):
    """
        Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
        Returns: string that looks like cell1#cell2#cell3
        """
    return DATA_DELIMITER.join(msg_fields)


users = {}
questions = {}
logged_users = {}
messages_to_send = []
ERROR_MSG = 'Error! '
SERVER_PORT = 5678
CORRECT_ANSWER_POINTS = 5
WRONG_ANSWER_POINTS = 0

def build_and_send_message(conn, cmd, data):
    """
    Builds a new message using chatlib, wanted command and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), cmd (str), data (str)
    Returns: Nothing
    """
    global messages_to_send
    full_msg = build_message(cmd, data)
    host = conn.getpeername()
    print('[SERVER] ', host, 'msg: ', full_msg)
    messages_to_send.append((conn, full_msg))


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    full_msg = conn.recv(MAX_MSG_LENGTH).decode()
    host = conn.getpeername()
    print('[CLIENT] ', host, 'msg: ', full_msg)
    cmd, data = parse_message(full_msg)
    return (
     cmd, data)


def load_questions():
    """
    Loads questions bank from file  ## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    questions = {2313:{'question':'How much is 2+2',
      'answers':['3', '4', '2', '1'],  'correct':2},
     4122:{'question':'What is the capital of France?',
      'answers':['Lion', 'Marseille', 'Paris', 'Montpellier'],  'correct':3}}
    return questions


def load_user_database():
    """
    Loads users list from file  ## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    users = {'test':{'password':'test',
      'score':0,  'questions_asked':[]},
     'abc':{'password':'123',
      'score':50,  'questions_asked':[]},
     'master':{'password':'master',
      'score':200,  'questions_asked':[]}}
    return users


def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (
     '', SERVER_PORT)
    print(('starting up on {} port {}'.format)(*server_address))
    sock.bind(server_address)
    sock.listen(1)
    return sock


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, PROTOCOL_SERVER['error_msg'], ERROR_MSG + error_msg)


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print('\t', c.getpeername())


def create_random_question():
    """
    Returns a string representing a YOUR_QUESTION command, using random picked question
    Example: id|question|answer1|answer2|answer3|answer4
    """
    global questions
    all_questions = list(questions.keys())
    rand_question_id = random.choice(all_questions)
    chosen_question = questions[rand_question_id]
    question_text, answers = chosen_question['question'], chosen_question['answers']
    q_string = join_data([str(rand_question_id), question_text, answers[0], answers[1], answers[2], answers[3]])
    return q_string


def create_high_scores():
    global users
    data = ''
    users_and_scores = []
    for user in users.keys():
        users_and_scores.append((user, users[user]['score']))

    users_and_scores.sort(key=(lambda x: x[1]), reverse=True)
    for user, score in users_and_scores:
        data += '%s: %d\n' % (user, score)

    return data


def handle_question_message(conn):
    """
    Sends to the socket QUESTION message with new question generated by create_random_question
    Recieves: socket
    Returns: None (sends answer to client)
    """
    question_str = create_random_question()
    build_and_send_message(conn, PROTOCOL_SERVER['question_msg'], question_str)


def handle_answer_message(conn, username, data):
    """
    Check is user answer is correct, adjust user's score and responds with feedback
    Recieves: socket, username and message data
    Returns: None
    """
    splitted = split_data(data, 2)
    if not splitted:
        return
    id, answer = int(splitted[0]), int(splitted[1])
    answer_is_correct = questions[id]['correct'] == answer
    if answer_is_correct:
        users[username]['score'] += CORRECT_ANSWER_POINTS
        build_and_send_message(conn, PROTOCOL_SERVER['correct_msg'], '')
    else:
        users[username]['score'] += WRONG_ANSWER_POINTS
        build_and_send_message(conn, PROTOCOL_SERVER['wrong_msg'], str(questions[id]['correct']))


def handle_getscore_message(conn, username):
    """
    Sends to the socket YOURSCORE message with the user's score.
    Recieves: socket and username (str)
    Returns: None (sends answer to client)
    """
    score = users[username]['score']
    build_and_send_message(conn, PROTOCOL_SERVER['yourscore_msg'], str(score))


def handle_highscore_message(conn):
    """
    Sends to the socket HIGHSCORE message.
    Recieves: socket
    Returns: None (sends answer to client)
    """
    highscore_str = create_high_scores()
    build_and_send_message(conn, PROTOCOL_SERVER['highscore_msg'], highscore_str)


def handle_logged_message(conn):
    """
    Sends to the socket LOGGED message with all the logged users
    Recieves: socket and username (str)
    Returns: None (sends answer to client)
    """
    global logged_users
    all_logged_users = logged_users.values()
    logged_str = ','.join(all_logged_users)
    build_and_send_message(conn, PROTOCOL_SERVER['logged_msg'], logged_str)


def handle_logout_message(conn):
    """
    Closes the given socket, and removes the current user from the logged_users dictionary
    Recieves: socket
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
    Recieves: socket and message data
    Returns: None (sends answer to client)
    """
    client_hostname = conn.getpeername()
    username, password = split_data(data, 2)
    if username not in users.keys():
        send_error(conn, 'Username does not exist')
        return
    if users[username]['password'] != password:
        send_error(conn, 'Password does not match!')
        return
    logged_users[client_hostname] = username
    build_and_send_message(conn, PROTOCOL_SERVER['login_ok_msg'], '')


def handle_client_message(conn, cmd, data):
    """
    Gets message command and data and calls the right function to handle command
    Recieves: socket, message command and data
    Returns: None
    """
    hostname = conn.getpeername()
    hostname_logged_in = hostname in logged_users.keys()
    if not hostname_logged_in:
        pass
    if cmd == PROTOCOL_CLIENT['login_msg']:
        handle_login_message(conn, data)
    else:
        username = logged_users[hostname]
        if cmd == PROTOCOL_CLIENT['logout_msg']:
            handle_logout_message(conn)
        elif cmd == PROTOCOL_CLIENT['getscore_msg']:
            handle_getscore_message(conn, username)
        elif cmd == PROTOCOL_CLIENT['gethighscore_msg']:
            handle_highscore_message(conn)
        elif cmd == PROTOCOL_CLIENT['getlogged_msg']:
            handle_logged_message(conn)
        elif cmd == PROTOCOL_CLIENT['getquestion_msg']:
            handle_question_message(conn)
        elif cmd == PROTOCOL_CLIENT['sendanswer_msg']:
            handle_answer_message(conn, username, data)
        else:
            send_error(conn, ERROR_MSG + 'Unsupported message!')
            return


def main():
    global questions
    global users
    users = load_user_database()
    questions = load_questions()
    print('Welcome to Trivia Server!')
    server_socket = setup_socket()
    client_sockets = []
    rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])
    for current_socket in rlist:
        if current_socket is server_socket:
            client_socket, client_address = server_socket.accept()
            print('New client joined!', client_address)
            client_sockets.append(client_socket)
            print_client_sockets(client_sockets)
        else:
            cmd, data = recv_message_and_parse(current_socket)
            if cmd is None or cmd == PROTOCOL_CLIENT['logout_msg']:
                handle_logout_message(current_socket)
                client_sockets.remove(current_socket)
                print('Connection closed')
                print_client_sockets(client_sockets)
            else:
                handle_client_message(current_socket, cmd, data)

    for message in messages_to_send:
        current_socket, data = message
        if current_socket in wlist:
            while current_socket in client_sockets:
                current_socket.sendall(data.encode())

            messages_to_send.clear()


if __name__ == '__main__':
    main()
