from ctypes import WINFUNCTYPE, FormatError
import socket
import time
import threading
import queue
import random

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
player_names = [None, None]
winner_name = None
need_to_run = True
can_play = False

welcome_msg = "Welcome to Quick Maths.\nPlayer 1: {}\nPlayer 2: {}\n==\nPlease answer the following question as fast as you can:\n{}?"
game_over_msg = "Game over!\nThe correct answer was {}!\nCongratulations to the winner: {}"

server_tcp_welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

questions = ["how mush is 1+3", "how mush is 2+3", "how mush is 3+4", "how mush is 4+5", 
"how mush is 5+1", "how mush is 6+2", "how mush is 7+1", "how mush is 8+1", "how mush is 9-2", 
"how mush is 8-5", "how mush is 7-6", "how mush is 6-3", "how mush is 3-1", "how mush is 2-1",
"how much is 3*2", "how much is 4*2", "how much is 1*1", "how much is 9/3", "how much is 8/2"]

answers = ["4", "5", "7", "9", "6", "8", "8", "9", "7", "3", "1", "3", "2", "1", "6", "8", "1", "3", "4"]

NUM_OF_QUESTIONS = 19

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

def udp():
    tcp_thread = threading.Thread(target = welcome_tcp)
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
    server_tcp_welcome_sock.listen(2)
    while True:
        registration_locker1 = threading.Lock()
        registration_locker2 = threading.Lock()
        playing_locker1 = threading.Lock()
        playing_locker2 = threading.Lock()
        first_player_thread = threading.Thread(target = client_registration_running, args = (0,))
        second_player_thread = threading.Thread(target = client_registration_running, args = (1,))
        quest_num = random.randint(0,18)
        first_player_thread = threading.Thread(target = client_registration_running, args = (registration_locker1, playing_locker1, 0, quest_num))
        second_player_thread = threading.Thread(target = client_registration_running, args = (registration_locker2, playing_locker2, 1, quest_num))
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

def welcome_tcp():
    server_tcp_welcome_sock.bind(TCP_welcome_addr)
    server_tcp_welcome_sock.listen(2)
    while True:
        server_tcp_client1_sock, addr = server_tcp_welcome_sock.accept()
        server_tcp_client2_sock, addr = server_tcp_welcome_sock.accept()
        client_msg_bytes =  server_tcp_client1_sock.recv(TCP_MSG_SIZE)
        server_tcp_client1_sock.settimeout(10)
        client_name1 = client_msg_bytes.decode(FORMAT)
        client_msg_bytes =  server_tcp_client2_sock.recv(TCP_MSG_SIZE)
        server_tcp_client2_sock.settimeout(10)
        client_name2 = client_msg_bytes.decode(FORMAT)
        player_names[0] = client_name1
        player_names[1] = client_name2
        time.sleep(10)
        quest_num = random.randint(0,18)
        starting_msg = welcome_msg.format(player_names[0], player_names[1], questions[quest_num])
        starting_msg_in_bytes = starting_msg.encode(FORMAT)
        server_tcp_client1_sock.sendall(starting_msg_in_bytes)
        server_tcp_client2_sock.sendall(starting_msg_in_bytes)
        first_player_thread = threading.Thread(target = answer_recieve, args = (server_tcp_client1_sock, client_name1, client_name2, quest_num,))
        second_player_thread = threading.Thread(target = answer_recieve, args = (server_tcp_client2_sock, client_name2, client_name1, quest_num,))
        first_player_thread.start()
        second_player_thread.start()
        ending_msg = game_over_msg.format(answers[quest_num], winner_name)
        ending_msg_in_bytes = ending_msg.encode(FORMAT)
        try:
            server_tcp_client1_sock.sendall(ending_msg_in_bytes)
            server_tcp_client2_sock.sendall(ending_msg_in_bytes)
        except Exception as e:
            print(e)
            print("server problem")
        server_tcp_client1_sock.close()
        server_tcp_client2_sock.close()



