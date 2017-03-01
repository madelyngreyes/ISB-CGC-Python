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

def getGenomicLocation(gene,verbose):
	#Useful links for queries:
	#https://cloud.google.com/bigquery/docs/reference/standard-sql/migrating-from-legacy-sql#escaping_reserved_keywords_and_invalid_identifiers
	#https://media.readthedocs.org/pdf/google-cloud-python/latest/google-cloud-python.pdf   Search on ScalarQueryParameter to get syntax
	bq = bigquery.Client()
	query = "SELECT seq_name, start, `end` FROM `isb-cgc.genome_reference.GENCODE_v24` WHERE feature = 'gene' AND gene_Status = 'KNOWN' AND gene_name = @gene;"

	query_parameters = (
		bigquery.ScalarQueryParameter('gene', 'STRING', gene)
	)

	query_results = bq.run_sync_query(query,query_parameters = [query_parameters])

	query_results.use_legacy_sql = False
	query_results.run()

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

	if genecount is not None:
		#query = "SELECT gene_name FROM @table LIMIT @genecount"
		query = "SELECT gene_name FROM `cgc-05-0016.other.tdp_hg38_genex_cnv` LIMIT 10"
		query_parameters = (
			bigquery.ScalarQueryParameter('table', 'STRING', table),
			bigquery.ScalarQueryParameter('genecount', 'INTEGER', genecount)
		)
	bq = bigquery.Client()
	#query_results = bq.run_sync_query(query,query_parameters = [query_parameters])
	query_results = bq.run_sync_query(query)
	query_results.use_legacy_sql = False
	query_results.run()

	page_token = None
	while True:
		rows, total_rows, page_token = query_results.fetch_data(page_token=page_token)
		return rows
		if not page_token:
			break

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
