from ctypes import WINFUNCTYPE, FormatError
import socket
import time
import threading
import queue
import struct
import math
from typing import List, Match


from mediator import *

IP = socket.gethostbyname(socket.gethostname())
WELCOME_PORT = 2555
BROADCAST_PORT = 13117
BROADCAST_IP = "255.255.255.255"

broadcast_client_addr = (BROADCAST_IP, BROADCAST_PORT)
broadcast_server_addr = (IP, BROADCAST_PORT)
TCP_welcome_addr = (IP,WELCOME_PORT)
magic_cookie = bytes([0xab, 0xcd, 0xdc, 0xba])
message_type = bytes([0x2])
server_port = str(WELCOME_PORT).encode(FORMAT)
udp_msg = UDP_msg(magic_cookie, message_type, server_port)
msg = udp_msg.get_msg()
answers_queue : queue.Queue = []
player_names = [None, None]
winner_name = None
need_to_run = True
can_play = False

welcome_msg = "Welcome to Quick Maths.\nPlayer 1: {}\nPlayer 2: {}\n==\nPlease answer the following question as fast as you can:\n{}?"
game_over_msg = "Game over!\nThe correct answer was {}!\nCongratulations to the winner: {}"

server_tcp_welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


#lockers:
broadcast_locker = threading.Lock()
answering_locker = threading.Lock()

def UDP_running():
    tcp_thread = threading.Thread(target = TCP_welcome_running)
    server_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_udp_sock.bind(broadcast_server_addr)
    server_udp_sock.sendto(msg, broadcast_client_addr)
    time.sleep(1)
    tcp_thread.start()
    while True:
        broadcast_locker.acquire()
        server_udp_sock.sendto( msg, broadcast_client_addr)
        broadcast_locker.release()
        time.sleep(1)

def TCP_welcome_running():
    global can_play
    server_tcp_welcome_sock.bind(TCP_welcome_addr)
    server_tcp_welcome_sock.listen()
    while True:
        registration_locker1 = threading.Lock()
        registration_locker2 = threading.Lock()
        playing_locker1 = threading.Lock()
        playing_locker2 = threading.Lock()
        first_player_thread = threading.Thread(target = client_registration_running, args = (0,))
        second_player_thread = threading.Thread(target = client_registration_running, args = (1,))
        first_player_thread = threading.Thread(target = client_registration_running, args = (registration_locker1, playing_locker1, 0))
        second_player_thread = threading.Thread(target = client_registration_running, args = (registration_locker2, playing_locker2, 1))
        playing_locker1.acquire()
        playing_locker2.acquire()
        first_player_thread.start()
        second_player_thread.start()
        time.sleep(1)
        registration_locker1.acquire()
        print("first player registered")
        registration_locker2.acquire()
        print("second player registered")
        broadcast_locker.acquire()
        time.sleep(10)
        playing_locker1.release()
        playing_locker2.release()
        time.sleep(1)
        first_player_thread.join()
        second_player_thread.join()
        broadcast_locker.release()
    
    
def client_registration_running(registration_locker : threading.Lock, playing_locker : threading.Lock, index_name : int):
    global winner_name
    global sock_list
    winner_name = None
    registration_locker.acquire()
    server_tcp_welcome_sock.listen()
    server_tcp_client_sock, addr = server_tcp_welcome_sock.accept()
    with server_tcp_client_sock:
    # global winner_name
    # global sock_list
    # registration_locker.acquire()
    # server_tcp_welcome_sock.listen()
    # server_tcp_client_sock, addr = server_tcp_welcome_sock.accept()
        client_msg_bytes =  server_tcp_client_sock.recv(TCP_MSG_SIZE)
        client_name = client_msg_bytes.decode(FORMAT)
        print(client_name)
        player_names[index_name] = client_name
        # sock_list.insert(index_name, server_tcp_client_sock)
        registration_locker.release()
        playing_locker.acquire()
        starting_msg = welcome_msg.format(player_names[0], player_names[1], "how much is 2+2")
        starting_msg_in_bytes = starting_msg.encode(FORMAT)
        server_tcp_client_sock.sendall(starting_msg_in_bytes)
        # server_tcp_client_sock.settimeout(10)
        answer_thread = threading.Thread(target = recieve_answer_running, args = (server_tcp_client_sock,))
        answer_thread.start()
        try:
            client_answer_in_bytes = answers_queue.get(True, 10)
            client_answer = client_answer_in_bytes.decode(FORMAT)
            if (winner_name == None):
                if(client_answer == "4"):
                    winner_name = client_name
                else:
                    winner_name = player_names[abs(index_name - 1)]
        except TimeoutError:
            winner_name = "tie"
        # try:
        #     client_answer_in_bytes = server_tcp_client_sock.recv(TCP_MSG_SIZE)
        #     answering_locker.acquire()
        #     client_answer = client_answer_in_bytes.decode(FORMAT)
            # if (winner_name == None):
            #     if(client_answer == "4"):
            #         winner_name = client_name
            #     else:
            #         winner_name = player_names[abs(index_name - 1)]
        #     answering_locker.release()
        # except:
        #     if(winner_name == None):
        #         winner_name = "tie"
        # server_tcp_client_sock.settimeout(None)
        # if (winner_name == None):
        #     if(client_answer == "4"):
        #         winner_name = client_name
        #     else:
        #         winner_name = player_names[abs(index_name - 1)]
        # answering_locker.release()
        ending_msg = game_over_msg.format("4", winner_name)
        ending_msg_in_bytes = ending_msg.encode(FORMAT)
        server_tcp_client_sock.sendall(ending_msg_in_bytes)
        # server_tcp_client_sock.close()
        playing_locker.release()
        # sock_list.pop

def recieve_answer_running(server_tcp_client_sock : socket.socket):
    global answers_queue
    client_answer_in_bytes = server_tcp_client_sock.recv(TCP_MSG_SIZE)
    answering_locker.acquire()
    client_answer = client_answer_in_bytes.decode(FORMAT)
    answers_queue.put (client_answer)

def start():
    print("Server started, listening on IP address {}".format(IP))
    broadcast_thread = threading.Thread(target = UDP_running)
    broadcast_thread.start()

start()
