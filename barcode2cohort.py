#!/usr/bin/python
import pihlStuff.py as pihl
import argparse
#import os
#import pprint
import httplib2
import datetime
import json
#from oauth2client.client import OAuth2WebServerFlow
#from oauth2client import tools
#from oauth2client.file import Storage
#from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# the CLIENT_ID for the ISB-CGC site
#CLIENT_ID = '907668440978-0ol0griu70qkeb6k3gnn2vipfa5mgl60.apps.googleusercontent.com'
# The google-specified 'installed application' OAuth pattern
#CLIENT_SECRET = 'To_WJH7-1V-TofhNGcEqmEYi'
# The google defined scope for authorization
#EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
# where a default credentials file will be stored for use by the endpoints
#DEFAULT_STORAGE_FILE = os.path.join(os.path.expanduser("~"), '.isb_credentials')


#def get_credentials(credFile):
#	oauth_flow_args = ['--noauth_local_webserver']
#	if credFile is None:
#		storage = Storage(DEFAULT_STORAGE_FILE)
#	else:
#		storage = Storage(credFile)
#		
#	credentials = storage.get()
#	if not credentials or credentials.invalid:
#		flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, EMAIL_SCOPE)
#		flow.auth_uri = flow.auth_uri.rstrip('/') + '?approval_prompt=force'
#		credentials = tools.run_flow(flow, storage, tools.argparser.parse_args(oauth_flow_args))
#	return credentials
   

#def get_authorized_service(api, version, site, credentials, verbose):
#    discovery_url = '%s/_ah/api/discovery/v1/apis/%s/%s/rest' % (site, api, version)
#   if verbose:
#		print discovery_url
#    http = credentials.authorize(httplib2.Http())
#    if credentials.access_token_expired or credentials.invalid:
#        credentials.refresh(http)
#    authorized_service = build(api, version, discoveryServiceUrl=discovery_url, http=http)
#    return authorized_service

#def getSite(tier):
#	sites = {"mvm" : "https://api-dot-mvm-dot-isb-cgc.appspot.com",
#			"dev" : "https://api-dot-mvm-dot-isb-cgc.appspot.com",
#			"test" : "https://api-dot-isb-cgc-test.appspot.com",
#			"prod" : "https://api-dot-isb-cgc.appspot.com" }
#	return sites[tier]

#def vPrint(doit, message):
#	if doit:
#		pprint.pprint(message)

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
			if barcodetype == "ParticipantBarcode":
				barcode = barcode[:12]
			elif barcodetype == "SampleBarcode":
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
	version = "v2"
	api = 'isb_cgc_api'
	site = getSite(args.tier)
	#cohort_id = '1' #Seems like a reasonable default but will get a real one below
	#preview_request = {"Study" : ["BRCA", "UCS"], "age_at_initial_pathologic_diagnosis_gte": 90}

	#Get credentials
	vPrint(args.verbose, ("Using credentials %s" % str(args.credentialsfile)))
	credentials = get_credentials(args.credentialsfile)
	vPrint(args.verbose,credentials)
	
	#create Authorized Service
	auth_service = get_authorized_service(api, version, site, credentials, args.verbose)
	
	#Create the barcode array
	if args.sample:
		barcodetype = "SampleBarcode"
	elif args.patient:
		barcodetype = "ParticipantBarcode"
	else:
		print("No barcode type selection found, must use either -b or -p")
		sys.exit(0)
	barcodelist = barcodeProcess(args.barcodefile, barcodetype)
	request = {barcodetype:barcodelist}
	
	#test cohorts().preview()
	vPrint(args.verbose, "cohorts().preview() test")
	try:
		data = cohortsPreview(auth_service, request)
		logTest(logfile, args.tier, "Cohorts Preview Test", data['patient_count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Cohorts Preview ERROR", exception)
		
		
	#test cohorts().create()
	if args.createcohort:
		vPrint(args.verbose, "cohorts().create() test")
		try:
			data = cohortsCreate(auth_service,args.cohortname, request)
			testing_cohort_id = data['id']  #will be used to delete in the next test
			logTest(logfile,args.tier,"Cohorts Create Test", testing_cohort_id)
		except HttpError as exception:
			logTest(logfile, args.tier, "Cohorts Create ERROR", exception)

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
	args = parser.parse_args()

	main(args)
