import socket
import threading
import sys

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5000


def receive_messages(sock):
    """Continuously receive and print messages from the server."""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[Disconnected from server]")
                break
            print(data.decode('utf-8'), end='')
        except (ConnectionResetError, OSError):
            print("\n[Connection closed]")
            break

    try:
        sock.close()
    except OSError:
        pass
    sys.exit(0)


def main():
    host = input(f"Server IP (press enter for default {DEFAULT_HOST}) or enter: ") or DEFAULT_HOST
    port_input = input(f"Server port (press enter for default {DEFAULT_PORT}) or enter: ")
    port = int(port_input) if port_input else DEFAULT_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print("\nConnected. Type /help for commands \n\nEnter your nickname: " )

    # start a background thread to listen for messages
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    # main loop for sending user input to the server
    try:
        while True:
            msg = input()
            if not msg: # message is empty
                continue
            sock.sendall((msg + "\n").encode('utf-8'))

            if msg.strip().lower() == '/quit':
                break
    except KeyboardInterrupt:
        # quit if crtl c or /quit
        try:
            sock.sendall(b"/quit\n")
        except OSError:
            pass
    finally:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == '__main__':
    main()
