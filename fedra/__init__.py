from pymongo import MongoClient
from dict import Dict as dict, List as list

d1 = MongoClient(document_class=dict)

module_info = {'id': '224'}

default_chunk_size = 5 * 1024 * 1024  # 5 MiB

