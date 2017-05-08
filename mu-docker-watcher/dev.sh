#!/bin/bash

docker run --rm -it \
           -v "$PWD":/app \
           -v "$PWD/containers_test":/app/containers \
           -v "$PWD"/pcap:/app/pcap \
	         -v "$PWD"/supervisord.conf:/etc/supervisord.conf \
           --network host \
           --name mu-docker-watcher \
           -e MODE=development \
           mu-docker-watcher
