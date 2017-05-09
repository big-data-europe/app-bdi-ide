from aiodockerpy import APIClient
from aiosparql.client import SPARQLClient
from aiosparql.escape import escape_string
from aiosparql.syntax import Node, RDFTerm, Triples
import asyncio
from datetime import datetime
from dateutil import parser as datetime_parser
import logging
from os import environ as ENV
from uuid import uuid1

from muswarmlogger.event2rdf import Event2RDF
from muswarmlogger.events import ContainerEvent, register_event, on_startup
from muswarmlogger.prefixes import SwarmUI


logger = logging.getLogger(__name__)
graph = ENV['MU_APPLICATION_GRAPH']


async def create_container_log_concept(sparql, container):
    concept = "docklogs:%s" % container['Id']
    resp = await sparql.query("""
        ASK
        FROM <%(graph)s>
        WHERE {
            <%(concept)s> ?p ?o .
        }
        """ % {
            "graph": graph,
            "concept": concept,
        })
    if not resp['boolean']:
        resp = await sparql.update("""
            WITH <%(graph)s>
            INSERT DATA {
                <%(concept)s> dct:title %(name)s .
            }
            """ % {
                "graph": graph,
                "concept": concept,
                "name": escape_string(container['Name'][1:]),
            })
        logger.info("Created logging concept: %s", concept)
    return concept


async def save_container_logs(client, container, since, sparql, base_concept):
    logs = await client.logs(container, stream=True, timestamps=True, since=since)
    async for line in logs:
        timestamp, log = line.decode().split(" ", 1)
        uuid = uuid1(0)
        concept = "%s/log/%s" % (base_concept, uuid)
        logger.debug("Log into %s: %s", concept, log.strip())
        resp = await sparql.update("""
            WITH <%(graph)s>
            INSERT DATA {
                <%(base_concept)s> swarmui:logLine <%(concept)s> .

                <%(concept)s> mu:uuid %(uuid)s ;
                dct:issued %(timestamp)s^^xsd:dateTime ;
                dct:title %(log)s .
            }
            """ % {
                "graph": graph,
                "base_concept": base_concept,
                "concept": concept,
                "uuid": escape_string(str(uuid)),
                "timestamp": escape_string(timestamp),
                "log": escape_string(log),
            })
    logger.info("Finished logging into %s (container %s is stopped)",
                base_concept, container[:12])


