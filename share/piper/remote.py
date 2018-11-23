from sarah.acp_bson import Client
from dict import Dict as dict


agent = Client('', 'piper')


def get_provider_sells(provider, sorted=True):
    msg = dict({'type_message': 'request', 'request_type': 'get', 'get': 'piper/provider_sells'})
    if isinstance(provider, str):
        msg.provider = {'id': provider}
    elif isinstance(provider, dict):
        msg.provider = provider
    answer = agent(msg)
    result = answer.result
    if sorted:
        result.sort(key=lambda x: x.description)
    return result
