from sarah.acp_bson import Client
agent_portia = Client('', 'portia')


def print_document(document, params=None):
	if params is None:
		params = {}
	answer = agent_portia({'type_message': 'action', 'action': 'portia/print_document', 'document': document, 'params': params})
