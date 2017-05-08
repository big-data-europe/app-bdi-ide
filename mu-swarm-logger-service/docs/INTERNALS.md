Internal Documentation
======================

Events Creation
---------------

A "logger" in this program is a Python module that registers a few events. It
can be loaded by executing the program with the name of the module in argument.

Example:

```
./run.py sparql print
# will load the modules print.py and sparql.py located in muswarmlogger/loggers
```

To create an event, you need to import the decorators of your choice from
`events.py` and decorate functions with it.

Example:

```python
from muswarmlogger.events import on_startup

@on_startup
async def greet_the_incoming_user(docker, sparql):
    # docker is an instance of the Docker client
    # sparql is an instance of the SPARQL client
    print("Greetings!")


from muswarmlogger.events import register_event

@register_event
async def print_any_docker_event(event, sparql):
    print("Received Docker event:", event)
    # the Docker client can be retrieved at event.client


from muswarmlogger.events import ContainerEvent, register_event

@register_event
async def print_only_container_events(event: ContainerEvent, sparql):
    print("Receveid container event:", event)
    print("Container ID is:", event.id)
```
