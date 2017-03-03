#!/usr/bin/python

import argparse
import datetime
import time
import os
import sys
import pprint
import requests
import json
from google.cloud import bigquery
import httplib2
import datetime
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DEFAULT_STORAGE_FILE = os.path.join(os.path.expanduser("~"), '.isb_credentials')
DEFAULT_PROJECT = 'cgc-05-0016'

def runSyncQuery(query, parameters, project):
	bq = bigquery.Client(project=project)
	if parameters is not None:
		query_results = bq.run_sync_query(query, query_parameters = [parameters])
	else:
		query_results = bq.run_sync_query(query)
	query_results.use_legacy_sql = False
	query_results.run()
	return query_results

def getSampleList(study):
	query = "SELECT SampleBarcode FROM `isb-cgc.tcga_cohorts.@study` LIMIT 10"
	query_parameters = (bigquery.ScalarQueryParameter('study', 'STRING', study))
	results = runSyncQuery(query, query_parameters)

def getGenomicLocation(gene,verbose):
	#Useful links for queries:
	#https://cloud.google.com/bigquery/docs/reference/standard-sql/migrating-from-legacy-sql#escaping_reserved_keywords_and_invalid_identifiers
	#https://media.readthedocs.org/pdf/google-cloud-python/latest/google-cloud-python.pdf   Search on ScalarQueryParameter to get syntax
	query = "SELECT seq_name, start, `end` FROM `isb-cgc.genome_reference.GENCODE_v24` WHERE feature = 'gene' AND gene_Status = 'KNOWN' AND gene_name = @gene;"
	query_parameters = (
		bigquery.ScalarQueryParameter('gene', 'STRING', gene)
	)
	query_results = runSyncQuery(query, query_parameters, DEFAULT_PROJECT)

	page_token = None
	while True:
		rows, total_rows, page_token = query_results.fetch_data(max_results=10, page_token=page_token)
		for row in rows:
			return row
		if not page_token:
			break

def getGeneList(table, genecount, verbose):
	#This may be a bit stupid, but this routine will return gene names from any table with the column "gene_name"
	query = "SELECT gene_name FROM @table"
	query_parameters = (bigquery.ScalarQueryParameter('table', 'STRING', table))
	vPrint(verbose, ("Table name is %s" % table))
	vPrint(verbose, ("Limit is %s" % str(genecount)))

	if genecount is not None:
		#query = "SELECT gene_name FROM @table LIMIT @genecount"
		query = "SELECT gene_name FROM @table LIMIT 10"
		query_parameters = (bigquery.ScalarQueryParameter('table', 'STRING', table))
		#query = "SELECT gene_name FROM `isb-cgc.other.tdp_hg38_genex_cnv` LIMIT @genecount"
		#query = "SELECT gene_name FROM other.tdp_hg38_genex_cnv LIMIT @genecount"
		#query_parameters = (bigquery.ScalarQueryParameter('genecount', 'INTEGER', genecount))
		#query_parameters = (
		#	bigquery.ScalarQueryParameter('table', 'STRING', table),
		#	bigquery.ScalarQueryParameter('genecount', 'INTEGER', genecount)
		#)
	query_results = runSyncQuery(query, query_parameters, DEFAULT_PROJECT)
	page_token = None
	while True:
		rows, total_rows, page_token = query_results.fetch_data(page_token=page_token)
		return rows
		if not page_token:
			break

def getFileLocations(barcode):
	api = 'isb_cgc_api'
	version = 'v2'
	site = "https://api-dot-isb-cgc.appspot.com"
	credentials = get_credentials(None)
	service = get_authorized_service(api,version,site,credentials,args.verbose)
	data = service.samples().cloud_storage_file_paths(sample_barcode=barcode).execute()
	pprint.pprint(data)

def get_authorized_service(api, version, site, credentials, verbose):
	discovery_url = '%s/_ah/api/discovery/v1/apis/%s/%s/rest' % (site, api, version)
	vprint(verbose, discovery_url)
	http = credentials.authorize(httplib2.Http())
	if credentials.access_token_expired or credentials.invalid:
		credentials.refresh(http)
	authorized_service = build(api, version, discoveryServiceUrl=discovery_url, http=http)
	return authorized_service

def get_credentials(credFile):
	oauth_flow_args = ['--noauth_local_webserver']
	if credFile is None:
		storage = Storage(DEFAULT_STORAGE_FILE)
	else:
		storage = Storage(credFile)

	credentials = storage.get()
	if not credentials or credentials.invalid:
		flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, EMAIL_SCOPE)
		flow.auth_uri = flow.auth_uri.rstrip('/') + '?approval_prompt=force'
		credentials = tools.run_flow(flow, storage, tools.argparser.parse_args(oauth_flow_args))
	return credentials

def vPrint(doit, message):
	if doit:
		pprint.pprint(message)

def main(args):

	#Basic info
	#projectID = 'isb-cgc'
	#datasetName = 'genome_reference'
	#tableName = 'GENCODE_v24'

	#If a gene file is given, use that, otherwise query the table
	if args.genefile is not None:
		vPrint(args.verbose, ("Opening %s" % args.genefile))
		genelist = open(args.genefile,"r")
	elif args.tablename is not None:
		vPrint(args.verbose, ("Querying %s for genes" % args.tablename))
		genelist = getGeneList(args.tablename, 10, args.verbose)
	else:
		print "No gene file or table provided, exiting"
		sys.exit()
	#Get the patient list
	if args.studyname is not None:
		sampleList = getSamples(args.studyname)

	for gene in genelist:
		if args.genefile is not None:
			gene = gene.rstrip()
		vPrint(args.verbose, ("Requesting query for gene %s" % gene))
		(chromosome,start, end)  = getGenomicLocation(gene,args.verbose)
		print "%s\t%s\t%s\t%s" % (gene, chromosome, start,end)
	#Get the chromosomal location of the gene
	#Slice each of the genes from the list of bamfiles
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback.')
	parser.add_argument("-g", "--genefile", nargs = '?', const = None, help = "File containing genes to slice")
	parser.add_argument("-t", "--tablename", nargs = '?', const = None, help = "Table containing gene names")
	parser.add_argument("-s", "--studyname", help = "Name of the study to bam slice")
	#parser.add_argument("-b", "--bamfile", required = True, hep = "File containing bam files to be sliced")

	args = parser.parse_args()
	main(args)
