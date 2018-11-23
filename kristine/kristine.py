
def tx_without_doubleentry():
    from katherine import d1
    from functools import reduce
    from dictutils import float_to_dec
    c = d1.kristine.transaction.find(projection={'_id': False})
    txs = [tx for tx in c]

    def vv(tx):
        float_to_dec(tx)
        if 'splits' in tx and reduce(lambda x,y: x + y.value, tx.splits, 0) != 0:
            return True
        else:
            return False

    return list(filter(vv, txs))
