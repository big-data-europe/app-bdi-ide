import os
import queries
import json
import signal
import urllib2
import sys
from time import time, sleep
from helpers import log


timenow = time()

def signal_handler(signal, frame):
    """
    Remove the containers information file if it exists upon recieving either SIGINT or SIGKILL.
    """
    msg = "[+] Clean up containers file: {dir} {file}".format(dir=os.environ['WRITE_DIR'], file=os.environ['WRITE_FILE'])
    log(msg)
    try:
        os.remove(os.environ['WRITE_DIR'] + os.environ['WRITE_FILE'])
    except OSError:
        pass
    sys.exit(0)

def is_db_up():
    try:
        urllib2.urlopen(os.environ['MU_SPARQL_ENDPOINT'], timeout=1)
        return True
    except urllib2.URLError as err:
        return False


def main_loop():
    while not is_db_up():
        log("[+] db not available")
        sleep(2)
        continue

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    log("[+] Entering main loop..")

    while True:
        log("[+] Getting the list of running containers.")
        containers = queries.list_container_events(timenow)

        log("[+] Writing the running containers into file.")
        queries.write_json_into_file(containers)

        sleep(int(os.environ['SLEEP_PERIOD']))

main_loop()
