import unittest
from dict import Dict as dict
from bethesdad import daemon


class Test_Bethesdad(unittest.TestCase):
    def test_find_document_purchase(self):
        msg = dict({'type_message': 'find', 'type': 'bethesda/document_debitable',
                    'query': {'!or': [{'payment': {'!exists': False}}, {'payments': {'!exists': False}}],
                              'purchase': {'!exists': False}}})

        answer = dict(daemon.rr(msg))
        print(len(answer.result))
