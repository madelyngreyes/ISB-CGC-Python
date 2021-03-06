#!/bin/bash

usage() { echo "Usage: $0 [-b <bam file>] [-o <output bam file>] [-r <chr#:start-stop>" 1>&2; exit 1; }

while getopts "b:r:o:" args; do
  case "${args}" in
    b)
      BAMFILE=${OPTARG}
      ;;
    r)
      RANGE=${OPTARG}
      ;;
    o)
      OUTPUTFILE=${OPTARG}
      ;;
    *)
      usage
      ;;
  esac
done
if [ -z "${BAMFILE}" ] || [ -z "${RANGE}" ] || [ -z "${OUTPUTFILE}" ]; then
  usage
fi

#export the oauth token
export GCS_OAUTH_TOKEN=`gcloud auth application-default print-access-token`
#Do the slice
echo "samtools view -b $BAMFILE -o $OUTPUTFILE $RANGE"
samtools view -b $BAMFILE -o $OUTPUTFILE $RANGE
