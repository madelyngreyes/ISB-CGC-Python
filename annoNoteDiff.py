#!/usr/bin/python

import argparse
import pprint
import difflib
from google.cloud import bigquery

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

def getNotes(verbose, filehandle):
	vPrint(verbose, "In getNotes")
	query = "SELECT annotationNoteText, notes FROM `tdp_annotation.NoteDifferences`"
	vPrint(verbose, ("Calling runSyncQuery with query:\n%s" % query))
	results = runSyncQuery(query, None, DEFAULT_PROJECT)

	page_token = None
	#differ =difflib.Differ()
	while True:
		rows, total_rows, page_token = results.fetch_data(max_results=10, page_token=page_token)
		for (old,new) in rows:
			#diff = list(differ.compare(old, new))
			diff = difflib.unified_diff(old,new)
			#pprint.pprint(''.join(diff))
			pprint.pprint(''.join(diff), filehandle)

def vPrint(doit, message):
	if doit:
		pprint.pprint(message)
def main(args):
	vPrint(args.verbose, "Calling getNotes")
	output = open(args.outputfile, "w")
	getNotes(args.verbose, output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback.')
	parser.add_argument("-o", "--outputfile", required = True, help = "File to store results")
	args = parser.parse_args()

	main(args)
