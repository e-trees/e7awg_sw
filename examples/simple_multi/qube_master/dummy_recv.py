from socket import *

def recv():
    server_ip = "127.0.0.1"
    server_port = 0x4000
    addr = (server_ip, server_port)

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(addr)

    while True:
        recv_data, recv_addr = sock.recvfrom(1024)
        print("recv", recv_data, recv_addr)
        sock.sendto(recv_data, recv_addr)

if __name__ == "__main__":
    recv()
