import unittest
from perlad import daemon
from dict import Dict as dict, List as list


class Test_Perlad(unittest.TestCase):
    def setUp(self):
        # print(self._testMethodDoc)
        pass

    def test_perla_find_provider_price_offer(self):
        msg = dict({'type_message': 'find', 'type': 'perla/provider_price_offer',
                    'query': {'item': {'sku': '1020', 'description': 'Maseca 10/1kg'}}})
        answer = daemon.rr(msg)

        if 'error' in answer:
            raise Exception()
        if 'result' not in answer:
            raise Exception()

    def test_perla_find_purchase_price(self):
        msg = dict({'type_message': 'find', 'type': 'perla/purchase_price',
                    'query': {'item': {'sku': '1020', 'description': 'Maseca 10/1kg'}}})
        answer = daemon.rr(msg)
        if 'error' in answer:
            raise Exception()
        if 'result' not in answer:
            raise Exception()

    def test_dos(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
