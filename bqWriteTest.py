#!/usr/bin/python

import argparse
import json
from pprint import pprint
from google.cloud import bigquery as bq


def stream_data(project_id,dataset_name, table_name, json_data_file):
	bqClient = bq.Client(project=project_id)
	dataset = bqClient.dataset(dataset_name)
	table = dataset.table(table_name)
	
	print "loading JSON file"
	with open(json_data_file) as json_data:
		data = json.load(json_data)
	#get table schema
	print "Getting table schema"
	table.reload()
	
	print "Preparing data"
	rows = [data]
	print "Inserting data"
	errors = table.insert_data(rows)

	if not errors:
		print('Loaded 1 row into {}:{}'.format(dataset_name,table_name))
	else:
		print "Errors:"
		pprint(errors)

def checkTable(project_id, dataset_name, table_name):
	bqclient = bq.Client(project=project_id)
	dataset = bqclient.dataset(dataset_name)
	table = dataset.table(table_name)

	if table.exists():
		print "Table %s exists in Dataset %s and Project %s" % (table_name, dataset_name, project_id)
	else:
		print "Creating table %s" % table_name
		table.schema = (
			bq.SchemaField('SampleBarcode', 'STRING'),
			bq.SchemaField('SampleSource', 'STRING'),
			bq.SchemaField('SampleID', 'STRING')
		)

		table.create()

def main(args):

	json_data = {
		'SampleBarcode' : 'TCGA-AA-1234-56-0192A',
        	'SampleSource' : 'Univeristy of Southern North Dakota at Hoople',
        	'SampleID' : 1.0
	}
	print "Checking on table"
	checkTable(args.project, args.dataset, args.table)
	print "Streaming data to table"
	stream_data(args.project, args.dataset, args.table, args.jsonfile)

	
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-p", "--project", nargs = '?', const = 'isb-cgc', help = "Project ID")
	parser.add_argument("-d", "--dataset", nargs = '?', const = 'temp', help = "Dataset name")
	parser.add_argument("-t", "--table", nargs = '?', const = 'tdp_testing_table', help = "Table name")
	parser.add_argument("-j", "--jsonfile", required = True, help = "Data file in JSON format")
	args = parser.parse_args()
	main(args)
