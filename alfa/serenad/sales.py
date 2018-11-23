from dict import Dict

__self__ = Dict({'id': '97-3', 'path': '/sales', 'type': 'anelys/system'})

import katherine
if not katherine.login(__self__):
    raise Exception('error at login in katherine')

d1 = katherine.get_database_client('8757-1', __self__)
d5 = katherine.get_database_driver('8757-6', __self__)
d6 = katherine.get_database_connection('8757-7', __self__)


def setup(installer, **kwargs):
    pass