import pymysql
from neo4jrestclient.client import GraphDatabase as GraphDatabase_rest
from neo4j.v1 import GraphDatabase as GraphDatabase_bolt, basic_auth
mariadb_config = dict()

d8757_5_rest = GraphDatabase_rest('http://quecosas.ddns.net:7474/db/data_model', username='alejandro', password='47exI4')
d8757_5_bolt = GraphDatabase_bolt.driver('bolt://quecosas.ddns.net/7687', auth=basic_auth('alejandro', '47exI4'))



def get_item_factor_related(item, maria_cursor=None):
    close_cursor = False
    if maria_cursor is None:
        close_cursor = True
        mariadb_conn = pymysql.connect(**mariadb_config)
        maria_cursor = mariadb_conn.cursor()
    select_stmt = 'SELECT pack.sku, pack.description, item_pack.factor FROM itzamara.item_pack AS item_pack ' \
                  'INNER JOIN itzamara.item ON item.id = item_pack.item_factor_id INNER JOIN itzamara.item AS pack ' \
                  'ON pack.id = item_pack.item_pack_id WHERE item.sku = %s;'
    curr_factor = 1
    sku_to_search = item['sku']
    sku_reviewed = [item['sku']]
    items_related = list()
    all_checked = False
    while not all_checked:
        # busqueda upside
        maria_cursor.execute(select_stmt, (sku_to_search,))
        for sku, description, factor in maria_cursor:
            if sku not in sku_reviewed:
                sku_reviewed.append(sku)
                items_related.append({'sku': sku,
                                      'description': description,
                                      'factor': curr_factor * factor,
                                      'factor_type': 'up',
                                      'checked_up': False,
                                      'checked_down': False})
        for item_related in items_related:
            if 'checked_up' in item_related and not item_related['checked_up']:
                sku_to_search = item_related['sku']
                curr_factor = item_related['factor']
                del item_related['checked_up']
                break
        else:
            all_checked = True
    lowest_common = None
    sku_to_search = item['sku']
    curr_factor = 1
    while True:
        select_stmt = 'SELECT item.sku, item.description, item_pack.factor FROM itzamara.item_pack AS item_pack INNER JOIN itzamara.item ON item.id = item_pack.item_factor_id INNER JOIN itzamara.item AS pack ON pack.id = item_pack.item_pack_id WHERE pack.sku = %s LIMIT 1;'
        maria_cursor.execute(select_stmt, (sku_to_search,))
        if maria_cursor.rowcount > 0:
            for sku, description, factor in maria_cursor:
                lowest_common = {'sku': sku,
                                 'description': description,
                                 'factor': curr_factor * factor}
                sku_to_search = sku
                curr_factor = curr_factor * factor
        else:
            break
    if lowest_common is not None:
        sku_reviewed.append(lowest_common['sku'])
        lowest_common['factor_type'] = 'lowest_common'
        lowest_common['checked_up'] = False
        items_related.append(lowest_common)
        all_checked = False
        curr_factor = 1
        sku_to_search = lowest_common['sku']
        while True:
            select_stmt = 'SELECT pack.sku, pack.description, item_pack.factor FROM itzamara.item_pack AS item_pack INNER JOIN itzamara.item ON item.id = item_pack.item_factor_id INNER JOIN itzamara.item AS pack ON pack.id = item_pack.item_pack_id WHERE item.sku = %s;'
            maria_cursor.execute(select_stmt, (sku_to_search,))
            for sku, description, factor in maria_cursor:
                if sku not in sku_reviewed:
                    sku_reviewed.append(sku)
                    items_related.append({'sku': sku,
                                          'description': description,
                                          "factor": curr_factor * factor,
                                          "factor_type": 'lowest',
                                          'checked_up': False})
            for item_related in items_related:
                if 'checked_up' in item_related and not item_related['checked_up']:
                    curr_factor = item_related['checked_up']
                    sku_to_search = item_related['sku']
                    del item_related['checked_up']
                    break
            else:
                break
    for item_related in items_related:
        if 'checked_down' in item_related:
            del item_related['checked_down']
        if 'checked_up' in item_related:
            del item_related['checkep_up']
    if close_cursor:
        maria_cursor.close()
        mariadb_conn.close()
        del mariadb_conn
    return items_related
