#!/bin/bash
#####################################################
#                                                   #
# Requires Google Cloud SDK and jq to be installed  #
# jq: https://stedolan.github.io/jq/                #
# SDK: https://cloud.google.com/sdk/downloads       #
#                                                   #
#####################################################

usage() { echo "Usage: $0 [-v <VM name>] [-u <username>] [-p <port number> Default is 3306] [-n No tunnel]" 1>&2; exit 1; }

VMNAME="tdp-pi"
USER="todd_pihl"
PORT=3306
TUNNEL="True"

while getopts "v:u:p:n" args; do
	case "${args}" in
		v)
			VMNAME=${OPTARG}
			;;
		u)
			USER=${OPTARG}
			;;
		p)
			PORT=${OPTARG}
			;;
		n)
			TUNNEL="False"
			;;
		*)
			usage
			;;
	esac
done

echo "VMNAME: ${VMNAME}  USER: ${USER}  PORT: ${PORT}  TUNNEL: ${TUNNEL}"

INSTANCES=($(gcloud compute instances list --format=json | jq -r '.[] | .name,.networkInterfaces[].accessConfigs[].natIP|tostring'))

for ((i=0; i<${#INSTANCES[*]};i++)); do
	if [[ "${INSTANCES[i]}" == "${VMNAME}" ]]; then
		IP="${INSTANCES[$((i+1))]}"
	fi
done

echo "User: ${USER}  IP: ${IP}"

if [ "${TUNNEL}" == "True" ] ; then
	echo "ssh ${USER}@${IP} -L ${PORT}:localhost:${PORT}"
	ssh ${USER}@${IP} -L ${PORT}:localhost:${PORT}
else
	echo "ssh ${USER}@${IP}"
	ssh ${USER}@${IP}
fi
