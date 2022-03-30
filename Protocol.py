# Protocol Constants
CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol

# Protocol Messages
# In this dictionary we will have all the client and server command names
PROTOCOL_CLIENT = {
    "login_msg": "LOGIN",
    "logout_msg": "LOGOUT",
    "logged_msg": "LOGGED",
    "get_qstn_msg": "GET_QUESTION",
    "send_ans_msg": "SEND_ANSWER",
    "my_score_msg": "MY_SCORE",
    "highscore_msg": "HIGHSCORE"
}  # .. Add more commands if needed

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK",
    "login_failed_msg": "ERROR",
    "logged_ans_msg": "LOGGED_ANSWER",
    "your_qstn_msg": "YOUR_QUESTION",
    "correct_ans_msg": "CORRECT_ANSWER",
    "wrong_ans_msg": "WRONG_ANSWER",
    "your_score_msg": "YOUR_SCORE",
    "all_score_msg": "ALL_SCORE",
    "error_msg_msg": "ERROR",
    "no_qstn_msg": "NO_QUESTIONS"
}  # ..  Add more commands if needed

# Other constants
ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
    """
    Gets command name and data field and creates a valid protocol message
    Returns: str, or None if error occurred.
    """
    full_msg = ""
    if cmd not in PROTOCOL_SERVER.values() and cmd not in PROTOCOL_CLIENT.values() or len(cmd) > 16:
        return ERROR_RETURN
    else:
        if len(cmd) < 16:
            cmd += " " * (16-len(cmd))
        full_msg += f"{cmd}|"

    if len(data) > 9999:
        return ERROR_RETURN
    else:
        full_msg += f"{'0'*(4-len(str(len(data)))) + str(len(data))}|{data}"

    return full_msg


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occured, returns None.
    CCCCCCCCCCCCCCCC|LLLL|MMM...
    """
    parts = split_msg(data, 3)
    if parts is None:
        return ERROR_RETURN, ERROR_RETURN
    else:
        if len(parts[0]) > 16:
            return ERROR_RETURN, ERROR_RETURN
        else:
            parts[0] = parts[0].strip()
            if parts[0] not in PROTOCOL_SERVER.values() and parts[0] not in PROTOCOL_CLIENT.values():
                return ERROR_RETURN, ERROR_RETURN
            else:
                cmd = parts[0]

        if len(parts[1]) is not 4:
            return ERROR_RETURN, ERROR_RETURN
        else:
            parts[1] = parts[1].strip()
            if not parts[1].isdigit():
                return ERROR_RETURN, ERROR_RETURN
            else:
                parts[1] = int(parts[1].strip())
                if parts[1] < 0 or parts[1] > 9999:
                    return ERROR_RETURN, ERROR_RETURN
                else:
                    length = parts[1]

        if len(parts[2]) is not length:
            return ERROR_RETURN, ERROR_RETURN
        else:
            msg = parts[2]

        return cmd, msg


def split_msg(msg, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's delimiter (|) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occured, returns None.
    """
    toReturn = []
    if len(msg) < 22:
        return ERROR_RETURN
    else:
        if msg[16] is not DELIMITER or msg[21] is not DELIMITER:
            return ERROR_RETURN
        else:
            toReturn.append(msg[0:16])
            toReturn.append(msg[17:21])
            toReturn.append(msg[22:])
            return toReturn

def join_msg(msg_fields):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the delimiter.
    Returns: string that looks like cell1|cell2|cell3
    """
    return DELIMITER.join(msg_fields)
