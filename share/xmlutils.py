from xml.dom import minidom


def remove_empty_nodes(node):
    import os
    if isinstance(node, str) and os.path.exists(node):
        path = node
        f = open(path, 'rt', encoding='utf8')
        node = minidom.parseString(f.read())
        f.close()
        remove_empty_nodes(node)
        f = open(path, 'wt', encoding='utf8')
        r = f.write(node.toxml())
        f.close()
        return
    if node.nodeType in [minidom.Node.ELEMENT_NODE, minidom.Node.DOCUMENT_NODE]:
        for sub_node in node.childNodes[:]:
            remove_empty_nodes(sub_node)
    elif node.nodeType == minidom.Node.TEXT_NODE and node.parentNode is not None and node.data.isspace():
            node.parentNode.removeChild(node)


def make_pretty(file_name):
    xxtree = None
    try:
        xxtree = minidom.parse(file_name)
    except:
        xxtree = None
    if xxtree is None:
        f = open(file_name, 'rt', encoding='utf8')
        xxtree = minidom.parse(f)
        f.close()

    remove_empty_nodes(xxtree)
    ff = open(file_name, 'wb')
    ff.write(xxtree.toprettyxml(indent='  ', encoding='utf8'))
    ff.close()
