#!/usr/bin/python
import pihlStuff as pihl
import argparse
import httplib2
import datetime
import os
import json
from googleapiclient.errors import HttpError

def logTest(filehandle, tier, testname, result):
	now = datetime.datetime.now()
	timestamp = "%s-%s-%s_%s:%s:%s" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
	filehandle.write(("%s\t%s\t%s\t%s\n") % (timestamp, tier, testname, result))

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

def barcodeProcess(barcodefile, barcodetype):
	barcodelist = []
	with open(barcodefile,"r") as barcodes:
		for barcode in barcodes:
			if barcodetype == "case_barcode":
				barcode = barcode[:12]
			elif barcodetype == "sample_barcode":
				barcode = barcode[:16]
			else:
				print "Big honking bug"
			barcodelist.append(barcode)
	return barcodelist
	
				
	
def main(args):
	
	#Create the log file
	now = datetime.datetime.now()
	filename = "%s_%s_%s_CohortCreationLog.tsv" % (now.month, now.day, now.year)
	log_header = "Timestamp\tTest Tier\tTest Name\tResult Count\n"
	
	if os.path.isfile(filename):
		logfile = open(filename, "a")
	else:
		logfile = open(filename,"w")
	logfile.write(log_header)
	
	#Set up main variables
	version = "v3"
	api = pihl.getProgram(args.program)
	site = pihl.getSite(args.tier)

	#Get credentials
	pihl.vPrint(args.verbose, ("Using credentials %s" % str(args.credentialsfile)))
	credentials = pihl.get_credentials(args.credentialsfile, args.tier, args.verbose)
	pihl.vPrint(args.verbose,credentials)
	
	#create Authorized Service
	auth_service = pihl.get_authorized_service(api, version, site, credentials, args.verbose)
	
	#Create the barcode array
	if args.sample:
		barcodetype = "sample_barcode"
	elif args.patient:
		barcodetype = "case_barcode"
	else:
		print("No barcode type selection found, must use either -b or -p")
		sys.exit(0)
	barcodelist = barcodeProcess(args.barcodefile, barcodetype)
	request = {barcodetype:barcodelist}

		
		
	#test cohorts().create()
	if args.createcohort:
		pihl.vPrint(args.verbose, "cohorts().create() test")
		try:
			data = cohortsCreate(auth_service,args.cohortname, request)
			testing_cohort_id = data['id']  #will be used to delete in the next test
			logTest(logfile,args.tier,"Cohorts Create Test", testing_cohort_id)
		except HttpError as exception:
			logTest(logfile, args.tier, "Cohorts Create ERROR", exception)
	else:
		#test cohorts().preview()
		pihl.vPrint(args.verbose, "cohorts().preview() test")
		try:
			data = cohortsPreview(auth_service, request)
			logTest(logfile, args.tier, "Cohorts Preview Test", data['patient_count'])
		except HttpError as exception:
			logTest(logfile, args.tier, "Cohorts Preview ERROR", exception)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback. Does not affect logging')
	tierchoice = ["mvm", "dev", "test", "prod"]
	parser.add_argument("-t", "--tier", required = True, type = str.lower, choices = tierchoice, help = "Tier that the tests will be run on")
	parser.add_argument("-c", "--credentialsfile", nargs = '?', const = None , help="File to use for credentials, will default to ~/.isb_credentials if left blank")
	parser.add_argument("-b", "--barcodefile", required = True, help = "File containing barcodes for processing")
	parser.add_argument("-s", "--sample", action="store_true", help = "Create cohort using sample barcodes")
	parser.add_argument("-p", "--patient", action = "store_true", help = "Create cohort using patient barcodes")
	parser.add_argument("-z", "--createcohort", action = "store_true", help = "Actually create the cohort, not just preview")
	parser.add_argument("-n", "--cohortname", required = True, help = "Name to give the cohort")
	programchoice = ["TCGA", "TARGET", "CCLE"]
	parser.add_argument("-g", "--program", required = True, type = str.upper, choices = programchoice, help = "Program  (TCGA, TARGET, CCLE) that the tests will be run on")
	args = parser.parse_args()

	main(args)
