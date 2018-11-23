from sarah.acp_bson import Client
agent_anelys = Client('anelysd_remote', 'anelys')


def get_id_with_name(name):
    answer = agent_anelys({'type_message': 'request', 'request_type': 'get', 
    	'get': 'anelys/get_id_with_name', 'name': name})
    if 'id' in answer:
        return answer['id']
    else:
        return None
