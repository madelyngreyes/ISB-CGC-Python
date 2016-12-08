#!/usr/bin/python

#This script is a basic QA test to see if the ISB APIs are working.  Tests V2 APIs only
# http://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/progapi/Programmatic-API.html
#Much of the code is taken and/or adapted from:
#https://github.com/isb-cgc/examples-Python/blob/master/python/isb_cgc_api_v2_cohorts.py


import argparse
import os
import pprint
import httplib2
import datetime
import json
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# the CLIENT_ID for the ISB-CGC site
CLIENT_ID = '907668440978-0ol0griu70qkeb6k3gnn2vipfa5mgl60.apps.googleusercontent.com'
# The google-specified 'installed application' OAuth pattern
CLIENT_SECRET = 'To_WJH7-1V-TofhNGcEqmEYi'
# The google defined scope for authorization
EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
# where a default credentials file will be stored for use by the endpoints
DEFAULT_STORAGE_FILE = os.path.join(os.path.expanduser("~"), '.isb_credentials')


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
   

def get_authorized_service(api, version, site, credentials, verbose):
    discovery_url = '%s/_ah/api/discovery/v1/apis/%s/%s/rest' % (site, api, version)
    if verbose:
		print discovery_url
    http = credentials.authorize(httplib2.Http())
    if credentials.access_token_expired or credentials.invalid:
        credentials.refresh(http)
    authorized_service = build(api, version, discoveryServiceUrl=discovery_url, http=http)
    return authorized_service

def getSite(tier):
	sites = {"mvm" : "https://api-dot-mvm-dot-isb-cgc.appspot.com",
			"dev" : "https://api-dot-mvm-dot-isb-cgc.appspot.com",
			"test" : "https://api-dot-isb-cgc-test.appspot.com",
			"prod" : "https://api-dot-isb-cgc.appspot.com" }
	return sites[tier]
	
def vPrint(doit, message):
	if doit:
		pprint.pprint(message)

def logTest(filehandle, tier, testname, result):
	now = datetime.datetime.now()
	timestamp = "%s-%s-%s_%s:%s:%s" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
	filehandle.write(("%s\t%s\t%s\t%s\n") % (timestamp, tier, testname, result))
	
def logError(e, message, logfile, tier):
	error = json.loads(e.content)
	errorstring =  "%s:\t%s:\t%s\n" % (message, error.get('code'), error.get('errors'))
	logTest(logfile, tier, message, errorstring)
	
#Data Requests
def cohortsList(service):
	try:
		data = service.cohorts().list().execute()
		return data
	except HttpError as exception:
		raise exception
	
def cohortsFiles(service, cohort_id):
	try:
		data = service.cohorts().cloud_storage_file_paths(cohort_id=cohort_id).execute()
		return data
	except HttpError as exception:
		raise exception
	
def cohortsPreview(service, body):
	try:
		data = service.cohorts().preview(**body).execute()
		return data
	except HttpError as exception:
		raise exception
	
def cohortsGet(service, cohort_id):
	try:
		data = service.cohorts().get(cohort_id = cohort_id).execute()
		return data
	except HttpError as exception:
		raise exception
		
def cohortsCreate(service, name, body):
	try:
		data = service.cohorts().create(name=name, body=body).execute()
		return data
	except HttpError as exception:
		raise exception

def cohortsDelete(service, cohort_id):
	try:
		data = service.cohorts().delete(cohort_id=cohort_id).execute()
		return data
	except HttpError as exception:
		raise exception
	
def patientsGet(service, barcode):
	try:
		data = service.patients().get(patient_barcode = barcode).execute()
		return data
	except HttpError as exception:
		raise exception
	
def samplesGet(service,barcode):
	try:
		data = service.samples().get(sample_barcode = barcode).execute()
		return data
	except HttpError as exception:
		raise exception
	
def samplesFiles(service,barcode):
	try:
		data = service.samples().cloud_storage_file_paths(sample_barcode=barcode).execute()
		return data
	except HttpError as exception:
		raise exception
	
def usersGet(service):
	try:
		data = service.users().get().execute()
		return data
	except HttpError as exception:
		raise exception

		
