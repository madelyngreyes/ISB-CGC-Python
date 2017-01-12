#!/usr/bin/python
#Parse the CPTAC files into a tab delimited form suitable for loading BigQuery

import argparse
import pandas as pd
import os

#BQ Connections
from google.cloud import bigquery
import json


DEFAULT_STORAGE_FILE = os.path.join(os.path.expanduser("~"), '.isb_credentials')
##########################################
#
#   Parsing iTRAQ file stuff
##########################################
def getFileType(filename):
	fileType = "NA"
	allowedFileType = {"itraq.tsv":"itraq", "peptides.tsv":"peptides", "summary.tsv":"summary"}
	for fType in allowedFileType:
		if fType in filename:
			fileType = allowedFileType[fType] 
	return fileType
	
def getExperimentType(filename):
	experimentType = "NA"
	allowedExperimentType = ("Phosphoproteome", "Proteome", "Glycoproteome")
	for expType in allowedExperimentType:
		if expType in filename:
			experimentType = expType
	return experimentType 
	
def getVersion(filename):
	version = "r1"
	allowedVersions = ("r2", "r3")
	for aVersion in allowedVersions:
		if aVersion in filename:
			version = aVersion
	return version

def getStudy(filename):
	#If COAD, probably need to do a barcode check to see if COAD or READ
	study = "NA"
	allowedStudy = {"Breast": "TCGA-BRCA", "Colon": "TCGA-COAD", "Ovarian": "TCGA-OV"}
	for aStudy in allowedStudy:
		if aStudy in filename:
			study = allowedStudy[aStudy]
	return study
	
def getHeaders(filename):
	headers = []
	f = open(filename,"r")
	firstline = f.readline()
	firstline.strip()
	headers = firstline.split("\t")
	f.close
	return headers
	
def getGenes(filename):
	data = pd.read_csv(filename, sep = '\t', skiprows = (0,1,2))
	genes = data.iloc[:,0]
	return genes
	
def getColumnData(filename, index):
	data = pd.read_csv(filename, sep = '\t')
	noNaN = data.where((pd.notnull(data)), None)
	#columndata = data.loc[:,index]
	columndata = noNaN.loc[:,index]
	return columndata
	
def getSampleBarcode(shared,unshared):
	barcode = "Mismatch"
	temp1 = shared.split()
	temp2 = unshared.split()
	if temp1[0] == temp2[0]:
		barcode = "TGGA-" + temp1[0]
	return barcode

def buildRow(counter,headerlist,fileType,expType,version,study,headers,numColumns,genes,description,organism,chromosome,locus):
	print "Genes is %s" % str(len(genes))
	#Get the column header
	loglabel = headers[counter].rstrip()

	#If the header isn't in the list we want to use, we want to ignore it.
	if loglabel not in headerlist:
		
		#iTRAQ files have paired columns (shared and unshared), so increment i to get the next column
		counter +=1
		unsharedlabel = headers[counter].rstrip()
		vPrint(args.verbose,("Shared:\t%s\tUnshared:\t%s" % (loglabel, unsharedlabel)))
			
		#Check that the paired columns have the same sample barcode and reformat to TCGA style
		sample = getSampleBarcode(loglabel, unsharedlabel)
		
		#Proceed if the barcodes from the column pairs match.  Bail if they don't
		if sample != 'Mismatch':
			
			#Get the data from the paired columns.  Each column has its own list
			logratio = getColumnData(args.cptacfile,loglabel)
			unsharedlog = getColumnData(args.cptacfile,unsharedlabel)
			vPrint(args.verbose,("Shared Size:\t%s\tUnshared Size:\t%s" % (str(len(logratio)), str(len(unsharedlog)))))
				
			#Now to start the printing
			rows = []
			genecount = 0
			while genecount < len(genes):
				row = []
				samplecount = 0
				row.append(sample)
				row.append(study)
				row.append(version)
					
				# The mean, median and std dev are the first three values in the lists and are constant for the entire sample.  Hardcode these.
				row.append(logratio[0]) #mean shared
				row.append(unsharedlog[0]) #mean unshared
				row.append(logratio[1]) #median shared
				row.append(unsharedlog[1]) #median unshared
				row.append(logratio[2]) #std dev shared
				row.append(unsharedlog[2]) #std dev unshared
				
				#The gene name and related data need to be incremented 
				row.append(genes[genecount]) #Gene name
				row.append(logratio[genecount + 3]) #shared gene value
				row.append(unsharedlog[genecount + 3]) #unshared gene value
				row.append(description[genecount + 3])
				row.append(organism[genecount + 3])
				row.append(chromosome[genecount + 3])
				row.append(locus[genecount+3])
					
				#Store the row and move to  the next gene
				rows.append(row)
				genecount += 1
				

	return rows

def createTable(dataset,name):
        table = dataset.table(name)
        table.schema = (
                bigquery.SchemaField('SampleBarcode', 'STRING'),
                bigquery.SchemaField('Study', 'STRING'),
                bigquery.SchemaField('ReportRevision', 'STRING'),
                bigquery.SchemaField('MeanLogRatio', 'FLOAT'),
                bigquery.SchemaField('MeanUnsharedLogRatio', 'FLOAT'),
                bigquery.SchemaField('MedianLogRatio', 'FLOAT'),
                bigquery.SchemaField('MedianUnsharedLogRatio', 'FLOAT'),
                bigquery.SchemaField('StandardDeviationLogRatio', 'FLOAT'),
                bigquery.SchemaField('StandardDeviationUnsharedLogRatio', 'FLOAT'),
                bigquery.SchemaField('Gene', 'STRING'),
                bigquery.SchemaField('GeneLogRatio', 'FLOAT'),
                bigquery.SchemaField('GeneUnsharedLogRatio', 'FLOAT'),
                bigquery.SchemaField('Description', 'STRING'),
                bigquery.SchemaField('Organism', 'STRING'),
                bigquery.SchemaField('Chromosome', 'STRING'),
                bigquery.SchemaField('Locus', 'STRING')
        )
        table.create()
	return table

