from helpers import log, query
from time import sleep
from itertools import groupby, ifilter
import json
import os


def prefix():
    """
    Returns a list with all the needed prefixes to query the database
    """
    string = "PREFIX dockevent: <http://ontology.aksw.org/dockevent/>\n"
    string += "PREFIX dockcontainer: <http://ontology.aksw.org/dockcontainer/>\n"
    string += "PREFIX dockcontainer_network: <http://ontology.aksw.org/dockcontainer/network/>\n"
    string += "PREFIX dockevent_type: <http://ontology.aksw.org/dockevent/types/>\n"
    string += "PREFIX dockevent_action: <http://ontology.aksw.org/dockevent/actions/>\n\n"
    return string


def get_triple_value(data, predicate):
    """
    Returns the value associated with a predicate in the result in json format
    from the triplestore.
    """
    values = filter(lambda item: predicate in item['p']['value'], data)

    # A container may have several links
    if predicate == "link":
        links = [el['o']['value'] for el in values]
        return { el.split(':')[0]: el.split(':')[1] for el in links }
    else:
        most_recent = max(values, key=lambda x: x['time']['value'])
        return most_recent['o']['value']


def write_json_into_file(data):
    """
    Writes json data into a given file.
    """
    filename = os.environ['WRITE_DIR'] + os.environ['WRITE_FILE']
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, "w") as f:
        json.dump(data, f, indent=2, encoding='utf8')
        f.write('\n')
        f.truncate()


def list_container_events(date_from):
    """
    Queries the database for all new events (after current timestamp) and returns
    a JSON object with the data.
    """
    my_query = prefix()
    my_query += "select distinct ?time ?cname ?p ?o\n"
    my_query += "where {\n"
    my_query += "?dockevent a dockevent_type:event .\n"
    my_query += "?dockevent dockevent:type dockevent_type:container .\n"
    my_query += "?dockevent dockevent:action dockevent_action:start .\n"
    my_query += "?dockevent dockevent:container ?curl .\n"
    my_query += "?dockevent dockevent:time ?time .\n"
    my_query += "?curl dockcontainer:label \"logging=true\" .\n"
    my_query += "?curl dockcontainer:name ?cname .\n"
    my_query += "?curl dockcontainer:network ?cnetwork .\n"
    my_query += "?cnetwork ?p ?o .\n"
    my_query += "FILTER (?time > \"%s\"^^<http://www.w3.org/2001/XMLSchema#int>)\n" % int(round(date_from))
    my_query += "} order by ?cname \n"

    result = query(my_query)

    custom_result = []

    for key, items in groupby(result['results']['bindings'], lambda x: x['cname']['value']):
        list_items = list(items)
        if list_items:
            custom_dict = {
                'name': key.replace("/",""),
                'data': {
                    'ipAddress': get_triple_value(list_items, 'network/ipAddress'),
                    'interface_id': get_triple_value(list_items, 'network/id'),
                    'network_name': get_triple_value(list_items, 'network/name')
                },
                'links': get_triple_value(list_items, 'link')
            }
            custom_result.append(custom_dict)

    return custom_result
