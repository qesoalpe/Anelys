from xml.dom import minidom
import os
import os.path
from decimal import Decimal
from dict import Dict as dict, List as list


def parse_policy_xml(poliza_xml):
    if isinstance(poliza_xml, str) and os.path.exists(poliza_xml):
        poliza_xml = minidom.parse(poliza_xml)
    elif isinstance(poliza_xml, str):
        poliza_xml = minidom.parseString(poliza_xml)
    elif isinstance(poliza_xml, minidom.Document):
        poliza_xml = poliza_xml.documentElement
    elif not isinstance(poliza_xml, (minidom.Document, minidom.Element, minidom.Node)):
        raise Exception('poliza\'s type is no correct the type is %s' % type(poliza_xml))

    poliza = dict({'date': poliza_xml.getAttribute('Fecha'), 'concept': poliza_xml.getAttribute('Concepto'),
                   'num_id': poliza_xml.getAttribute('NumUnIdenPol'), 'type': 'haley/policy'})
    transactions = list()

    for trans_xml in [node for node in poliza_xml.childNodes if node.nodeName == 'PLZ:Transaccion']:
        tx_dict = dict()
        cfdis_dict = list()
        for cfdi_dom in [node for node in trans_xml.childNodes if node.nodeName == 'PLZ:CompNal']:
            cfdi_dict = dict({'uuid': cfdi_dom.getAttribute('UUID_CFDI').upper(),
                              'third': {'rfc': cfdi_dom.getAttribute('RFC')},
                              'total': round(Decimal(cfdi_dom.getAttribute('MontoTotal')), 2)})

            if cfdi_dom.hasAttribute('Moneda') and cfdi_dom.getAttribute('Moneda') != 'MXN':
                cfdi_dict.currency = cfdi_dom.getAttribute('Moneda')
                if cfdi_dom.hasAttribute('TipCamb'):
                    cfdi_dict.fx_rate = round(Decimal(cfdi_dom.getAttribute('TipCamb')), 5)

            cfdis_dict.append(cfdi_dict)

        if len(cfdis_dict) > 1:
            tx_dict.cfdis = cfdis_dict
        elif len(cfdis_dict) == 1:
            tx_dict.cfdi = cfdis_dict[0]

        checks_dict = list()
        for check_dom in [node for node in trans_xml.childNodes if node.nodeName == 'PLZ:Cheque']:
            check_dict = dict({'number': int(check_dom.getAttribute('Num')), 'date': check_dom.getAttribute('Fecha'),
                               'account': {'number': check_dom.getAttribute('CtaOri')},
                               'bank': check_dom.getAttribute('BanEmisNal'),
                               'beneficiary': {'name': check_dom.getAttribute('Benef')},
                               'third': {'rfc': check_dom.getAttribute('RFC')},
                               'amount': round(Decimal(check_dom.getAttribute('Monto')), 2)})
            checks_dict.append(check_dict)

        if len(checks_dict) == 1:
            tx_dict.check = checks_dict[0]
        elif len(checks_dict) > 1:
            tx_dict.checks = checks_dict

        tx_dict.debit = round(Decimal(trans_xml.getAttribute('Debe')), 2)
        tx_dict.credit = round(Decimal(trans_xml.getAttribute('Haber')), 2)
        tx_dict.account = dict({'number': trans_xml.getAttribute('NumCta'),
                                'description': trans_xml.getAttribute('DesCta')})
        tx_dict.concept = trans_xml.getAttribute('Concepto')
        transactions.append(tx_dict)
    
    if len(transactions) == 1:
        poliza.transaction = transactions[0]
    elif len(transactions) > 1:
        poliza.transactions = transactions

    return poliza
