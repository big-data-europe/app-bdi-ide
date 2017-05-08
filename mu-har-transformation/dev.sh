#!/bin/bash

docker run --rm -it \
           -v "$PWD"/src:/app/src/ \
           -v "$PWD"/pcap:/app/pcap \
           -v "$PWD"/har:/app/har \
           -v "$PWD"/docker-compose.yml:/app/docker-compose.yml \
           --name mu-har-transformation \
           mu-har-transformation
