# pcap-har-watcher
Watch a given folder for new pcap files and transform them into HAR files with a series of additional changes in order to enrich the files to be
afterwards fed into an ELK instance (Elasticsearch, Logstash, Kibana).
This pcap files are originally meant to come from observing docker containers run in a network, so additional information about them will be
included in pcap file naming scheme.

  * Decode the base64 strings into JSON objects.
  * Add additional container information into the HAR file to allow the tracing of http responses accross the docker network.

Once the PCAP files are converted into HAR format, they will be pushed into an ElasticSearch instance to visualize the data in Kibana.

## Usage

```sh
docker run --rm -it \
           -v "$PWD"/src:/app/src/ \
           -v "$PWD"/pcap:/app/pcap \
           -v "$PWD"/har:/app/har \
           -v "$PWD"/docker-compose.yml:/app/docker-compose.yml \
           --name mu-har-transformation \
           mu-har-transformation

```

* The **pcap/** folder contains the .pcap files generated previously by the **mu-docker-watcher** microservice.
* The **har/** folder contains the .har (JSON) files converted from the .pcap.
* The **docker-compose.yml** file contains information about the links that are between containers, and that information needs to be added to the .har files.


## Acknowledgments

This script uses the **pcap2har** script found [here](https://github.com/andrewf/pcap2har) slighly modified for it's purposes.

Copyright for the **pcap2har** project:

Copyright (c) 2009 Andrew Fleenor, Ryan C. Witt, Jake Holland, and Google, Inc.
All rights reserved.
