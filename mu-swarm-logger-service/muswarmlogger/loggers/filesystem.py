from aiodockerpy import APIClient
import asyncio
from datetime import datetime
import logging
from os import environ as ENV, path

from muswarmlogger.events import ContainerEvent, register_event, on_startup


logger = logging.getLogger(__name__)
output_dir = ENV["LOG_DIR"]


async def save_container_logs(client, container, since):
    logs = await client.logs(container, stream=True, timestamps=True, since=since)
    with open(path.join(output_dir, container), "a") as fh:
        async for line in logs:
            timestamp, log = line.decode().split(" ", 1)
            print(timestamp, "|", log.rstrip(), file=fh)
        logger.info("Finished logging (container %s is stopped)", container[:12])


@register_event
async def start_logging_container(event: ContainerEvent, _):
    if not event.status == "start":
        return
    if not event.attributes.get('LOG'):
        return
    container = await event.container
    if container['Config']['Tty']:
        return
    asyncio.ensure_future(save_container_logs(event.client, event.id, event.time))
    logger.info("Logging container %s", container['Id'][:12])


@on_startup
async def start_logging_existing_containers(docker: APIClient, _):
    now = datetime.utcnow()
    containers = await docker.containers()
    for container in containers:
        container = await docker.inspect_container(container['Id'])
        if not container['Config']['Labels'].get('LOG'):
            continue
        if container['Config']['Tty']:
            continue
        asyncio.ensure_future(save_container_logs(docker, container['Id'], now))
        logger.info("Logging container %s", container['Id'][:12])
