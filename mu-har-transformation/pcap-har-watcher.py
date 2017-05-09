#!/usr/bin/env python2

import argparse
import os
import json
import signal
import sys
import getopt
import requests
import shutil
import time
import logging
import base64
import yaml
import random
import subprocess
import urllib2


observed_pcaps = []
containers_link_info = {}

elastic_host = "http://elasticsearch"
elastic_port = "9200"
pcap_read_dir = os.environ['PCAP_READ_DIR']
har_output_dir = os.environ['HAR_OUTPUT_DIR']
container_data_dir = os.environ['CONTAINER_DATA_DIR']
container_data_file = os.environ['CONTAINER_DATA_FILE']
sleep_period = os.environ['SLEEP_PERIOD']


def get_module_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    """
    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)-4s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create a handler that will log into a file.
    logfile = 'har_' + str(random.getrandbits(32)) + '.log'
    fileHandler = logging.FileHandler(logfile)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    logger.setLevel(logging.DEBUG)
    return logger


logger = get_module_logger(__name__)


def parse_container_links(container_name):
    """
    Parses the containers.json file to extract information about the links to other containers for a given one.

    Args:
        container_name: the container to look for.
    """

    containers_links = {}
    containers_file = container_data_dir + container_data_file
    decoded = json.loads(open(containers_file).read())
    container = filter(lambda container: container_name in container['name'], decoded)
    if container: # If not empty
        containers_links = container[0]['links']

    return containers_links


def transform_pcap(root, pcap_file, inputfolder, outputfolder):
    """
    Transforms a single .pcap file into a .har file.

    Args:
        pcap_file: the pcap file
        inputfolder: the input folder.
        outputfolder: the output folder.
    Raises:
        OSError: if there is a race condition while making a directory in the outut folder, this error will arise.
    """
    new_output_folder = os.path.join(outputfolder, root.split(inputfolder, 1)[1])
    if not os.path.exists(new_output_folder):
        try:
            os.makedirs(new_output_folder)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    output_name = os.path.join(new_output_folder, pcap_file) + ".har"
    cmd = "python pcap2har {input} {output}".format(input=os.path.join(root, pcap_file), output=output_name)

    subprocess.Popen(cmd, shell=True).wait()

    return output_name


def enrich_har(har_file):
    """
    Modifies an existing HAR file with additional information about the container
    it involves and the links to other containers. Also converts base64 strings
    back into JSON format.
    Information is repeated in each entry because each one will need to be posted
    sepparately into ElasticSearch.

    Args:
        har_file: the har file
    """
    container_name = har_file.split("_")[1]

    # If the container is not yet in the saved containers info, save it for later use.
    if not container_name in containers_link_info:
        containers_link_info[container_name] = parse_container_links(container_name)

    decoded = json.loads(open(har_file).read())

    result = parse_recursive_har(decoded, har_file)

    newname = har_file[:-4] + '.trans.har'
    with open(newname, 'w') as f:
        json.dump(result, f, indent=2, encoding='utf8', sort_keys=True)
        f.write('\n')
    return newname


def parse_recursive_har(har, har_name, isBase64 = False, isEntry = False):
    """
    Transform the har object decoding the base64 strings into JSON objects.

    Args:
        har: a single HAR (json) object.
    """
    result = {}
    # If it is one of the entries in the entries[] array, enrich it with additional information.
    if isEntry == True:
        container_name = har_name.split("_")[1]
        if container_name == "default":
            interface = har_name.split('_')[2]
            result['links'] = containers_link_info
        else:
            interface = har_name.split('_')[5]
            if container_name in containers_link_info:
                result['links'] = containers_link_info[container_name]
        result['meta'] = { 'container': container_name, 'interface': interface }

    # Loop through the keys in the HAR file
    for attr, value in har.iteritems():
        # If we stumble upon base64 content, we call the function to decode it.
        if (type(har[attr]) is dict) and (attr == "content"):
            if "encoding" in har[attr].keys() and har[attr]["encoding"] == "base64" and (har[attr]["mimeType"] == "application/json" or har[attr]["mimeType"] == "application/vnd.api+json" or har[attr]["mimeType"] == "application/sparql-results+json"):
                result[attr] = parse_recursive_har(har[attr], har_name, True)
            else:
                result[attr] = parse_recursive_har(har[attr], har_name)
        # If the key is a dictionary just loop through it.
        elif type(har[attr]) is dict:
            result[attr] = parse_recursive_har(har[attr], har_name)
        # If the key is a list, some data transformation is needed.
        elif type(har[attr]) is list:
            result[attr] = []
            if attr == "entries": # Enrich each entry in the entries[] array.
                for i, val in enumerate(har[attr]):
                    result[attr].append(parse_recursive_har(val, har_name, False, True))
            elif attr == "headers": # Convert headers from an array into an object.
                result[attr] = { header['name']: header['value'] for header in har[attr] }
            else:
                for i, val in enumerate(har[attr]):
                    result[attr].append(parse_recursive_har(val, har_name))
        # If it is a value in base64 (previously detected) then decode it, otherwise return it as is.
        else:
            if attr == "text" and isBase64 == True:
                result[attr] = base64.b64decode(value)
            else:
                result[attr] = value
    return result


def post_har(har_file, index, etype):
    """
    Posts a .har file to a given index in an ElasticSearch instance.

    Args:
        har_file: the .har file name.
        index: the index name to post to in ElasticSearch.
    """
    decoded = json.loads(open(har_file).read())
    log = decoded['log']

    if log['browser']['name']:
        browser = log['browser']['name'] + "/" + log['browser']['version']

    url = elastic_host + ":" + elastic_port + "/" + index + "/" + etype + "?pretty"

    for i, entry in enumerate(log['entries']):
        entry['browser'] = browser if browser else { "name": "", "version": "mumble" }
        # del entry['response']['content'] # Delete the content? take only into account the request?
        response = requests.post(url, data = json.dumps(entry))
        logger.info(response.text)


def transformation_pipeline(inputfolder, outputfolder):
    """
    Watches the folder inputfolder for new unobserved pcap files and converts them into har format.

    Args:
        inputfolder: input folder to look for pcap files.
        outputfolder: output folder to save the converted har files.
    """
    for root, dirs, files in os.walk(inputfolder):
        for fich in files:
            if fich.endswith(".pcap") and fich not in observed_pcaps:
                logger.info("[+] File: {pcap} not yet transformed. Transforming it..".format(pcap=fich))
                # PCAP to HAR
                har_name = transform_pcap(root, fich, inputfolder, outputfolder)

                # ENRICH HAR
                logger.info("[+] File: {har} not yet enriched. Enriching it..".format(har=os.path.basename(har_name)))
                enriched_har_name = enrich_har(har_name)

                # Do not post the whole HAR in ElasticSearch, it is only created for debugging purposes.
                if not fich.split("_")[1] == "default":
                    # POST TO ElasticSearch.
                    logger.info("[+] Send file: {har} to ElasticSearch..".format(har=os.path.basename(har_name)))
                    post_har(har_name, "hars", "har")

                    # Only if it was properly transformed.
                    observed_pcaps.append(fich)


def is_elasticsearch_up():
    try:
        urllib2.urlopen(elastic_host + ":" + elastic_port, timeout=1)
        return True
    except urllib2.URLError as err:
        return False


if __name__ == '__main__':

    while not is_elasticsearch_up():
        logger.info("ElasticSearch not available yet.")
        time.sleep(2)
        continue

    while True:
        if os.path.exists(pcap_read_dir):
            transformation_pipeline(pcap_read_dir, har_output_dir)
            time.sleep(float(sleep_period))
        else:
            raise OSError('The directory' + pcap_read_dir + ' does not exist')
