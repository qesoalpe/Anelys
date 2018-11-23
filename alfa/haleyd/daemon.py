from sarah.acp_bson import Recipient, Pool_Handler
from sarah import dictutils
from decimal import Decimal as D
import re
from xml.dom import minidom
from xmlutils import remove_empty_nodes
from haley.cfdiutils import parse_cfdi_xml
import dictutils
from dict import Dict as dict, List as list
from katherine import d1, d5, d6

db_haley = d1.haley
coll_cfdi = db_haley.get_collection('cfdi')
coll_cfdi_xml = db_haley.get_collection('cfdi_xml')


def persist_cfdi(cfdi, xmlstring=None):
    """
    persiste los cfdis y regresa si ya existia
    :param cfdi:
    :param xmlstring:
    :return (cfdi, exists):
    """
    if isinstance(cfdi, dict) and 'type' in cfdi and cfdi.type == 'haley/cfdi':
        if xmlstring is None:
            raise Exception('if cfdi is type Dict then should put xmlstring to the cfdi_xml')

    else:
        if isinstance(cfdi, str):
            cfdi_dom = minidom.parseString(cfdi)
        elif isinstance(cfdi, minidom.Document):
            cfdi_dom = cfdi
        else:
            raise Exception('cfdi should be str or minidom.Document')

        if cfdi_dom.documentElement.nodeName != 'cfdi:Comprobante':
            raise Exception('xml should has document elememt.name = cfdi:Comprobante')

        remove_empty_nodes(cfdi_dom)
        cfdi = parse_cfdi_xml(cfdi_dom)
        xmlstring = cfdi_dom.toxml()

    r = coll_cfdi_xml.replace_one({'uuid': cfdi.uuid},
                                  {'uuid': cfdi.uuid, 'type': 'haley/cfdi_xml', 'xmlstring': xmlstring}, True)
    existed = r.matched_count == 1

    dictutils.dec_to_float(cfdi)

    coll_cfdi.replace_one({'uuid': cfdi.uuid}, cfdi, True)

    d5_session = d5.session()

    cfdi_node = dict({'uuid': cfdi.uuid, 'datetime': cfdi.datetime, 'total': cfdi.total,
                      'effect': cfdi.effect, 'version': cfdi.version})

    if 'folio' in cfdi:
        cfdi_node.folio = cfdi.folio

    result = d5_session.run('MERGE (cfdi{uuid:{uuid}}) '
                            'MERGE (emitter{rfc:{emitter_rfc}}) '
                            'MERGE (recipient{rfc:{recipient_rfc}}) '
                            'SET cfdi = {cfdi}, cfdi :haley_cfdi '
                            'MERGE (emitter)<-[:emitter]-(cfdi) '
                            'MERGE (cfdi)-[:recipient]->(recipient);',
                            {'uuid': cfdi.uuid, 'cfdi': cfdi_node,
                             'emitter_rfc': cfdi.emitter.rfc, 'recipient_rfc': cfdi.recipient.rfc})
    result.single()
    d5_session.close()
    dictutils.float_to_dec(cfdi)
    return cfdi, existed


def handle_action_parse_cfdi_xml(msg):
    if msg.cfdi_type in ['xml_string', 'xml', 'xmlstring', 'string_xml', 'stringxml'] and 'multi' not in msg or not msg.multi:
        cfdi_dom = minidom.parseString(msg.cfdi)
        remove_empty_nodes(cfdi_dom)
        cfdi = parse_cfdi_xml(cfdi_dom)
        if 'persist' not in msg or msg.persist:
            persist_cfdi(cfdi, xmlstring=cfdi_dom.toxml())
        return {'cfdi': cfdi}
    elif 'multi' in msg and msg.multi and msg.cfdi_type in ['xml_string', 'xml', 'xmlstring', 'string_xml', 'stringxml']:
        cfdis = list()
        count_existed = 0
        for cfdi in msg.cfdis:
            cfdi_dom = minidom.parseString(cfdi)
            remove_empty_nodes(cfdi_dom)
            cfdi = parse_cfdi_xml(cfdi_dom)
            if 'persist' not in msg or msg.persist:
                cfdi, existed = persist_cfdi(cfdi, xmlstring=cfdi_dom.toxml())
                if existed:
                    count_existed += 1
            cfdis.append(cfdi)
        reply = dict({'cfdis': cfdis})
        if 'persist' not in msg or msg.persist:
            reply.existed = count_existed
        return reply


def handle_action_send_cfdi(msg):
    pass


def handle_action_persist_cfdi(msg):
    if 'cfdi' in msg:
        pass


