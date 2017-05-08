from aiodockerpy import APIClient
from aiosparql.client import SPARQLClient
import asyncio
from docker.utils.utils import kwargs_from_env
import logging

from muswarmlogger.events import (
    list_handlers, new_event, run_on_startup_subroutines)


logger = logging.getLogger(__name__)


async def run_loop(sparql_endpoint=None, debug=False):
    sparql_context = SPARQLClient(sparql_endpoint)
    docker_args = kwargs_from_env()
    docker_context = APIClient(timeout=5, **docker_args)
    with sparql_context as sparql, docker_context as docker:
        await run_on_startup_subroutines(docker, sparql)
        async for x in docker.events(decode=True):
            try:
                event = new_event(docker, x)
                await asyncio.gather(
                    *(handler(event, sparql)
                    for handler in list_handlers(event, reload=debug)))
            except Exception:
                logger.exception(
                    "An error occurred during a coroutine execution. "
                    "The loop will not be interrupted.")
