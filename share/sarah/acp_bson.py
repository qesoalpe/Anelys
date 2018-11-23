from dict import Dict
import socket
import citlali
import bson
import threading
import sarah.dictutils as dictutils
from sarah.handler import Pool_Handler
from bson.codec_options import CodecOptions

bson_codec_options = CodecOptions(document_class=Dict)


class Recipient:
    def __init__(self):
        self._s = None
        self.stop = None
        self.read_msg = None

    def prepare(self, port_or_name, func_read_msg=None):
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        port = None
        if isinstance(port_or_name, int):
            port = port_or_name
        elif isinstance(port_or_name, str):
            address, port = citlali.get_address_port_recipient(port_or_name)
        elif isinstance(port_or_name, dict):
            port = port_or_name['port']
        elif isinstance(port_or_name, tuple):
            port = port_or_name[1]

        s.bind(('', port))
        self._s = s
        self.stop = False
        if func_read_msg is not None:
            self.read_msg = func_read_msg

    def start_to_serve_emitter(self, conn):
        try:
            header = bytearray(8)
            received_total = 0
            while received_total < 8:
                buffer = bytearray(8)
                buffer_size = 8 - received_total
                received = conn.recv_into(buffer, buffer_size)
                header[received_total: received_total + received] = buffer[: received]
                received_total += received

            proto = int.from_bytes(header[0:1], 'big', signed=False)
            ver = int.from_bytes(header[1:2], 'big', signed=False)
            length = int.from_bytes(header[4:8], 'big', signed=False)
            if proto == 1:
                received_total = 0
                msg = bytearray(length)
                while received_total < length:
                    buffer_size = 4096
                    buffer = bytearray(buffer_size)
                    received = conn.recv_into(buffer, buffer_size)
                    msg[received_total: received_total + received] = buffer[0: received]
                    received_total += received
                msg = bson.BSON(msg).decode(bson_codec_options)
                dictutils.float_to_dec(msg)
                answer = self.read_msg(msg)
                if answer is None:
                    answer = dict()
                # se convierten del answer los Decimal a float
                dictutils.dec_to_float(answer)
                answer = bson.BSON.encode(answer)
                header = bytearray(8)
                answer_len = len(answer)
                answer_len = answer_len.to_bytes(4, 'big')
                header[4:] = answer_len
                conn.sendall(header)
                conn.sendall(answer)
        except Exception as ex:
            print('exception:', ex.args)
            answer = {'error': True, 'error_msg': ex.args}
            answer = bson.BSON.encode(answer)
            header = bytearray(8)
            answer_len = len(answer)
            answer_len = answer_len.to_bytes(4, 'big')
            header[4:] = answer_len
            conn.sendall(header)
            conn.sendall(answer)
            # raise ex
        finally:
            conn.close()
            del conn

    def begin_receive_forever(self):
        s = self._s
        s.listen(100)
        while not self.stop:
            conn, addr = s.accept()
            thr = threading.Thread(target=self.start_to_serve_emitter, args=(conn,))
            thr.start()

    def register_handler(self, path, handler):
        if self.read_msg is not None and not isinstance(self.read_msg, Pool_Handler):
            raise Exception('No se puede registrar con un Pool_Handler cuando ya se encuentra instanciado un handler')
        if self.read_msg is None:
            self.read_msg = Pool_Handler()
        self.read_msg.register_handler(path, handler)

    reg = register_handler


class Emitter:
    proto = int(1).to_bytes(1, 'big')
    version = proto

    @staticmethod
    def send_msg(address, msg):
        dictutils.dec_to_float(msg)
        vmsg = msg
        msg = bson.BSON.encode(msg)
        dictutils.float_to_dec(vmsg)
        header = bytearray(8)
        header[0:1] = Emitter.proto
        header[1:2] = Emitter.version

        header[4:8] = len(msg).to_bytes(4, 'big')
        ss = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        ss.connect(address)
        ss.sendall(header)
        ss.sendall(msg)
        header = bytearray(8)
        ss.recv_into(header, 8)
        answer_len = int.from_bytes(header[4:8], 'big')
        received_total = 0
        answer = bytearray(answer_len)
        while received_total < answer_len:
            buffer = bytearray(1024)
            received = ss.recv_into(buffer, 1024)
            answer[received_total: received_total + received] = buffer[0:received]
            received_total += received
        answer = bson.BSON(answer).decode()
        dictutils.float_to_dec(answer)
        return Dict(answer)


class Client:
    def __init__(self, emitter_stamp, recipient):
        if emitter_stamp is None:
            emitter_stamp = {'id': 'no_identified'}
        elif isinstance(emitter_stamp, str):
            emitter_stamp = {'id': emitter_stamp}
        elif isinstance(emitter_stamp, dict):
            pass

        self._emitter_stamp = emitter_stamp
        if isinstance(recipient, str):
            recipient = citlali.get_address_port_recipient(recipient)
        self._recp_addr = recipient

    def send_msg(self, msg):
        if 'emitter' not in msg:
            msg['emitter'] = self._emitter_stamp
        answer = Emitter.send_msg(self._recp_addr, msg)

        return answer

    sendmsg = send_msg

    def __call__(self, msg):
        return self.sendmsg(msg)