def formatData(rowdata):
	#https://www.oreilly.com/learning/handling-missing-data
	
	row_data = {
		"SampleBarcode" : rowdata[0],
		"Study" : rowdata[1],
		"Report Revision" : rowdata[2],
		"MeanLogRatio" : rowdata[3],
		"MeanUnsharedLogRatio" : rowdata[4],
		"MedianLogRatio" : rowdata[5],
		"MedianUnsharedLogRatio" : rowdata[6],
		"StandardDeviationLogRatio" : rowdata[7],
		"StandardDeviationUnsharedLogRatio" : rowdata[8],
		"Gene" : rowdata[9],
		"GeneLogRatio" : rowdata[10],
		"GeneUnsharedLogRatio" : rowdata[11],
		"Description" : rowdata[12],
		"Organism" : rowdata[13],
		"Chromosome" : rowdata[14],
		"Locus" : rowdata[15]
	}

	json_data = {
		"kind" : "bigquery$tableDataInsertAllRequest",
		"rows" : [
			{"json" : row_data}
		]
	}
	
	#data = json.loads(str(json_data))
	data = json.dumps(row_data)
	return data

def insertData(table,data):
	# https://googlecloudplatform.github.io/google-cloud-python/stable/bigquery-usage.html
	table.reload()
	rows = [data]
	errors = table.insert_data(rows)

	return errors

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

def get_authorized_service(credentials):
	http = credentials.authorize(httplib2.Http())
	if credentials.access_token_expired or credentials.invalid:
		credentials.refresh(http)
	authorized_service = discovery.build('bigquery', 'v2', http=http)
	return authorized_service
	
def vPrint(doit, message):
	if doit:
		print message
	
def main(args):
	# User Set variables
        project_id = "isb-cgc"
        datasetname = "test"  
        #tablename = "tdp_itraq_test

	#Test to see that we have either an output file or a Bigquery Table
	if args.outputfile is not None:
		vPrint(args.verbose, "Opening output file")
		outfile = open(args.outputfile,"w")
	elif args.bigquery is not None:
		vPrint(args.verbose, "Writing to BigQuery")

		#Test to see if table exists and created it if it doesn't
		bq = bigquery.Client(project=project_id)
		dataset = bq.dataset(datasetname)
		table = dataset.table(args.bigquery)
		if table.exists():
	                vPrint(args.verbose, ("%s exists" % args.bigquery))
        	else:   
                	vPrint(args.verbose, ("%s does not exist, creating new table" % args.bigquery))
	                table = createTable(data,args.tablename)
	else:
		print "No output option selected, ending program"
		sys.exit()


	#Start buidling the various components
	# fileType, expType, version, numColumns and study are individual values
	# headers, genes, description, organism, chromosome, locus are lists of COLUMN values taken from 
	# a pandas array

	fileType = getFileType(args.cptacfile)
	expType = getExperimentType(args.cptacfile)
	version = getVersion(args.cptacfile)
	study = getStudy(args.cptacfile)
	headers = getHeaders(args.cptacfile)
	numColumns = len(headers)
	genes = getGenes(args.cptacfile)
	description = getColumnData(args.cptacfile, 'Description')
	organism = getColumnData(args.cptacfile, 'Organism')
	chromosome = getColumnData(args.cptacfile, 'Chromosome')
	locus = getColumnData(args.cptacfile, 'Locus')
	
	headerlist = ["SampleBarcode","Study","ReportRevision","MeanLogRatio","MeanUnsharedLogRatio","MedianLogRatio","MedianUnsharedLogRatio",
	"StandardDeviationLogRatio","StandardDeviationUnsharedLogRatio","Gene","GeneLogRatio","GeneUnsharedLogRatio","Description","Organism",
	"Chromosome","Locus"]
	
	
	#Print a header only if output file and verbose are specified
	if args.outputfile is not None:
		if args.verbose:
			line = '\t'.join(headerlist)
			outfile.write(line + "\n")
		
	# i will track which column of the itraq speadsheet is being processed.  Skip the first (index 0) because it is gene names only
	# i will increment after each sample pair
	i=1
	#while i < numColumns:
	while i <= 3:
		#Build the row to print
		rows = buildRow(i,headerlist,fileType,expType,version,study,headers,numColumns,genes,description,organism,chromosome,locus)
		
		#Print to the output file if it was specified
		if args.outputfile is not None:
			for row in rows:
				line = '\t'.join(str(item) for item in row)
				outfile.write(line + "\n")

		#Append to the BigQuery table if specified
		if args.bigquery is not None:
			for row in rows:
				insertdata = formatData(row)
				response = insertData(table,row)
				if response:
					vPrint(args.verbose,response)
		#Increment to the next sample pair
		i+=2
	
	if outfile is not None:
		outfile.close()
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Parser for cptac2BQ program")
	parser.add_argument("-v", "--verbose", action = "store_true")
	parser.add_argument("-c", "--cptacfile", required = True, help = "Name of the file from CPTAC")
	parser.add_argument("-o", "--outputfile", help = "Name of the output file")
	parser.add_argument("-b", "--bigquery", help = "Write to Biquery table instead of output file");
	
	args = parser.parse_args()
	
	main(args)
