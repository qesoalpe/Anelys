import os
from xml.dom import minidom
import sarah.dictutils
from haley import cfdiutils
import xmlutils
from dict import Dict
from katherine import d1, d5

coll_cfdi_xml = d1.haley.cfdi_xml
coll_cfdi = d1.haley.cfdi
path = os.getcwd()

try:
    import sys
    from PySide2.QtWidgets import QFileDialog, QApplication
    app = QApplication(sys.argv)
    path = QFileDialog.getExistingDirectory()
    app.exit()
except TypeError as e:
    print('ocurrio un error, al seleccionar un directorio para buscar cfdi\'s(.xml), se usara como ruta el cwd')
    path = os.getcwd()

print("se ha seleccionado {}".format(path))
ls = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f[-3:].lower() == 'xml']
print('fueron encontrados {} .xml'.format(len(ls)))
count_stored = 0
d5_session = d5.session()
for xml_filename in ls:
    with open(xml_filename, 'r', encoding='utf8') as xml_file:

        cfdi_dom = minidom.parseString(xml_file.read())
        if cfdi_dom.documentElement.nodeName == 'cfdi:Comprobante':
            xmlutils.remove_empty_nodes(cfdi_dom)
            uuid = cfdi_dom.getElementsByTagName('tfd:TimbreFiscalDigital')[0].getAttribute('UUID').upper()
            cfdi = coll_cfdi.find_one({'uuid': uuid}, {'_id': False})
            print('procesing uuid: ', uuid)
            if cfdi is None:
                count_stored += 1
                cfdi = cfdiutils.parse_cfdi_xml(cfdi_dom)
                sarah.dictutils.dec_to_float(cfdi)
                coll_cfdi.insert_one(cfdi)
                cfdi_xml = {'uuid': uuid, 'type': 'haley/cfdi_xml', 'xmlstring': cfdi_dom.toxml()}
                coll_cfdi_xml.replace_one({'uuid': uuid}, cfdi_xml, upsert=True)

                print('\tse inserto', uuid, 'en la base de datos')
            else:
                print('\t', uuid, 'ya se encontraba almacenado en la base de datos')
            d5_node_cfdi = Dict({'uuid': cfdi['uuid'], 'datetime': cfdi['datetime'], 'total': cfdi['total'],
                                 'effect': cfdi.effect if 'effect' in cfdi else cfdi.voucher_effect})

            if 'version' in cfdi:
                d5_node_cfdi.version = cfdi.version

            if 'folio' in cfdi:
                d5_node_cfdi['folio'] = cfdi['folio']

            result = d5_session.run('MERGE (cfdi{uuid:{uuid}}) '
                                    'MERGE (emitter:haley_taxpayer{rfc:{emitter_rfc}}) '
                                    'MERGE (recipient:haley_taxpayer{rfc:{recipient_rfc}}) '
                                    'SET cfdi = {cfdi}, cfdi :haley_cfdi '
                                    'MERGE (emitter)<-[:emitter]-(cfdi) '
                                    'MERGE (cfdi)-[:recipient]->(recipient);',
                                    {'uuid': cfdi.uuid, 'cfdi': d5_node_cfdi,
                                     'emitter_rfc': cfdi['emitter']['rfc'], 'recipient_rfc': cfdi['recipient']['rfc']})
            result.single()

d5_session.close()
if count_stored > 0:
    print("fueron almacenados {} cfdis".format(count_stored))
print('se ha terminado de analizar y almacenar los cfdis.')
input('presiona enter para finalizar')
