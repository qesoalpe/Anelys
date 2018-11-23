from xmlutils import *
import xml.dom.minidom as xml
from decimal import Decimal
from dict import Dict
from utils import *
from utils import find_one
from xml.dom import minidom


def build_folio(serie, folio):
    if serie is not None and serie and folio is not None and folio and isnumeric(serie[-1]):
        return serie + '-' + folio
    elif serie is not None and serie and folio is not None and folio and not isnumeric(serie[-1]):
        return serie + folio
    elif (serie is None or not serie) and folio is not None and folio:
        return folio


def parse_cfdi_xml_33(cfdi_xml):
    if isinstance(cfdi_xml, str):
        cfdi_xml = minidom.parseString(cfdi_xml)
    if isinstance(cfdi_xml, minidom.Document):
        cfdi_xml = cfdi_xml.documentElement
    cfdi = Dict()
    cfdi.version = '3.3'
    cfdi.type = 'haley/cfdi'
    tfd = cfdi_xml.getElementsByTagName('tfd:TimbreFiscalDigital')[0]
    cfdi.uuid = tfd.getAttribute('UUID').upper()
    cfdi.datetime = cfdi_xml.getAttribute('Fecha')
    # cfdi.datetime_certification = tfd.getAttribute('FechaTimbrado')

    if cfdi_xml.hasAttribute('Serie'):
        serie = cfdi_xml.getAttribute('Serie')
    else:
        serie = None

    if cfdi_xml.hasAttribute('Folio'):
        folio = cfdi_xml.getAttribute('Folio').lstrip('0')
    else:
        folio = None

    folio = build_folio(serie, folio)
    if folio is not None:
        cfdi.folio = folio

    tipo_de_comprobante = cfdi_xml.getAttribute('TipoDeComprobante').upper()
    if tipo_de_comprobante == 'I':
        cfdi.effect = 'ingress'
    elif tipo_de_comprobante == 'E':
        cfdi.effect = 'egress'
    elif tipo_de_comprobante == 'N':
        cfdi.effect = 'payroll'
    elif tipo_de_comprobante == 'T':
        cfdi.effect = 'transfer'
    elif tipo_de_comprobante == 'P':
        cfdi.effect = 'payment'

    node = find_one(lambda x: x.nodeName == 'cfdi:Emisor', cfdi_xml.childNodes)
    emitter = Dict({'rfc': node.getAttribute('Rfc')})
    if node.hasAttribute('Nombre') and node.getAttribute('Nombre'):
        emitter.name = node.getAttribute('Nombre')
    cfdi.emitter = emitter

    node = find_one(lambda x: x.nodeName == 'cfdi:Conceptos', cfdi_xml.childNodes)
    concepts = list()
    for concepto in [concepto for concepto in node.childNodes if concepto.nodeName == 'cfdi:Concepto']:
        concept = Dict({
            'quanty': round(Decimal(concepto.getAttribute('Cantidad')), 6),
            'description': concepto.getAttribute('Descripcion'),
            'value': round(Decimal(concepto.getAttribute('ValorUnitario')), 6),
            'amount': round(Decimal(concepto.getAttribute('Importe')), 6),
            'ClaveProdServ': concepto.getAttribute('ClaveProdServ')
        })
        for e, c in {'&apos;': '\'', '&amp;': '&', '&quot;': '"'}.items():
            if e in concept.description:
                concept.description = concept.description.replace(e, c)

        if concepto.hasAttribute('NoIdentificacion') and concepto.getAttribute('NoIdentificacion'):
            concept.number_id = concepto.getAttribute('NoIdentificacion')

        if 'number_id' in concept and emitter.rfc in ["NWM9709244W4", 'MAZ8111185X2']:
            concept.number_id = concept.number_id.lstrip('0')

        discount = concepto.getAttribute('Descuento')
        if discount and isnumeric(discount):
            concept.discount = round(Decimal(discount), 6)

        impuestos = find_one(lambda x: x.nodeName == 'cfdi:Impuestos', concepto.childNodes)
        if impuestos is not None:
            traslados = find_one(lambda x: x.nodeName == 'cfdi:Traslados', impuestos.childNodes)
            if traslados is not None:
                total_traslado = Decimal()
                for traslado in [tr for tr in traslados.childNodes if tr.nodeName == 'cfdi:Traslado']:
                    importe = traslado.getAttribute('Importe')
                    if importe and isnumeric(importe):
                        total_traslado += Decimal(importe)
                concept.amount += total_traslado
                concept.value = concept.amount / concept.quanty

        concepts.append(concept)

    cfdi.concepts = concepts

    if emitter.rfc == 'DCA930316BY9':
        from katherine import d6
        d6.ping(True)
        d6_cursor = d6.cursor()
        for concept in [c for c in cfdi.concepts if 'sku' in c or 'number_id' in c]:
            r = d6_cursor.execute('select description from piper.item where provider_id = "61-10" and sku = %s limit 1;',
                                  (concept.sku if 'sku' in concept else concept.number_id))
            if r:
                concept.description, = d6_cursor.fetchone()
            else:
                i = concept.description.find('-')
                if i >= 0 and isnumeric(concept.description[:i]):
                    concept.description = concept.description[i+1:]
        d6_cursor.close()
        d6.close()

    for node in cfdi_xml.childNodes:
        if node.nodeName == 'cfdi:Receptor':
            recipient = Dict({'rfc': node.getAttribute('Rfc')})
            if node.hasAttribute('Nombre') and node.getAttribute('Nombre'):
                recipient.name = node.getAttribute('Nombre')
            cfdi.recipient = recipient
            
        elif node.nodeName == 'cfdi:Impuestos':
            taxes = Dict()
            if node.hasAttribute('TotalImpuestosTrasladados'):
                taxes.transfered = round(Decimal(node.getAttribute('TotalImpuestosTrasladados')),  6)
            xml_transfered = find_one(lambda x: x.nodeName == 'cfdi:Traslados', node.childNodes)
            if xml_transfered is not None:
                transfered = list()
                for tax_transfered in [nn for nn in xml_transfered.childNodes if nn.nodeName == 'cfdi:Traslado']:
                    trans = Dict()
                    if tax_transfered.getAttribute('Impuesto') == '002':
                        trans.tax = 'haley/iva'
                    elif tax_transfered.getAttribute('Impuesto') == '003':
                        trans.tax = 'haley/ieps'

                    if tax_transfered.getAttribute('TipoFactor').lower() == 'tasa':
                        trans.type = 'rate'
                        trans.rate = round(Decimal(tax_transfered.getAttribute('TasaOCuota')), 6)
                    elif tax_transfered.getAttribute('TipoFactor').lower() == 'cuota':
                        trans.type = 'quota'
                        trans.quota = round(Decimal(tax_transfered.getAttribute('TasaOCuota')), 6)
                    elif tax_transfered.getAttribute('TipoFactor').lower() == 'exento':
                        trans.type = 'exempt'

                    importe = tax_transfered.getAttribute('Importe')
                    if importe and isnumeric(importe):
                        trans.amount = round(Decimal(importe), 6)
                    else:
                        trans.amount = Decimal()

                    transfered.append(trans)
                if len(transfered):
                    cfdi.transfered = transfered
            cfdi.taxes = taxes
    cfdi.subtotal = round(Decimal(cfdi_xml.getAttribute('SubTotal')), 2)

    discount = cfdi_xml.getAttribute('Descuento')
    if discount:
        discount = round(Decimal(discount), 2)
        if discount > 0:
            cfdi.discount = discount

    cfdi.total = round(Decimal(cfdi_xml.getAttribute('Total')), 2)

    return cfdi


