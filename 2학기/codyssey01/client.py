import socket
import threading
import sys

BUFFER_SIZE = 1024


def receive_messages(sock: socket.socket) -> None:
    while True:
        try:
            msg = sock.recv(BUFFER_SIZE).decode('utf-8')
            if not msg:
                print('⚠️ 서버 연결이 종료되었습니다.')
                break
            print(msg, end = '') if msg.endswith('\n') else print(msg)
        except Exception:
            print('⚠️ 서버 연결이 종료되었습니다.')
            break
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        sock.close()
    except Exception:
        pass
    # 수신 스레드 종료 시 프로세스도 종료되도록 안내
    try:
        sys.exit(0)
    except SystemExit:
        pass


def start_client(host: str = '127.0.0.1', port: int = 12345) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    thread = threading.Thread(target = receive_messages, args = (sock,), daemon = True)
    thread.start()

    try:
        while True:
            msg = input()
            sock.sendall((msg + '\n').encode('utf-8'))
            if msg.strip() == '/종료':
                break
    except KeyboardInterrupt:
        try:
            sock.sendall('/종료\n'.encode('utf-8'))
        except Exception:
            pass
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        sys.exit(0)


if __name__ == '__main__':
    start_client()