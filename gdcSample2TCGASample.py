#! /usr/bin/python

# Problem:  GDC sample barcodes don't contain the vial indicator which means taking a smple barcode directly from GDC and trying to use
# it in ISB-CGC is difficult/impossible.

import pihlStuff as pihl
import argparse
import datetime
import json
from googleapiclient.errors import HttpError

def casesGet(service, barcode):
	try:
		data = service.cases().get(case_barcode = barcode).execute()
		return data
	except HttpError as exception:
		raise exception

def cohortsPreview(service, body):
	try:
		data = service.cohorts().preview(**body).execute()
		return data
	except HttpError as exception:
		raise exception
		
def cohortsCreate(service, name, body):
	try:
		data = service.cohorts().create(name=name, body=body).execute()
		return data
	except HttpError as exception:
		raise exception

def main(args):
	#Main variables
	version = "v3"
	program_api = pihl.getProgram(args.program)
	site = pihl.getSite(args.tier)
	isbsample_list = []
	
	
	#Set up credentials
	credentials = pihl.get_credentials(args.credentialsfile, args.tier, args.verbose)
	pihl.vPrint(args.verbose,credentials)
	
	#Get an authorized service
	program_auth_service = pihl.get_authorized_service(program_api, version, site, credentials, args.verbose)
	
	#Open the GDC barcode file and loop through
	with open(args.inputfile, 'r') as gdcsamples:
		for gdcsample in gdcsamples:
			gdcsample = gdcsample.rstrip()
			case = gdcsample[:-3]
			pihl.vPrint(args.verbose, case)
			data = casesGet(program_auth_service, case)
			for isbsample in data['samples']:
				isbsample = isbsample.encode("UTF-8")
				if gdcsample in isbsample:
					isbsample_list.append(isbsample)
	isbsample_list = set(isbsample_list)
	isbsample_list = list(isbsample_list)
	pihl.vPrint(args.verbose, isbsample_list)
	
	#Create a cohort if requested
	if args.makecohort:
		now = datetime.datetime.now()
		cohortname = "%s_%s_%s_GDC_Sample_Cohort" % ( now.month, now.day, now.year)
		query = {"sample_barcode" : isbsample_list}
		try:
			#data = cohortsPreview(program_auth_service, query)
			data = cohortsCreate(program_auth_service, cohortname, query)
			pihl.vPrint(args.verbose, data)
		except HttpError as exception:
			pihl.vPrint(args.verbose, exception)
		

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback. Does not affect logging')
	tierchoice = ["mvm", "dev", "test", "prod"]
	parser.add_argument("-t", "--tier", required = True, type = str.lower, choices = tierchoice, help = "Tier that the tests will be run on")
	programchoice = ["TCGA", "TARGET", "CCLE"]
	parser.add_argument("-p", "--program", required = True, type = str.upper, choices = programchoice, help = "Program  (TCGA, TARGET, CCLE) that the tests will be run on")
	parser.add_argument("-c", "--credentialsfile", nargs = '?', const = None , help="File to use for credentials, will default to ~/.isb_credentials if left blank")
	parser.add_argument("-i", "--inputfile", required = True, help = "File of GDC sample barcodes, one per line")
	parser.add_argument("-m", "--makecohort", action = "store_true", help = "Create a cohort from the converted barcodes")
	args = parser.parse_args()
	
	main(args)