def parse_cfdi_xml_32(cfdi_xml):
    remove_empty_nodes(cfdi_xml)
    comprobante = cfdi_xml.documentElement
    tfd = cfdi_xml.getElementsByTagName('tfd:TimbreFiscalDigital')[0]
    cfdi = Dict()
    cfdi.version = '3.2'
    cfdi['type'] = 'haley/cfdi'
    cfdi['uuid'] = tfd.getAttribute('UUID').upper()
    cfdi['datetime'] = comprobante.getAttribute('fecha')
    # cfdi['datetime_certification'] = tfd.getAttribute('FechaTimbrado')

    if comprobante.hasAttribute('serie'):
        serie = comprobante.getAttribute('serie')
    else:
        serie = None

    if comprobante.hasAttribute('folio'):
        folio = comprobante.getAttribute('folio').lstrip('0')
    else:
        folio = None

    cfdi.folio = build_folio(serie, folio)

    cfdi['total'] = round(Decimal(comprobante.getAttribute('total')), 2)
    tipo_de_comprobante = comprobante.getAttribute('tipoDeComprobante')
    
    if comprobante.hasAttribute('descuento'):
        cfdi['discount'] = round(Decimal(comprobante.getAttribute('descuento')), 2)
        if cfdi['discount'] == Decimal():
            del cfdi['discount']

    if tipo_de_comprobante == 'ingreso':
        cfdi.effect = 'ingress'
    elif tipo_de_comprobante == 'egreso':
        cfdi.effect = 'egress'
    elif tipo_de_comprobante == 'traslado':
        cfdi.effect = 'transfer'

    for node in comprobante.childNodes:
        if node.nodeName == 'cfdi:Emisor':
            cfdi['emitter'] = {'rfc': node.getAttribute('rfc')}
            if node.hasAttribute('nombre'):
                cfdi['emitter']['name'] = node.getAttribute('nombre')
        elif node.nodeName == 'cfdi:Receptor':
            cfdi['recipient'] = {'rfc': node.getAttribute('rfc')}
            if node.hasAttribute('nombre'):
                cfdi['recipient']['name'] = node.getAttribute('nombre')
        elif node.nodeName == 'cfdi:Conceptos':
            items = []
            for Concepto in node.childNodes:
                if Concepto.nodeType == xml.Node.ELEMENT_NODE:
                    item = {'description': Concepto.getAttribute('descripcion'),
                            'quanty': Decimal(Concepto.getAttribute('cantidad')),
                            'um': Concepto.getAttribute('unidad'),
                            'amount': Decimal(Concepto.getAttribute('importe')),
                            'value': Decimal(Concepto.getAttribute('valorUnitario'))}
                    if Concepto.hasAttribute('noIdentificacion'):
                        item['number_id'] = Concepto.getAttribute('noIdentificacion').lstrip('0')
                    items.append(item)
            cfdi['concepts'] = items
        elif node.nodeName == 'cfdi:Impuestos':
            taxes = {}
            if node.hasAttribute('totalImpuestosTrasladados'):
                taxes['tax_transfer_amount'] = Decimal(node.getAttribute('totalImpuestosTrasladados'))
            for type_tax in node.childNodes:
                if type_tax.nodeName == 'cfdi:Traslados':
                    transfered = []
                    for tax in type_tax.childNodes:
                        if tax.nodeType == xml.Node.ELEMENT_NODE:
                            transd = {'rate': Decimal(tax.getAttribute('tasa')),
                                      'amount': Decimal(tax.getAttribute('importe')),
                                      'name': tax.getAttribute('impuesto')}
                            if transd['name'] in ['iva', 'IVA']:
                                transd['tax'] = 'haley/iva'
                            elif transd['name'] in ['ieps', 'IEPS']:
                                transd['tax'] = 'haley/ieps'
                            transfered.append(transd)
                    taxes['transfered'] = transfered
            cfdi['taxes'] = taxes
    return cfdi


def parse_cfdi_xml(cfdi_xml):
    if isinstance(cfdi_xml, str):
        cfdi_xml = minidom.parseString(cfdi_xml)
        comprobante = cfdi_xml.documentElement
        remove_empty_nodes(comprobante)
    else:
        comprobante = cfdi_xml.documentElement
        
    if comprobante.hasAttribute('version') and comprobante.getAttribute('version') == '3.2':
        return parse_cfdi_xml_32(cfdi_xml)
    elif comprobante.hasAttribute('Version') and comprobante.getAttribute('Version') == '3.3':
        return parse_cfdi_xml_33(cfdi_xml)
