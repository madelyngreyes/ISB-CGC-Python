#!/bin/bash

usage() { echo "Usage: $0 [-v <VM name>] [-u <username>]" 1>&2; exit 1; }

VMNAME="<DEFAULT VM NAME HERE"
USER="DEFAULT USER NAME HERE"

while getopts "v:u:" args; do
	case "${args}" in
		v)
			VMNAME=${OPTARG}
			;;
		u)
			USER=${OPTARG}
			;;
		*)
			usage
			;;
	esac
done
	  
COUNT=0
INSTANCES=$(gcloud compute instances list --format=json | jq '.[] | {name: .name, ip: .networkInterfaces[].accessConfigs[].natIP'})
IFS='"' read -ra ARRAY <<< ${INSTANCES}
for i in "${ARRAY[@]}"; do
	if [[ "${i}" == "${VMNAME}" ]]; then
		((COUNT+=4))
		IP="${ARRAY[$COUNT]}"
	fi
	((COUNT+=1))
done

ssh ${USER}@${IP} -L 3306:localhost:3306
