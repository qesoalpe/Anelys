from katherine import d1
from utils import find_one
from dict import Dict as dict, List as list


providers = list(d1.piper.provider.find({}, {'_id': False}))

map_type_collection = {
    'bethesda/invoice': d1.bethesda.invoice,
    'bethesda/ticket': d1.bethesda.ticket,
    'bethesda/remission': d1.bethesda.remission,
    'bethesda/sale_note': d1.bethesda.sale_note
}


def populate_purchases_for_provider(provider):
    if isinstance(provider, str):
        provider_id = provider
    elif isinstance(provider, dict):
        provider_id = provider.id
    else:
        raise Exception('proovider should be a id or a dict with id key')

    provider = find_one(lambda x: x.id == provider_id, providers)
    provider.purchases = list(d1.bethesda.purchase.find({'provider.id': provider_id}, {'_id': False},
                                                        sort=[('datetime', 1)]))


def populate_items_for_provider(provider):
    if isinstance(provider, str):
        provider_id = provider
    elif isinstance(provider, dict):
        provider_id = provider.id
    else:
        raise Exception('proovider should be a id or a dict with id key')

    provider = find_one(lambda x: x.id == provider_id, providers)
    provider['items'] = list()
    provider.concepts = list()

    items_sku = list()
    concepts_number_id = list()

    if 'purchases' not in provider:
        populate_purchases_for_provider(provider_id)

    for p in reversed(provider.purchases):
        items = p['items']
        concepts = list()

        def doit(document):
            if document.type in map_type_collection.keys():
                document = map_type_collection[document.type].find_one({'id': document.id}, {'_id': False})
                if document is not None:
                    # items.extend(document['items'])
                    if 'cfdi' in document:
                        cfdi = d1.haley.cfdi.find_one({'uuid': document.cfdi.uuid}, {'_id': False})
                        concepts.extend(cfdi.concepts)

        if 'document' in p:
            doit(p.document)
        elif 'documents' in p:
            for doc in p.documents:
                doit(doc)
        items = list(filter(lambda x: 'provider_item' in x and 'sku' in x.provider_item, items))
        concepts = list(filter(lambda x: 'number_id' in x, concepts))
        for concept in concepts:
            for k in list(concept.keys()):
                if k not in ['number_id', 'description', 'ClaveProdServ']:
                    del concept[k]
                if concept.number_id not in concepts_number_id:
                    concepts_number_id.append(concept.number_id)
                    provider.concepts.append(concept)

        for item in items:
            item.local_sku = item.sku
            item.sku = item.provider_item.sku
            if 'description' in item.provider_item:
                item.description = item.provider_item.description
            else:
                del item.description
            for k in list(item.keys()):
                if k not in ['sku', 'description', 'local_sku']:
                    del item[k]
            concept = find_one(lambda x: x.number_id == item.sku, provider.concepts)
            if concept is not None:
                if 'ClaveProdServ' in concept:
                    item.ClaveProdServ = concept.ClaveProdServ

            if item.sku not in items_sku:
                items_sku.append(item.sku)
                provider['items'].append(item)


if __name__ == '__main__':
    provider = find_one(lambda x: x.id == '61-10', providers)
    populate_items_for_provider(provider)
    print(len(provider['items']))