def main(args):
	
	#Create the log file
	now = datetime.datetime.now()
	filename = "%s_%s_%s_ISB-CGG-API_Testing_Log.tsv" % (now.month, now.day, now.year)
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
	cohort_id = '1' #Seems like a reasonable default but will get a real one below
	preview_request = {"Study" : ["BRCA", "UCS"], "age_at_initial_pathologic_diagnosis_gte": 90}
	patient_barcode = 'TCGA-W5-AA2R'
	sample_barcode = 'TCGA-W5-AA2R-01A'
	cohort_name = "%s_%s_%s_API_Testing_Cohort" % (now.month, now.day, now.year)
	testing_cohort_id = None
	
	

	#Get credentials
	vPrint(args.verbose, ("Using credentials %s" % str(args.credentialsfile)))
	credentials = get_credentials(args.credentialsfile)
	vPrint(args.verbose,credentials)
	
	#create Authorized Service
	auth_service = get_authorized_service(api, version, site, credentials, args.verbose)
	
	#Test cohort endpoints 
	
	#Need to test the list first so that we can retrieve a valid cohort ID in case 1 isn't value
	#test cohorts().list() endpoint
	vPrint(args.verbose, "cohorts().list() test")
	try:
		data = cohortsList(auth_service)
		if data['count'] > 0:
			cohort_id = data['items'][0]['id']
		logTest(logfile,args.tier,"Cohorts List Test",data['count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Cohorts List ERROR", exception)
	
	#Test cohorts().cloud_storage_file_paths()
	vPrint(args.verbose, "cohorts().cloud_storage_file_paths() test")
	try:
		data = cohortsFiles(auth_service, cohort_id)
		logTest(logfile,args.tier,"Cohorts Storage File Paths",data['count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Cohorts Cloud Storage File Paths ERROR", exception)
	
	#test cohorts().preview()
	vPrint(args.verbose, "cohorts().preview() test")
	try:
		data = cohortsPreview(auth_service, preview_request)
		logTest(logfile, args.tier, "Cohorts Preview Test", data['patient_count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Cohorts Preview ERROR", exception)
	
	#test cohorts().get()
	vPrint(args.verbose, "cohorts().get() test")
	try:
		data = cohortsGet(auth_service, cohort_id)
		logTest(logfile, args.tier, "Cohorts Get Test", data['patient_count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Cohorts Get ERROR", exception)
		
	#test cohorts().create()
	vPrint(args.verbose, "cohorts().create() test")
	try:
		data = cohortsCreate(auth_service, cohort_name, preview_request)
		testing_cohort_id = data['id']  #will be used to delete in the next test
		logTest(logfile,args.tier,"Cohorts Create Test", testing_cohort_id)
	except HttpError as exception:
		logTest(logfile, args.tier, "Cohorts Create ERROR", exception)
		
	#test cohorts().delete()
	vPrint(args.verbose, "cohorts().delete() test")
	if testing_cohort_id is not None:
		try:
			data = cohortsDelete(auth_service, testing_cohort_id)
			logTest(logfile, args.tier, "Cohorts Delete Test", data['message'])
		except HttpError as exception:
			logTest(logfile, args.tier, "Cohorts Delete ERROR", exception)
	else:
		logTest(logfile,args.tier, "Cohorts Delete Test", "Not performed because of no testing cohort ID")
	
	#Test Patient endpoints
	
	#test patients().get()
	vPrint(args.verbose, "patients().get() test")
	try:
		data = patientsGet(auth_service, patient_barcode)
		logTest(logfile, args.tier, "Patient Get Test", len(data['samples']))
	except HttpError as exception:
		logTest(logfile, args.tier, "Patients Get ERROR", exception)
	
	#Test Sample Endpoints
	
	#test samples().get()
	vPrint(args.verbose, "samples().get() test")
	try:
		data = samplesGet(auth_service, sample_barcode)
		logTest(logfile, args.tier, "Sample Get Test", data['data_details_count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Samples Get ERROR", exception)
	
	#test samples().cloud_storage_file_paths()
	vPrint(args.verbose, "samples().cloud_storage_file_paths() test")
	try:
		data = samplesFiles(auth_service, sample_barcode)
		logTest(logfile, args.tier, "Sample File Path Test", data['count'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Sample File Path ERROR", exception)
	
	#Test User Endpoint
	
	vPrint(args.verbose, "users().get() test")
	try:
		data = usersGet(auth_service)
		logTest(logfile, args.tier, "Users Get Test", data['message'])
	except HttpError as exception:
		logTest(logfile, args.tier, "Users Get ERROR", exception)


	logfile.close()
	
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback. Does not affect logging')
	tierchoice = ["mvm", "dev", "test", "prod"]
	parser.add_argument("-t", "--tier", required = True, type = str.lower, choices = tierchoice, help = "Tier that the tests will be run on")
	parser.add_argument("-c", "--credentialsfile", nargs = '?', const = None , help="File to use for credentials, will default to ~/.isb_credentials if left blank")
	args = parser.parse_args()
	main(args)
