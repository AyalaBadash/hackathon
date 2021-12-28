import socket
import sys

from mediator import *
def start():
    client_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # client_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_udp_sock.bind(('', 13117))
    msg, addr = client_udp_sock.recvfrom(UDP_MSG_SIZE)
    if (msg[:4] != bytes([0xab, 0xcd, 0xdc, 0xba])) or (msg[4] != 0x2):
        print("couldn't connect - format is illegal.")
    else:
        server_ip = addr[0]
        print("Received offer from {}, attempting to connect...".format(server_ip) )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_tcp_sock:
            server_port = int(msg[5:].decode(FORMAT))
            try:
                client_tcp_sock.connect((server_ip, server_port))
                print("choose a name:")
                group_name = input() #"Kim" 
                group_name_in_bytes = group_name.encode(FORMAT)
                client_tcp_sock.sendall(group_name_in_bytes)
                try:
                    game_msg_byte = client_tcp_sock.recv(TCP_MSG_SIZE)
                    game_msg = game_msg_byte.decode(FORMAT)
                    print(game_msg)
                    ans = sys.stdin.read(1)
                    client_tcp_sock.send(ans.encode(FORMAT))
                    try:
                        score_msg_byte = client_tcp_sock.recv(TCP_MSG_SIZE)
                        score_msg = score_msg_byte.decode(FORMAT)
                        print(score_msg)
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e) 
            except Exception as e:
                print(e)
            print("Server disconnected, listening for offer requests...\n")
    client_udp_sock.close()
def main():
    print("Client started, listening for offer request...")
    while True:
        start()

main()