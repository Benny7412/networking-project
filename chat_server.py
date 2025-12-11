import socket
import threading

HOST = '0.0.0.0'
PORT = 5000

clients = {} 
lock = threading.Lock()

# send message to all clients, used for things like users joining and leaving
def broadcast(message):
    with lock:
        targets = list(clients.keys())

    for sock in targets:
        try:
            sock.sendall(message.encode('utf-8'))
        except OSError:
            remove_client(sock)


def remove_client(sock):
    """Remove a client from the clients dict and notify others."""
    with lock:
        nick = clients.get(sock, "Unknown")
        if sock in clients:
            del clients[sock]

    try:
        sock.close()
    except OSError:
        pass

    broadcast(f"{nick} has left the chat.\n")


def process_command(sock, msg):
    """
    Handle a command (messages starting with '/').
    Returns False if the client should be disconnected, True otherwise.
    """
    parts = msg.split(' ', 1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ''

    with lock:
        nick = clients.get(sock, "Unknown")

    if cmd == '/list':
        # send a list of connected users
        with lock:
            names = ", ".join(clients.values())
        sock.sendall(f"Connected users: {names}\n".encode('utf-8'))
        return True

    if cmd == '/nick':
        # change name
        if not arg:
            sock.sendall(b"FAILED! Usage: /nick NAME\n")
            return True

        old = nick
        with lock:
            clients[sock] = arg
        broadcast(f"{old} is now known as {arg}\n")
        return True

    if cmd == '/help':
        # show commands
        help_text = (
            "Commands: \n"
            "  /list         - show connected users\n"
            "  /nick NAME    - change your nickname\n"
            "  /quit         - leave the chat\n"
        )
        sock.sendall(help_text.encode('utf-8'))
        return True

    if cmd == '/quit':
        # Tell client goodbye; caller will close connection
        sock.sendall(b"Goodbye!\n")
        return False

    sock.sendall(b"Unknown command. Type /help for help.\n")
    return True


def handle_client(sock, addr):
    """Handle communication with a single client."""
    try:
        nickname = sock.recv(1024).decode('utf-8').strip()
        if not nickname:
            nickname = f"{addr[0]}:{addr[1]}"

        with lock:
            clients[sock] = nickname

        sock.sendall(
            f"\nWelcome, {nickname}! Type /help for commands.\n".encode('utf-8')
        )
        broadcast(f"{nickname} has joined the chat.\n")

        # main loop
        while True:
            data = sock.recv(1024)
            if not data:
                break  # client disconnected

            msg = data.decode('utf-8').strip()
            if not msg:
                continue

            if msg.startswith('/'):
                # user entered a command
                if not process_command(sock, msg):
                    break  # user typed /quit
            else:
                # valid chat message
                with lock:
                    nick = clients.get(sock, "Unknown")
                broadcast(f"{nick}: {msg}\n")

    except (ConnectionResetError, OSError):
        pass
    finally:
        remove_client(sock)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            client_sock, addr = server_sock.accept()
            print("New connection from", addr)
            thread = threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True
            )
            thread.start()


if __name__ == '__main__':
    main()
