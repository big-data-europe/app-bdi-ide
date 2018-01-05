#!/bin/bash

echo "Installing the BDE Big Data Integrator"
echo "..."

# Increasing the max mnap count
echo "Increasing the max mnap count"
sysctl -w vm.max_map_count=262144

# Setting the path of the current path in the docker-compose
# environment variable of the swarm admin
echo "Setting current path in swarm-admin configuration..."
current_directory=`pwd`
current_directory_no_spaces="${current_directory//\ /\\\\\\\ }"

sed -i -e "s|UNESCAPED_PWD|$current_directory|g" docker-compose.yml
sed -i -e "s|PWD|\"$current_directory_no_spaces\"|g" docker-compose.yml

# creating data/swarm-admin to prevent the app to crash.
echo "Manually creating data/swarm-admin to prevent the app to crash."
mkdir -p data/swarm-admin

# Setting the hostnames
echo "Configuring your localhost"
./scripts/edit-hosts.sh

# All done!
echo "..."
echo "Your BDE Big Data Integrator has been successfully configured!"
echo "Surf to http://integrator-ui.big-data-europe.aksw.org"

