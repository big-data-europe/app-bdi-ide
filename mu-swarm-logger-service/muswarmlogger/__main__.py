import argparse
import asyncio
import importlib
import logging

from muswarmlogger.loop import run_loop


parser = argparse.ArgumentParser()
parser.add_argument("--debug",
    action="store_true", help="Debug mode (reload modules automatically")
parser.add_argument("--sparql-endpoint",
    type=str, help="SPARQL endpoint (MU_SPARQL_ENDPOINT by default)")
parser.add_argument("loggers", metavar="logger", type=str, nargs="+",
    help="A logger to import")


def main():
    opt = parser.parse_args()
    if opt.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    for logger in opt.loggers:
        importlib.import_module("muswarmlogger.loggers.%s" % logger)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_loop(
            sparql_endpoint=opt.sparql_endpoint, debug=opt.debug))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


try:
    main()
except (SystemExit, KeyboardInterrupt):
    exit(0)
