from sarah.acp_bson import Recipient, Pool_Handler
from base64 import b64encode, b64decode
import json
from decimal import Decimal
import serial
import os

os.chdir(os.path.dirname(__file__))

ff = open('citlali_file', 'rb')
config = json.loads(b64decode(ff.read()).decode())
ff.close()
scale = None
if 'scale' in config:
    scale_cnf = config['scale']
    ser = serial.Serial()
    ser.port = scale_cnf['port']
    ser.baudrate = scale_cnf['baudrate']
    ser.bytesize = scale_cnf['bytesize']
    ser.parity = scale_cnf['parity']
    ser.stopbits = scale_cnf['stopbits']
    if isinstance(ser.stopbits, Decimal):
        ser.stopbits = float(ser.stopbits)
    ser.timeout = 0
    ser.open()
    scale = {'serial_port': ser}
    scale['seq_request_weight'] = scale_cnf['seq_request_weight'].encode()


def handle_get_dianna_local_device(msg):
    return {'local_device': config['local_device']}


def handle_get_dianna_has_scale(msg):
    return {'has_scale': scale is not None}


def handle_get_dianna_request_scale_weight(msg):
    weight = None
    if scale is not None:
        sport = scale['serial_port']
        sport.write(scale['seq_request_weight'])
        sport.flush()
        buffer = ''
        while True:
            ss = sport.read(1)
            if ss == serial.CR:
                break
            ss = ss.decode()
            if not ss.isspace() and not ss.isalpha():
                buffer += ss
        weight = Decimal(buffer)
    return {'weight': weight}


rr = Pool_Handler()
rr.reg('type_message=request.request_type=get.get=dianna/local_device', handle_get_dianna_local_device)
rr.reg('type_message=request.request_type=get.get=dianna/has_scale', handle_get_dianna_has_scale)
rr.reg('type_message=request.request_type=get.get=dianna/request_scale_weight', handle_get_dianna_request_scale_weight)
read_msg = rr

if __name__ == '__main__':
    print("I'm citlali daemon.")
    recipient = Recipient()
    recipient.prepare('citlali', read_msg)
    recipient.begin_receive_forever()
