#!/bin/bash

echo "installing the BDE Big Data Integrator"

# Setting the path of the current path in the docker-compose
# environment variable of the swarm admin
echo "setting current path in swarm-admin configuration..."
current_directory=`pwd`
current_directory_no_spaces="${current_directory//\ /\\\\\\\ }"

sed -i -e "s|UNESCAPED_PWD|$current_directory|g" docker-compose.yml
sed -i -e "s|PWD|\"$current_directory_no_spaces\"|g" docker-compose.yml

# creating data/swarm-admin to prevent the app to crash.
echo "Manually creating data/swarm-admin to prevent the app to crash."
mkdir -p data/swarm-admin

# Setting the hostnames
echo "configuring your localhost"
./scripts/edit-hosts.sh

# All done!
echo "Your BDE Big Data Integrator has been successfully configured!"
echo "Surf to http://integrator-ui.big-data-europe.aksw.org"

