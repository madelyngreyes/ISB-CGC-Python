#!/bin/bash
#####################################################
#                                                   #
# Requires Google Cloud SDK and jq to be installed  #
# jq: https://stedolan.github.io/jq/                #
# SDK: https://cloud.google.com/sdk/downloads       #
#                                                   #
#####################################################

usage() { echo "Usage: $0 [-v <VM name>] [-u <username>] [-p <port number> Default is 3306] [-n No tunnel]" 1>&2; exit 1; }

VMNAME="DEFAULT VM NAME HERE"
USER="DEFAULT USER NAME HERE"
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

INSTANCES=$(gcloud compute instances list --format=json | jq '.[] | .name,.networkInterfaces[].accessConfigs[].natIP')
IFS='"' read -ra ARRAY <<< ${INSTANCES}

for ((i=0; i<${#ARRAY[*]};i++)); do
	if [[ "${ARRAY[i]}" == "${VMNAME}" ]]; then
		IP="${ARRAY[$((i+2))]}"
	fi
done


if [[ "${TUNNEL}" -eq "True" ]] ; then
	ssh ${USER}@${IP} -L ${PORT}:localhost:${PORT}
else
	ssh ${USER}@${IP}
fi
