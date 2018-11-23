from sarah.acp_bson import Recipient
from base64 import b64decode
import json

ff = open('dianna_file', 'rb')
config = json.loads(b64decode(ff.read()).decode())
ff.close()


def handle_request(msg):
    if 'request_type' in msg:
        if msg['request_type'] == 'get':
            if msg['get'] == 'dianna/local_device':
                return {'local_device': config['local_device']}


dict_handle_msg = dict()
dict_handle_msg['request'] = handle_request


def read_msg(msg):
    if 'type_message' in msg and msg['type_message'] in dict_handle_msg:
        return dict_handle_msg[msg['type_message']](msg)


if __name__ == '__main__':
    print("I'm citlali daemon.")
    recipient = Recipient()
    recipient.prepare('citlali', read_msg)
    recipient.begin_receive_forever()
