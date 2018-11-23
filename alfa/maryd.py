from pymongo import MongoClient
from datetime import datetime
from sarah.acp_bson import Recipient
import sarah.dictutils as dictutils
import os
import json
from isodate import datetime_isoformat
os.chdir(os.path.dirname(__file__))
f = open('mary.config.json', 'rt')
config = json.load(f)
f.close()

mongo_client = MongoClient(**config['mongo']['conn'])
db_mary = mongo_client.get_database('mary')
if 'auth' in config['mongo']:
    db_mary.authenticate(**config['mongo']['auth'])
coll_msg_pending = db_mary['msg_pending']


def read_msg(msg):
    try:
        if msg['type_message'] == 'action':
            if msg['action'] == 'mary/get_my_messages':
                print('makeing poling of', msg['emitter']['id'])
                cc = coll_msg_pending.find({'recipient.id': msg['emitter']['id']})
                msgs = []
                for mm in cc:
                    msgs.append(mm['message'])
                coll_msg_pending.remove({'recipient.id': msg['emitter']['id']})
                return {'messages': msgs}
            elif msg['action'] == 'mary/remit_message':
                dictutils.dec_to_float(msg)
                coll_msg_pending.insert_one({
                    'recipient': msg['message']['recipient'],
                    'emitter': msg['emitter'],
                    'datetime': datetime_isoformat(datetime.now()),
                    'message': msg['message']
                })
    except:
        pass


if __name__ == '__main__':
    print("I'm mary.")
    recipient = Recipient()
    recipient.prepare('/mary', func_read_msg=read_msg)
    recipient.begin_receive_forever()
