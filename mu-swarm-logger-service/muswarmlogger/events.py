from aiodockerpy import APIClient
from aiosparql.client import SPARQLClient
import importlib
import logging
import os, sys
from typing import Any, Callable, Dict, List


logger = logging.getLogger(__name__)
on_startup_subroutines = []
event_handlers = []
module_mtimes = {}


class Event:
    def __init__(self, client: APIClient, data: dict):
        self.client = client
        self.data = data

    @property
    def type(self):
        return self.data['Type']

    @property
    def action(self):
        return self.data['Action']

    @property
    def id(self):
        return self.data['Actor']['ID']

    @property
    def attributes(self):
        return self.data['Actor']['Attributes']

    @property
    def time(self):
        return self.data['time']

    @property
    def time_nano(self):
        return self.data['timeNano']


class ContainerEvent(Event):
    _container_task = None

    @property
    def container(self):
        if self._container_task is None:
            self._container_task = self.client.loop.create_task(
                self.client.inspect_container(self.id))
        return self._container_task

    @property
    def name(self):
        return self.attributes['name']

    @property
    def status(self):
        return self.data['status']


def new_event(client: APIClient, data: Dict[str, Any]) -> None:
    event_type = data['Type']
    if event_type == "container":
        return ContainerEvent(client, data)
    else:
        logger.debug("Unrecognized event (%s): %s", event_type, data)
        return Event(client, data)


def on_startup(subroutine: Callable[[APIClient, SPARQLClient], None]) -> None:
    on_startup_subroutines.append(subroutine)


def register_event(subroutine: Callable[[Event, SPARQLClient], None]) -> None:
    module_name = subroutine.__module__
    module = sys.modules[module_name]
    stat_info = os.stat(module.__file__)
    if module_name not in module_mtimes:
        module_mtimes[module_name] = stat_info.st_mtime
    event_handlers.append(subroutine)


async def run_on_startup_subroutines(docker: APIClient, sparql: SPARQLClient) -> None:
    for subroutine in on_startup_subroutines:
        try:
            await subroutine(docker, sparql)
        except Exception:
            logger.exception("Startup subroutine failed")


def list_handlers(event: Event, reload: bool = False) -> None:
    handlers = _filter_handlers(event)
    if reload:
        changes = _detect_changes(handlers)
        if changes:
            logger.debug("Reloading modules: %s", ", ".join(changes.keys()))
            _reload_modules(changes)
            handlers = _filter_handlers(event)
    return handlers


def _detect_changes(handlers: List[Callable]) -> Dict[str, float]:
    changes = {}
    for subroutine in handlers:
        module_name = subroutine.__module__
        module = sys.modules[module_name]
        stat_info = os.stat(module.__file__)
        if module_mtimes[module_name] != stat_info.st_mtime:
            changes[module_name] = stat_info.st_mtime
    return changes


def _reload_modules(changes: Dict[str, float]) -> None:
    for module_name, st_mtime in changes.items():
        event_handlers[:] = [
            x
            for x in event_handlers
            if x.__module__ != module_name
        ]
        importlib.reload(sys.modules[module_name])
        module_mtimes[module_name] = st_mtime


def _filter_handlers(event: Event):
    event_type = type(event)
    return [
        event_handler
        for event_handler in event_handlers
        if 'event' not in event_handler.__annotations__ or
        event_handler.__annotations__['event'] is event_type
    ]
