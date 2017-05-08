#!/usr/bin/env bash

containers=()

# Check if ENV variables are set and if not assign them a default value.
env_pcap_dir=$(printenv PCAP_WRITE_DIR)
pcap_write_dir=${env_pcap_dir:-"pcap/"}

env_sleep_period=$(printenv SLEEP_PERIOD)
sleep_period=${env_sleep_period:-"5"}

env_container_data_dir=$(printenv CONTAINER_DATA_DIR)
container_data_dir=${env_container_data_dir:-"containers/"}

env_container_data_file=$(printenv CONTAINER_DATA_FILE)
container_data_file=${env_container_data_filer:-"containers.json"}


#/ Usage:
#/ Description:
#/ Examples:
#/ Options:
#/   --help: Display this help message
usage() { grep '^#/' "$0" | cut -c4- ; exit 0 ; }
expr "$*" : ".*--help" > /dev/null && usage

# Convenience logging function.
info()    { echo "[INFO]    $@"  ; }

# Cleanup files after exiting the script.
cleanup() {
  echo "Cleanup logic here"
  exit 0
}


# Searches for a tuple in an array. There is a need to use then
# external containers array instead of passing it as a parameter because
# in bash arrays can't be passed as is, but the whole list of elements.
containsTuple() {
  local cont="$1"
  local iface="$2"

  # When array is empty.
  if [ ${#containers[@]} == 0 ]; then
    return 1
  fi
  for ((i=0; i<${#containers[@]}; i+=2)); do
    if [ $cont == "${containers[i]}" ] && [ $iface == "${containers[i+1]}" ]; then
      return 0
    fi
  done
  return 1
}


function analyzeTraffic {
  # container, interface, container_ip, network_name
  local cname="$1"
  local iface="$2"
  local cip="$3"
  local netname="$4"
  local bdir="$5"

  # Check if we are already observe that container
  containsTuple $cname $iface

  if [ $? != 0 ]; then
    info "Container ${cname} using network interface: ${iface} not being observed, adding it."
    containers+=($cname)
    containers+=($iface)

    mkdir -p $bdir$iface"/"$cname

    # Start capturing traffic in the given interface.
    # TODO: Change the PERIOD (-G) For an ENV VARIABLE
    # (-s 0) captures full packets. This is slower but there will be no incomplete packets.
    tcpdump -s 0 -i $iface -G 5 -w $bdir$iface"/"$cname"/"$cname"_"$iface"_%Y-%m-%d_%H:%M:%S.pcap" host $cip &

  fi
}



#####################
# Start of the script
#####################
if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
    trap cleanup EXIT TERM INT

    # Create directory to write generated pcaps.
    mkdir -p $pcap_write_dir

    while :
    do
      info "Iterate over each container of the file containers.json"

      # Get the length of the containers array
      container_count=$(cat $container_data_dir$container_data_file | jq '. | length')

      # Read the containers.json file
      # Parse the info: cname, interface, ip, network_name
      # Check if already observed
      # If not, drop tcpdump + add the container to be observed.
      for i in $(seq 0 $((container_count-1)))
      do
        cname=$(cat $container_data_dir$container_data_file | jq -r ".[${i}] .name")
        network_name=$(cat $container_data_dir$container_data_file | jq -r ".[${i}] .data .network_name")
        ip_address=$(cat $container_data_dir$container_data_file | jq -r ".[${i}] .data .ipAddress")
        interface_id=$(cat $container_data_dir$container_data_file | jq -r ".[${i}] .data .interface_id")

        # Find the host interface that connects to the network the docker is running in.
        for host_iface in `netstat -i | grep br | awk '{ print $1 }'`; do

          if [[ "$interface_id" == *$(echo $host_iface | awk -F'-' '{ print $2 }')* ]]; then
            analyzeTraffic $cname $host_iface $ip_address $network_name $pcap_write_dir
          elif [[ "$network_name" == "bridge" ]]; then
            analyzeTraffic $cname "docker0" $ip_address $network_name $pcap_write_dir
          fi
        done

      done

      info "Sleep for ${sleep_period} seconds."
      sleep $sleep_period
    done
fi