def answer_recieve(server_tcp_client_sock : socket.socket, client_name, enemy_name, quest_num : int):
    global winner_name
    try:
        print("before sending")
        client_answer_in_bytes = server_tcp_client_sock.recv(TCP_MSG_SIZE)
        print("after sending")
        answering_locker.acquire()
        client_answer = client_answer_in_bytes.decode(FORMAT)
        if (winner_name == None):
            if(client_answer == answers[quest_num]):
                winner_name = client_name
            else:
                winner_name = enemy_name
        answering_locker.release()
    except Exception as e:
        print(e)
        print("server problem")
        if(winner_name == None):
            winner_name = "tie"
    

def client_registration_running(registration_locker : threading.Lock, playing_locker : threading.Lock, index_name : int, quest_num: int):
    global winner_name
    winner_name = None
    registration_locker.acquire()
    server_tcp_client_sock, addr = server_tcp_welcome_sock.accept()
    server_tcp_client_sock.settimeout(10)
    client_msg_bytes =  server_tcp_client_sock.recv(TCP_MSG_SIZE)
    client_name = client_msg_bytes.decode(FORMAT)
    print(client_name)
    player_names[index_name] = client_name
    # sock_list.insert(index_name, server_tcp_client_sock)
    registration_locker.release()
    playing_locker.acquire()
    starting_msg = welcome_msg.format(player_names[0], player_names[1], questions[quest_num])
    starting_msg_in_bytes = starting_msg.encode(FORMAT)
    server_tcp_client_sock.sendall(starting_msg_in_bytes)
    # answers_queue = queue.Queue()
    # answer_thread = threading.Thread(target = recieve_answer_running, args = (server_tcp_client_sock, answers_queue,))
    # answer_thread.start()
    # try:
    #     client_answer = answers_queue.get(block = True, timeout = 10)
    #     answering_locker.acquire
    #     if (winner_name == None):
    #         if(client_answer == "4"):
    #             winner_name = client_name
    #         else:
    #             winner_name = player_names[abs(index_name - 1)]
    #     answering_locker.release
    # except TimeoutError:
    #     winner_name = "tie"
    #     pass 
    # finally:

    try:
        client_answer_in_bytes = server_tcp_client_sock.recv(TCP_MSG_SIZE)
        answering_locker.acquire()
        client_answer = client_answer_in_bytes.decode(FORMAT)
        if (winner_name == None):
            if(client_answer == answers[quest_num]):
                winner_name = client_name
            else:
                winner_name = player_names[abs(index_name - 1)]
        answering_locker.release()
    except Exception as e:
        print(e)
        print("server problem")
        if(winner_name == None):
            winner_name = "tie"
    # server_tcp_client_sock.settimeout(None)
    # if (winner_name == None):
    #     if(client_answer == "4"):
    #         winner_name = client_name
    #     else:
    #         winner_name = player_names[abs(index_name - 1)]
    # answering_locker.release()    
    ending_msg = game_over_msg.format(answers[quest_num], winner_name)
    ending_msg_in_bytes = ending_msg.encode(FORMAT)
    try:
        server_tcp_client_sock.sendall(ending_msg_in_bytes)
    except Exception as e:
        print(e)
        print("server problem")
    server_tcp_client_sock.close()
    playing_locker.release()
    # sock_list.pop

def recieve_answer_running(server_tcp_client_sock : socket.socket , answers_queue : queue.Queue):
    client_answer_in_bytes = server_tcp_client_sock.recv(TCP_MSG_SIZE)
    answering_locker.acquire()
    client_answer = client_answer_in_bytes.decode(FORMAT)
    answers_queue.put (client_answer)


def start():
    print("Server started, listening on IP address {}".format(IP))
    broadcast_thread = threading.Thread(target = UDP_running)
    broadcast_thread.start()

start()