async def save_container_stats(client, container, since, sparql):
    """
    Docker stats API doc:
    https://docs.docker.com/engine/api/v1.26/#operation/ContainerStats
    """
    stats = client.stats(container, decode=True)
    async for data in stats:
        uuid_pids_stats = uuid1(0)
        uuid_cpu_stats_cpu_usage = uuid1(0)
        uuid_cpu_stats_throttling_data = uuid1(0)
        uuid_cpu_stats = uuid1(0)
        uuid_precpu_stats_cpu_usage = uuid1(0)
        uuid_precpu_stats_throttling_data = uuid1(0)
        uuid_precpu_stats = uuid1(0)
        uuid_memory_stats_stats = uuid1(0)
        uuid_memory_stats = uuid1(0)
        uuid = uuid1(0)

        stats_node = Node(':%s' % uuid, {
            'a': SwarmUI.Stats,
            'mu:uuid': uuid,
            'swarmui:read': datetime_parser.parse(data['read']),
            'swarmui:preread': datetime_parser.parse(data['preread']),
            'swarmui:pidsStats': RDFTerm(':%s' % uuid_pids_stats),
            'swarmui:numProcs': data['num_procs'],
            'swarmui:cpuStats': RDFTerm(':%s' % uuid_cpu_stats),
            'swarmui:precpuStats': RDFTerm(':%s' % uuid_precpu_stats),
            'swarmui:memoryStats': RDFTerm(':%s' % uuid_memory_stats),
            'swarmui:name': data['name'],
            'swarmui:id': data['id'],
        })

        triples = Triples([stats_node])

        for if_, network in data['networks'].items():
            network_uuid = uuid1(0)
            network_node = Node(':%s' % network_uuid, {
                'a': SwarmUI.Network,
                'mu:uuid': network_uuid,
                'swarmui:interface': if_,
                'swarmui:rxBytes': network['rx_bytes'],
                'swarmui:rxPackets': network['rx_packets'],
                'swarmui:rxErrors': network['rx_errors'],
                'swarmui:rxDropped': network['rx_dropped'],
                'swarmui:txBytes': network['tx_bytes'],
                'swarmui:txPackets': network['tx_packets'],
                'swarmui:txErrors': network['tx_errors'],
                'swarmui:txDropped': network['tx_dropped'],
            })
            triples.append(network_node)
            stats_node.append(('swarmui:network', network_node))

        triples.extend([
            Node(':%s' % uuid_pids_stats, {
                'a': SwarmUI.PidsStats,
                'mu:uuid': uuid_pids_stats,
                'swarmui:current': data['pids_stats']['current'],
            }),
            Node(':%s' % uuid_cpu_stats_cpu_usage, [
                ('a', SwarmUI.CpuUsage),
                ('mu:uuid', uuid_cpu_stats_cpu_usage),
                ('swarmui:totalUsage', data['cpu_stats']['cpu_usage']['total_usage']),
            ] + [
                ('swarmui:percpuUsage', x)
                for x in data['cpu_stats']['cpu_usage'].get('percpu_usage', [])
            ] + [
                ('swarmui:usageInKernelmode', data['cpu_stats']['cpu_usage']['usage_in_kernelmode']),
                ('swarmui:usageInUsermode', data['cpu_stats']['cpu_usage']['usage_in_usermode']),
            ]),
            Node(':%s' % uuid_cpu_stats_throttling_data, {
                'a': SwarmUI.ThrottlingData,
                'mu:uuid': uuid_cpu_stats_throttling_data,
                'swarmui:periods': data['cpu_stats']['throttling_data']['periods'],
                'swarmui:throttledPeriods': data['cpu_stats']['throttling_data']['throttled_periods'],
                'swarmui:throttledTime': data['cpu_stats']['throttling_data']['throttled_time'],
            }),
            Node(':%s' % uuid_cpu_stats, {
                'a': SwarmUI.CpuStats,
                'mu:uuid': uuid_cpu_stats,
                'swarmui:cpuUsage': RDFTerm(':%s' % uuid_cpu_stats_cpu_usage),
                'swarmui:systemCpuUsage': data['cpu_stats']['system_cpu_usage'],
                'swarmui:throttlingData': RDFTerm(':%s' % uuid_cpu_stats_throttling_data),
            }),
            Node(':%s' % uuid_precpu_stats_cpu_usage, [
                ('a', SwarmUI.CpuUsage),
                ('mu:uuid', uuid_precpu_stats_cpu_usage),
                ('swarmui:totalUsage', data['precpu_stats']['cpu_usage']['total_usage']),
            ] + [
                ('swarmui:percpuUsage', x)
                for x in data['precpu_stats']['cpu_usage'].get('percpu_usage', [])
            ] + [
                ('swarmui:usageInKernelmode', data['precpu_stats']['cpu_usage']['usage_in_kernelmode']),
                ('swarmui:usageInUsermode', data['precpu_stats']['cpu_usage']['usage_in_usermode']),
            ]),
            Node(':%s' % uuid_precpu_stats_throttling_data, {
                'a': SwarmUI.ThrottlingData,
                'mu:uuid': uuid_precpu_stats_throttling_data,
                'swarmui:periods': data['precpu_stats']['throttling_data']['periods'],
                'swarmui:throttledPeriods': data['precpu_stats']['throttling_data']['throttled_periods'],
                'swarmui:throttledTime': data['precpu_stats']['throttling_data']['throttled_time'],
            }),
            Node(':%s' % uuid_precpu_stats, {
                'a': SwarmUI.PrecpuStats,
                'mu:uuid': uuid_precpu_stats,
                'swarmui:cpuUsage': RDFTerm(':%s' % uuid_precpu_stats_cpu_usage),
                'swarmui:systemCpuUsage': data['precpu_stats'].get('system_cpu_usage'),
                'swarmui:throttlingData': RDFTerm(':%s' % uuid_precpu_stats_throttling_data),
            }),
            Node(':%s' % uuid_memory_stats_stats, {
                'a': SwarmUI.Stats,
                'mu:uuid': uuid_memory_stats_stats,
                'swarmui:activeAnon': data['memory_stats']['stats']['active_anon'],
                'swarmui:activeFile': data['memory_stats']['stats']['active_file'],
                'swarmui:cache': data['memory_stats']['stats']['cache'],
                'swarmui:dirty': data['memory_stats']['stats']['dirty'],
                'swarmui:hierarchicalMemoryLimit': data['memory_stats']['stats']['hierarchical_memory_limit'],
                'swarmui:hierarchicalMemswLimit': data['memory_stats']['stats']['hierarchical_memsw_limit'],
                'swarmui:inactiveAnon': data['memory_stats']['stats']['inactive_anon'],
                'swarmui:inactiveFile': data['memory_stats']['stats']['inactive_file'],
                'swarmui:mappedFile': data['memory_stats']['stats']['mapped_file'],
                'swarmui:pgfault': data['memory_stats']['stats']['pgfault'],
                'swarmui:pgmajfault': data['memory_stats']['stats']['pgmajfault'],
                'swarmui:pgpgin': data['memory_stats']['stats']['pgpgin'],
                'swarmui:pgpgout': data['memory_stats']['stats']['pgpgout'],
                'swarmui:rss': data['memory_stats']['stats']['rss'],
                'swarmui:rssHuge': data['memory_stats']['stats']['rss_huge'],
                'swarmui:swap': data['memory_stats']['stats']['swap'],
                'swarmui:totalActiveAnon': data['memory_stats']['stats']['total_active_anon'],
                'swarmui:totalActiveFile': data['memory_stats']['stats']['total_active_file'],
                'swarmui:totalCache': data['memory_stats']['stats']['total_cache'],
                'swarmui:totalDirty': data['memory_stats']['stats']['total_dirty'],
                'swarmui:totalInactiveAnon': data['memory_stats']['stats']['total_inactive_anon'],
                'swarmui:totalInactiveFile': data['memory_stats']['stats']['total_inactive_file'],
                'swarmui:totalMappedFile': data['memory_stats']['stats']['total_mapped_file'],
                'swarmui:totalPgfault': data['memory_stats']['stats']['total_pgfault'],
                'swarmui:totalPgmajfault': data['memory_stats']['stats']['total_pgmajfault'],
                'swarmui:totalPgpgin': data['memory_stats']['stats']['total_pgpgin'],
                'swarmui:totalPgpgout': data['memory_stats']['stats']['total_pgpgout'],
                'swarmui:totalRss': data['memory_stats']['stats']['total_rss'],
                'swarmui:totalRssHuge': data['memory_stats']['stats']['total_rss_huge'],
                'swarmui:totalSwap': data['memory_stats']['stats']['total_swap'],
                'swarmui:totalUnevictable': data['memory_stats']['stats']['total_unevictable'],
                'swarmui:totalWriteback': data['memory_stats']['stats']['total_writeback'],
                'swarmui:unevictable': data['memory_stats']['stats']['unevictable'],
                'swarmui:writeback': data['memory_stats']['stats']['writeback'],
            }),
            Node(':%s' % uuid_memory_stats, {
                'a': SwarmUI.MemoryStats,
                'mu:uuid': uuid_memory_stats,
                'swarmui:usage': data['memory_stats']['usage'],
                'swarmui:maxUsage': data['memory_stats']['max_usage'],
                'swarmui:stats': RDFTerm(':%s' % uuid_memory_stats_stats),
                'swarmui:limit': data['memory_stats']['limit'],
            }),
        ])
        await sparql.update("""
            PREFIX : <http://ontology.aksw.org/dockstats/>

            WITH {{graph}}
            INSERT DATA {
                {{}}
            }
            """, triples)

    logger.info("Finished logging stats (container %s is stopped)", container[:12])


