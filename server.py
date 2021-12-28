import socket
import time
import threading


from mediator import *

IP = socket.gethostbyname(socket.gethostname())
WELCOME_PORT = 2555
BROADCAST_PORT = 13117
BROADCAST_IP = "255.255.255.255"

broadcast_addr = (BROADCAST_IP, BROADCAST_PORT)
TCP_welcome_addr = (IP, WELCOME_PORT)
magic_cookie = bytes(0xabcddcba)
message_type = bytes(0x2)
server_port = str(WELCOME_PORT).encode(FORMAT)
udp_msg = UDP_msg(magic_cookie, message_type, server_port)
msg = udp_msg.get_msg

#lockers:
broadcast_locker = threading.Lock()
registration_locker1 = threading.Lock()
registration_locker2 = threading.Lock()
playing_locker1 = threading.Lock()
playing_locker2 = threading.Lock()
answering_locker = threading.Lock()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_tcp_sock:
    print("Server started, listening on IP address {}".format(IP))
    server_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST)
    server_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT)
    server_udp_sock.bind(broadcast_addr)

    def UDP_running():
        tcp_thread = threading.Thread(TCP_welcome_running)
        server_udp_sock.sendto( msg, TCP_welcome_addr)
        tcp_thread.start()
        time.sleep(1)
        while True:
            broadcast_locker.acquire()
            server_udp_sock.sendto( msg, TCP_welcome_addr)
            broadcast_locker.release()
            time.sleep(1)

    def TCP_welcome_running():
        server_tcp_sock.bind((IP, WELCOME_PORT))
        first_player_thread = threading.Thread(target = client_registration_running, args = (registration_locker1, playing_locker1,))
        second_player_thread = threading.Thread(target = client_registration_running, args = (registration_locker2, playing_locker2,))
        while True:
            playing_locker1.acquire()
            playing_locker2.acquire()
            first_player_thread.start()
            second_player_thread.start()
            time.sleep(1)
            registration_locker1.acquire()
            registration_locker2.acquire()
            broadcast_locker.acquire()
            playing_locker1.release()
            playing_locker2.release()

       
    def client_registration_running(registration_locker : threading.Lock, playing_locker : threading.Lock):
        registration_locker.acquire()
        tcp


    while True:
        while True:
            send_UDP_message()
        
        get_two_players()

        timer = time.time() + 10
        while(time.time() < timer):

