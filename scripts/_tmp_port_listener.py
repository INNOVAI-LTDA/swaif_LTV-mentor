import socket
import time
s = socket.socket()
s.bind(("127.0.0.1", 8137))
s.listen(1)
time.sleep(60)