@register_event
async def store_events(event: ContainerEvent, sparql: SPARQLClient):
    container = (await event.container) if event.status == "start" else None
    e2rdf = Event2RDF()
    e2rdf.add_event_to_graph(event.data, container=container)
    ntriples = e2rdf.serialize().decode("utf-8")
    await sparql.update("""
        WITH <%(graph)s>
        INSERT DATA {
            %(ntriples)s
        }
        """ % {
            "graph": graph,
            "ntriples": ntriples,
        })


@register_event
async def start_logging_container(event: ContainerEvent, sparql: SPARQLClient):
    if not event.status == "start":
        return
    if not event.attributes.get('LOG'):
        return
    container = await event.container
    if container['Config']['Tty']:
        return
    container_concept = await create_container_log_concept(sparql, container)
    asyncio.ensure_future(save_container_logs(event.client, event.id, event.time, sparql, container_concept))
    logger.info("Logging container %s into %s", container['Id'][:12], container_concept)


@register_event
async def start_logging_container_stats(event: ContainerEvent, sparql: SPARQLClient):
    if not event.status == "start":
        return
    if not event.attributes.get('STATS'):
        return
    container = await event.container
    asyncio.ensure_future(save_container_stats(event.client, event.id, event.time, sparql))
    logger.info("Logging container %s", container['Id'][:12])


@on_startup
async def start_logging_existing_containers(docker: APIClient, sparql: SPARQLClient):
    now = datetime.utcnow()
    containers = await docker.containers()
    for container in containers:
        container = await docker.inspect_container(container['Id'])
        if not container['Config']['Labels'].get('LOG'):
            continue
        if container['Config']['Tty']:
            continue
        container_concept = await create_container_log_concept(sparql, container)
        asyncio.ensure_future(save_container_logs(docker, container['Id'], now, sparql, container_concept))
        logger.info("Logging container %s into %s", container['Id'][:12], container_concept)


@on_startup
async def start_logging_existing_containers_stats(docker: APIClient, sparql: SPARQLClient):
    now = datetime.utcnow()
    containers = await docker.containers()
    for container in containers:
        container = await docker.inspect_container(container['Id'])
        if not container['Config']['Labels'].get('STATS'):
            continue
        asyncio.ensure_future(save_container_stats(docker, container['Id'], now, sparql))
        logger.info("Logging container %s", container['Id'][:12])
