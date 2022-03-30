import socket
import select
import Protocol

IP = '127.0.0.1'
PORT = 6853


def send_waiting_messages(wlist):
    for message in messages_to_send:
        current_socket_, data_ = message
        if current_socket_ in wlist:
            current_socket_.send(data_)
            messages_to_send.remove(message)


server_socket = socket.socket()
server_socket.bind((IP, PORT))
server_socket.listen(5)
open_client_sockets = []
messages_to_send = []

# while True:
#     read_list, write_list, error_list = select.select([server_socket] + open_client_sockets, open_client_sockets, [])
#     for current_socket in read_list:
#         if current_socket is server_socket:
#             (new_socket, address) = server_socket.accept()
#             print("New socket connected to server: ", new_socket.getpeername())
#             open_client_sockets.append(new_socket)
#         else:
#             try:
#                 print(f'{current_socket.getpeername()} sent: ')
#                 data = current_socket.recv(4096)
#                 if data == b'end':
#                     peer_id = current_socket.getpeername()
#                     open_client_sockets.remove(current_socket)
#                     print(f"Connection with client {peer_id} closed.")
#                     messages_to_send.append((current_socket, data))
#                 else:
#                     peer_id = current_socket.getpeername()
#                     print(f"client: {peer_id}", data.decode())
#                     messages_to_send.append((current_socket, b'Hello, ' + data))
#             except ConnectionResetError as error:
#                 open_client_sockets.remove(current_socket)
#                 data = f"Client {current_socket.getpeername()} disgracefully disconnected."
#                 print(data)
#                 messages_to_send.append((current_socket, data))
#     send_waiting_messages(write_list)


def main():
    pass


if __name__ == '__main__':
    main()
