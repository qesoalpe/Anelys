from isis.application import Application
from isis.file_dialog import File_Dialog
import sys
from os.path import expanduser
import os.path
from dict import Dict as dict, List as list
from sarah.acp_bson import Client
import pathlib

print('starting haley.send_cfdis_to_haleyd')

agent_haley = Client('', 'haley')
app = Application(sys.argv)
path = File_Dialog.getExistingDirectory(None, 'select cfdi\'s directory', expanduser('~'))
app.exit()
del app

if path and os.path.exists(path):
    files_path = [path / pathlib.Path(fp) for fp in os.listdir(path)]
    xmls_string = [fp.read_text('utf8') for fp in files_path if fp.is_file() and fp.suffix.lower() in ['.xml']]

    msg = dict({'type_message': 'action', 'action': 'haley/parse_cfdi_xml', 'multi': True, 'cfdis': xmls_string,
                'cfdi_type': 'xmlstring', 'persist': True})
    print('enviando mensaje')
    answer = agent_haley(msg)
    print('respuesta recibida')
    print('cfdis:', len(answer.cfdis))
    print('news:', len(answer.cfdis) - answer.existed)
    print('existed:', answer.existed)
else:
    print('path %s not exists' % path)
print('Done')
input('press enter to continue...')
