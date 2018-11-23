import socket

ss = socket.socket()

ss.bind(('', 143))

import imaplib

mail = imaplib.IMAP4()
