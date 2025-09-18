import socket
import threading

BUFFER_SIZE = 1024

clients = {}          # {conn: username}
name_to_conn = {}     # {username: conn}
lock = threading.Lock()


def ensure_unique_name(base_name: str) -> str:
    with lock:
        if base_name and base_name not in name_to_conn:
            return base_name
        i = 2
        while True:
            candidate = f'{base_name if base_name else "user"}#{i}'
            if candidate not in name_to_conn:
                return candidate
            i += 1


def send_line(conn: socket.socket, message: str) -> None:
    try:
        conn.sendall((message + '\n').encode('utf-8'))
    except Exception:
        remove_client(conn)


def broadcast(message: str, exclude: socket.socket = None) -> None:
    with lock:
        targets = list(clients.keys())
    for c in targets:
        if exclude and c is exclude:
            continue
        send_line(c, message)


def remove_client(conn: socket.socket) -> None:
    username = None
    with lock:
        if conn in clients:
            username = clients.pop(conn)
            if name_to_conn.get(username) is conn:
                name_to_conn.pop(username, None)
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        conn.close()
    except Exception:
        pass
    if username:
        broadcast(f'⚠️ {username} 님이 퇴장하셨습니다.')


def handle_whisper(sender: str, raw: str) -> None:
    if raw.startswith('/w '):
        parts = raw.split(' ', 2)
    else:
        parts = raw.split(' ', 2)  # '/귓속말 '

    if len(parts) < 3:
        with lock:
            sender_conn = name_to_conn.get(sender)
        if sender_conn:
            send_line(sender_conn, '[SYSTEM] 사용법: /w 대상사용자 메시지')
        return

    target_name = parts[1]
    message = parts[2].strip()
    if not message:
        with lock:
            sender_conn = name_to_conn.get(sender)
        if sender_conn:
            send_line(sender_conn, '[SYSTEM] 귓속말 메시지가 비어있습니다.')
        return

    with lock:
        target_conn = name_to_conn.get(target_name)
        sender_conn = name_to_conn.get(sender)

    if not target_conn:
        if sender_conn:
            send_line(sender_conn, f'[SYSTEM] 대상 사용자({target_name})를 찾을 수 없습니다.')
        return

    send_line(target_conn, f'[귓속말] {sender}> {message}')
    if sender_conn:
        send_line(sender_conn, f'[귓속말] {sender} -> {target_name}: {message}')


def handle_client(conn: socket.socket, addr) -> None:
    try:
        send_line(conn, '사용자명을 입력하세요: ')
        username = conn.recv(BUFFER_SIZE).decode('utf-8').strip()
        username = ensure_unique_name(username)

        with lock:
            clients[conn] = username
            name_to_conn[username] = conn

        send_line(conn, f'[SYSTEM] 당신의 이름은 {username} 입니다.')
        broadcast(f'{username} 님이 입장하셨습니다.')

        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            msg = data.decode('utf-8').strip()
            if not msg:
                continue
            if msg == '/종료':
                send_line(conn, '연결을 종료합니다.')
                break

            if msg.startswith('/w ') or msg.startswith('/귓속말 '):
                handle_whisper(sender = username, raw = msg)
            else:
                broadcast(f'{username}> {msg}')
    except Exception:
        pass
    finally:
        remove_client(conn)


def start_server(host: str = '127.0.0.1', port: int = 12345) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f'💡 서버 시작됨 {host}:{port}')

    try:
        while True:
            conn, addr = server_socket.accept()
            t = threading.Thread(target = handle_client, args = (conn, addr), daemon = True)
            t.start()
    except KeyboardInterrupt:
        print('\n[SYSTEM] 서버를 종료합니다.')
    finally:
        with lock:
            conns = list(clients.keys())
        for c in conns:
            remove_client(c)
        try:
            server_socket.close()
        except Exception:
            pass


if __name__ == '__main__':
    start_server()