def handle_find_haley_cfdi(msg):    
    l_filter = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'emitter':
                if isinstance(v1, str):
                    l_filter['emitter.rfc'] = v1
                elif isinstance(v1, dict):
                    l_filter['emitter.rfc'] = v1['rfc']
            elif k1 == 'recipient':
                if isinstance(v1, str):
                    l_filter['recipient.rfc'] = v1
                elif isinstance(v1, dict):
                    l_filter['recipient.rfc'] = v1['rfc']
            elif k1 == 'datetime':
                if isinstance(v1, str):
                    l_filter['datetime'] = re.compile(v1 + '.*')
                elif isinstance(v1, dict):
                    l_filter['datetime'] = dict()
                    if '!gt' in v1:
                        l_filter['datetime']['$gt'] = v1['!gt']
                    if '!lt' in v1:
                        l_filter['datetime']['$lt'] = v1['lt']
    cfdis = list()
    for doc in coll_cfdi.find(l_filter, {'_id': False}):
        cfdis.append(doc)
    return {'result': cfdis}


def handle_find_one_haley_cfdi(msg):
    l_filt = dict()
    if 'query' in msg:
        for k1, v1 in msg['query'].items():
            if k1 == 'uuid':
                l_filt['uuid'] = v1
    return {'result': coll_cfdi.find_one(l_filt, {'_id': False})}


def handle_find_one_haley_cfdi_xml(msg):
    cfdi_xml = coll_cfdi_xml.find_one(msg['query'], {'_id', False})
    return {'result': cfdi_xml}


def handle_get_taxing_item(msg):
    item = msg['item']
    d6.ping(True)
    d6_cursor = d6.cursor()
    d6_cursor.execute('SELECT DISTINCT taxs.id, taxs.tax, name, rate FROM haley.tax_sale AS taxs INNER JOIN '
                      'haley.items_taxing AS taxing ON taxing.tax_sale_id = taxs.id WHERE taxing.item_sku = %s;',
                      (item['sku'],))
    reply = dict()
    reply['item'] = item
    if d6_cursor.rowcount == 0:
        pass
    elif d6_cursor.rowcount == 1:
        id, tax_type, name, rate = d6_cursor.fetchone()
        tax = {'id': id, 'tax': tax_type, 'name': name, 'rate': rate}
        if not isinstance(item['price'], dict):
            item['price'] = {'value': item['price']}
        price = item['price']
        before_tax = round(price['value'] / (1 + rate), 6)
        tax['value'] = round(before_tax * rate, 6)
        price['tax'] = tax
    elif d6_cursor.rowcount > 1:
        taxs = list()
        for id, tax_type, name, rate in d6_cursor:
            taxs.append({'id': id, 'tax': tax_type, 'name': name, 'rate': rate})
        price_value = None
        if isinstance(item['price'], dict):
            price_value = item['price']['value']
        total_taxs_rate = D()
        for tax in taxs:
            total_taxs_rate += tax['rate']
        before_taxs = round(price_value / (1 + total_taxs_rate), 6)
        for tax in taxs:
            tax['value'] = round(before_taxs * tax['rate'], 6)
        if not isinstance(item['price'], dict):
            item['price'] = {'value': item['price']}
        price = item['price']
        price['before_taxs'] = before_taxs
        price['taxs'] = taxs
    reply['item'] = item
    d6_cursor.close()
    return reply


def handle_get_haley_cfdis_no_attached(msg):
    d5_session = d5.session()
    result = d5_session.run('MATCH (recipient:haley_taxpayer{rfc:\'PILA960104HT8\'})<-[:recipient]-(cfdi:haley_cfdi) '
                            'WHERE cfdi.datetime > \'2018-09-10\' AND cfdi.effect in [\'ingress\', \'egress\'] AND '
                            'NOT ((cfdi)-[:attached]-()) RETURN cfdi.uuid as uuid')
    cfdis_uuid = [rc['uuid'] for rc in result]
    d5_session.close()
    result = list(coll_cfdi.find({'uuid': {'$in': cfdis_uuid}}, {'_id': False}))
    return {'result': result}


rr = Pool_Handler()
rr.reg('type_message=action.action=haley/parse_cfdi_xml', handle_action_parse_cfdi_xml)
rr.reg('type_message=find.type=haley/cfdi', handle_find_haley_cfdi)
rr.reg('type_message=find_one.type=haley/cfdi', handle_find_one_haley_cfdi)
rr.reg('type_message=find_one.type=haley/cfdi_xml', handle_find_one_haley_cfdi_xml)
rr.reg('type_message=request.request_type=get.get=haley/cfdis_no_attached', handle_get_haley_cfdis_no_attached)
read_msg = rr


if __name__ == '__main__':
    print("I'm haley.")
    recipient = Recipient()
    recipient.prepare('haley', read_msg)
    recipient.begin_receive_forever()
