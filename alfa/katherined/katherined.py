from sarah.handler import Pool_Handler
from katherine import d1


def handle_get_user(msg):
    if 'name' in msg:
        user = d1.katherine.user.find_one({'name': msg['name']})
        return {'user': user}
    elif 'mail' in msg:
        user = d1.katherine.user.find_one({'mail': msg['mail']})
        return {'user': user}


    
handler = Pool_Handler()

if __name__ == '__main__':
    from sarah.acp_bson import Recipient
    recipient = Recipient()
    recipient.prepare('katherine', handler)
    recipient.begin_receive_forever()
