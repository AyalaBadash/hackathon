UDP_MSG_SIZE = 2048
TCP_MSG_SIZE = 2048
FORMAT = 'utf-8'

class UDP_msg:
    magic_cookie: bytes
    message_type: bytes
    server_port: bytes
    
    def __init__(self, magic_cookie, message_type, server_port):
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.server_port = server_port

    def get_magic_cookie(self):
        return self.magic_cookie

    def get_message_type(self):
        return self.message_type
        
    def get_server_port(self):
        return self.server_port

    def get_msg(self):
        return self.magic_cookie + self.message_type + self.server_port


def translate_bytes(bytes):
    msg_type = bytes[:4]
    msg_data = bytes[4]
    port = bytes[5:7]
    return msg_type.decode("utf-8"), msg_data.deocde("utf-8"), port.decode("utf-8")