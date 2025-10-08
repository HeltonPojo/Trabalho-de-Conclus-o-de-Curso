import socket
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--message",
        default="exit",
        help="menssagem para controlar os nós",
    )
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    mensagem = args.message.encode()

    sock.sendto(mensagem, ("localhost", 5001))
    sock.sendto(mensagem, ("localhost", 5002))
