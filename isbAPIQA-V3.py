#!/usr/bin/python

#This script is a basic QA test to see if the V3 ISB APIs are working.  Tests V3 APIs only
# http://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/progapi/Programmatic-API.html
# Much of the code is taken and/or adapted from:
# https://github.com/isb-cgc/examples-Python/blob/master/python/isb_cgc_api_v2_cohorts.py
#
# Credential files can be generated using isb_auth.py -v -u -s credential_filename 
# Paste the URL into a logged in browser window
#
#  API Repo: https://github.com/isb-cgc/ISB-CGC-API/tree/api_3/api_3
#  Google API Explorer (MVM!!!):  https://apis-explorer.appspot.com/apis-explorer/?base=https://mvm-api-dot-isb-cgc.appspot.com/_ah/api#p/
#
# For testing TARGET and CCLE on the different tiers, you need to first create cohorts with specific names.  TCGA has a universally shared cohort
# TARGET - "All TARGET for testing"
# CCLE - "All TARGET for testing"
# TCGA - "All TCGA Data"
#


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

# The google defined scope for authorization
EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
# where a default credentials file will be stored for use by the endpoints
DEFAULT_STORAGE_FILE = os.path.join(os.path.expanduser("~"), '.isb_credentials')


def get_credentials(credFile, tier, verbose):
	oauth_flow_args = ['--noauth_local_webserver']
	if credFile is None:
		storage = Storage(DEFAULT_STORAGE_FILE)
	else:
		storage = Storage(credFile)
	credentials = storage.get()
	
	client_id = {
		'mvm' : '907668440978-0ol0griu70qkeb6k3gnn2vipfa5mgl60.apps.googleusercontent.com',
		'dev' : '907668440978-0ol0griu70qkeb6k3gnn2vipfa5mgl60.apps.googleusercontent.com',
		'test' : '144657163696-9dnmed5krg4r00km2fg1q93l71nj3r9j.apps.googleusercontent.com',
		'prod' : '907668440978-0ol0griu70qkeb6k3gnn2vipfa5mgl60.apps.googleusercontent.com'
	}
	
	client_secret = {
		'mvm' : 'To_WJH7-1V-TofhNGcEqmEYi',
		'dev' : 'To_WJH7-1V-TofhNGcEqmEYi',
		'test' : 'z27YV6Fd0HDKISkkHVoY1cTa',
		'prod' : 'To_WJH7-1V-TofhNGcEqmEYi'
	}
	vPrint(verbose, ("ID: %s" % client_id[tier]))
	vPrint(verbose, ("Secret: %s" % client_secret[tier]))
	if not credentials or credentials.invalid:
		flow = OAuth2WebServerFlow(client_id[tier], client_secret[tier], EMAIL_SCOPE)
		flow.auth_uri = flow.auth_uri.rstrip('/') + '?approval_prompt=force'
		credentials = tools.run_flow(flow, storage, tools.argparser.parse_args(oauth_flow_args))
	return credentials


def get_authorized_service(program_api, version, site, credentials, verbose):
    discovery_url = '%s/_ah/api/discovery/v1/apis/%s/%s/rest' % (site, program_api, version)
    if verbose:
		print discovery_url
    http = credentials.authorize(httplib2.Http())
    if credentials.access_token_expired or credentials.invalid:
        credentials.refresh(http)
    authorized_service = build(program_api, version, discoveryServiceUrl=discovery_url, http=http)
    return authorized_service

def getSite(tier):
	sites = {"mvm" : "https://mvm-api-dot-isb-cgc.appspot.com",
			"dev" : "https://mvm-api-dot-isb-cgc.appspot.com",
			"test" : "https://api-dot-isb-cgc-test.appspot.com",
			"prod" : "https://api-dot-isb-cgc.appspot.com" }
	return sites[tier]
	
def getProgram(program):
	programs = {
			"TCGA" : "isb_cgc_tcga_api",
			"TARGET" : "isb_cgc_target_api",
			"CCLE" : "isb_cgc_ccle_api"
			}
	return programs[program]
	
def vPrint(doit, message):
	if doit:
		pprint.pprint(message)

def logTest(filehandle, program, tier, testname, status, result):
	now = datetime.datetime.now()
	timestamp = "%s-%s-%s_%s:%s:%s" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
	filehandle.write(("%s\t%s\t%s\t%s\t%s\t%s\n") % (timestamp, program, tier, testname, status, result))
	
		
# Cohort testing
def cohortsList(service):
	try:
		data = service.cohorts().list().execute()
		return data
	except HttpError as exception:
		raise exception

def cohortsFiles(service, cohort_id, limit):
	try:
		if limit == 0:
			data = service.cohorts().cloud_storage_file_paths(cohort_id=cohort_id).execute()
		else:
			data = service.cohorts().cloud_storage_file_paths(cohort_id=cohort_id, limit=limit).execute()
		return data
	except HttpError as exception:
		raise exception
	
def cohortsPreview(service, body):
	try:
		data = service.cohorts().preview(body=body).execute()
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

#Cases testing
def casesGet(service, barcode):
	try:
		data = service.cases().get(case_barcode = barcode).execute()
		return data
	except HttpError as exception:
		raise exception

#Samples testing	
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

#Users testing	
def usersGet(service):
	try:
		data = service.users().get().execute()
		return data
	except HttpError as exception:
		raise exception

#Annotation testing (Currently TCGA only)
def aliquotAnnotations(service,barcode):
	try:
		data = service.aliquots().annotations(aliquot_barcode=barcode).execute()
		return data
	except HttpError as exception:
		raise exception

def sampleAnnotations(service,barcode):
	try:
		data = service.samples().annotations(sample_barcode=barcode).execute()
		return data
	except HttpError as exception:
		raise exception

def caseAnnotations(service,barcode):
	try:
		data = service.cases().annotations(case_barcode=barcode).execute()
		return data
	except HttpError as exception:
		raise exception

def getCohortIDs(cohortlist, cohortname, program):
	cohortdictionary = {
		'TCGA' : None,
		'TARGET' : None,
		'CCLE' : None
	}
	
	for cohort in cohortlist['items']:
		if cohort['name'] == cohortname:
			cohortdictionary[program] = cohort['id']
	return cohortdictionary
	
def main(args):
	
	#Create the log file
	now = datetime.datetime.now()
	filename = "%s_%s_%s_ISB-CGG-API_Testing_Log.tsv" % ( now.month, now.day, now.year)
	log_header = "Timestamp\tTest Program\tTest Tier\tTest Name\tStatus\tResult Message\n"
	
	if os.path.isfile(filename):
		logfile = open(filename, "a")
	else:
		logfile = open(filename,"w")
	logfile.write(log_header)
	
	#Set up main variables
	version = "v3"
	program_api = getProgram(args.program)
	site = getSite(args.tier)

	
	preview_request = {
		'TCGA' : '{"Common": {"project_short_name": ["TCGA-BRCA","TCGA-UCS"]}, "Clinical": {"age_at_diagnosis_gte": 90}}',
		'TARGET' : '{"Common" : {"project_short_name" : ["TARGET-AML", "TARGET-WT"]}, "Clinical" : {"age_at_diagnosis_gte": 7}}',
		'CCLE' : '{"Common" : {"project_short_name" : ["CCLE-COAD", "CCLE-READ"]}, "Clinical" : {"gender": "Male"}}'
		}
	testing_cohort_request = {
		'TARGET' : '{"program_name" : ["TARGET"] }',
		'CCLE' : '{"program_name" : ["CCLE"]}',
		'TCGA' : '{"program_name" : ["TCGA"]}'
	}
	testing_cohort_name = {
		'TARGET' : 'All TARGET for testing',
		'CCLE': 'All CCLE for testing',
		"TCGA": 'All TCGA Data'
	}
	
	case_barcode = {'TCGA' : 'TCGA-DJ-A3US', 'TARGET' : 'TARGET-20-PABLDZ', 'CCLE' : 'FU-OV-1'}
	sample_barcode = {'TCGA' : 'TCGA-DJ-A3US-10A', 'TARGET' : 'TARGET-20-PABLDZ-04A', 'CCLE' : 'CCLE-FU-OV-1'}
	aliquot_barcode = {'TCGA' :'TCGA-DJ-A3US-10A-01D-A22C-01', 'TARGET' : 'TARGET-20-PABLDZ-04A-01R', 'CCLE' : 'CCLE-FU-OV-1-RNA-08'}
	
	cohort_name = "%s_%s_%s_%s_API_Testing_Cohort" % (now.month, now.day, now.year, args.program)
	testing_cohort_id = None
	recordlimit = 0

	

	#Get credentials
	vPrint(args.verbose, ("Using credentials %s" % str(args.credentialsfile)))
	credentials = get_credentials(args.credentialsfile, args.tier, args.verbose)
	vPrint(args.verbose,credentials)
	
	#create Authorized Services, one for common services and one for program specific
	program_auth_service = get_authorized_service(program_api, version, site, credentials, args.verbose)
	common_auth_service = get_authorized_service("isb_cgc_api", version, site, credentials, args.verbose)
	
	######################################################
	#                                                    #
	#                Testing                             #
	#                                                    #
	######################################################
	
	#Need to test the cohort list first so that we can retrieve a valid cohort ID in case 1 isn't value
	#test cohorts().list() endpoint
	# The following enpoints are program agnostic:  cohorts.cloud_storage_file_paths, cohorts.delete, cohorts, get, cohorts.list
	vPrint(args.verbose, "cohorts().list() test")
	try:
		data = cohortsList(common_auth_service)
		cohort_id_set = getCohortIDs(data, testing_cohort_name[args.program], args.program)
		cohort_id = cohort_id_set[args.program]
		
		#If the testing cohort doesn't exist, create it
		if cohort_id is None:
			vPrint(args.verbose, ("No testing cohort for %s, creating one" % args.program))
			try:
				data = cohortsCreate(program_auth_service, testing_cohort_name[args.program], json.loads(testing_cohort_request[args.program]))
				cohort_id = data['id'] 
				vPrint(args.verbose, ("Testing cohort id is %s" % cohort_id))
				logTest(logfile,args.program, args.tier,"Creating Testing Cohort", "PASS", "Successfully created Testing cohort " + cohort_id)
			except HttpError as exception:
				logTest(logfile, args.program, args.tier, "Creating Testing Cohort", "FAIL", exception)
		
		vPrint(args.verbose, ("Program:\t%s\tCohort ID:\t%s" % (args.program, cohort_id)))
		logTest(logfile,args.program, args.tier,"Cohorts List Test","PASS", "Number of cohorts found: " + str(data['count']))
	except HttpError as exception:
		logTest(logfile, args.program, args.tier, "Cohorts List Test", "FAIL", exception)
		
	#Test cohorts().cloud_storage_file_paths()
	vPrint(args.verbose, "cohorts().cloud_storage_file_paths() test")
	if cohort_id is not None:
		try:
			data = cohortsFiles(common_auth_service, cohort_id, recordlimit)
			logTest(logfile,args.program, args.tier,"Cohorts Storage File Paths", "PASS", "Number of cohort files found: " + str(data['count']) + " for cohort " + cohort_id)
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Cohorts Cloud Storage File Paths", "FAIL", exception)
	else:
		logTest(logfile, args.program, args.tier, "Cohorts Cloud Storage File Paths", "FAIL", "No valid cohort ID provided")
	
	#test cohorts().preview()
	vPrint(args.verbose, "cohorts().preview() test")
	try:
		data = cohortsPreview(program_auth_service, json.loads(preview_request[args.program]))
		logTest(logfile, args.program, args.tier, "Cohorts Preview Test", "PASS", "Cohort case count: " + str(data['case_count']))
	except HttpError as exception:
		logTest(logfile, args.program, args.tier, "Cohorts Preview Test", "FAIL", exception)
	
	#test cohorts().get()
	vPrint(args.verbose, "cohorts().get() test")
	if cohort_id is None:
		logTest(logfile, args.program, args.tier, "Cohorts Get Test", "FAIL", "No testing cohort available")
	else:
		try:
			data = cohortsGet(common_auth_service, cohort_id)
			logTest(logfile, args.program, args.tier, "Cohorts Get Test", "PASS", "Cohort sample count: " + str(data['sample_count']))
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Cohorts Get Test", "FAIL", exception)
		
	#test cohorts().create()
	vPrint(args.verbose, "cohorts().create() test")
	try:
		data = cohortsCreate(program_auth_service, cohort_name, json.loads(preview_request[args.program]))
		testing_cohort_id = data['id']  #will be used to delete in the next test
		logTest(logfile,args.program, args.tier,"Cohorts Create Test", "PASS", "Successfully created cohort " + testing_cohort_id)
	except HttpError as exception:
		logTest(logfile, args.program, args.tier, "Cohorts Create Test", "FAIL", exception)
		
	#test cohorts().delete()
	vPrint(args.verbose, "cohorts().delete() test")
	if testing_cohort_id is not None:
		try:
			data = cohortsDelete(common_auth_service, testing_cohort_id)
			logTest(logfile, args.program, args.tier, "Cohorts Delete Test", "PASS", data['message'])
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Cohorts Delete Test", "FAIL", exception)
	else:
		logTest(logfile,args.program, args.tier, "FAIL","Cohorts Delete Test", "Not performed because of no testing cohort ID")
	
	#Test Patient endpoints
	
	#test cases().get()
	vPrint(args.verbose, "cases().get() test")
	try:
		data = casesGet(program_auth_service, case_barcode[args.program])
		logTest(logfile, args.program, args.tier, "Patient Get Test", "PASS", "Number of samples for case: " + str(len(data['samples'])))
	except HttpError as exception:
		logTest(logfile, args.program, args.tier, "Patients Get Test", "FAIL" , exception)
	
	#Test Sample Endpoints
	
	#test samples().get()
	vPrint(args.verbose, "samples().get() test")
	try: 
		data = samplesGet(program_auth_service, sample_barcode[args.program])
		logTest(logfile, args.program, args.tier, "Sample Get Test", "PASS", "Number of sample detail sections: " + str(data['data_details_count']))
	except HttpError as exception:
		logTest(logfile, args.program, args.tier, "Samples Get test", "FAIL", exception)
	
	#test samples().cloud_storage_file_paths()
	vPrint(args.verbose, "samples().cloud_storage_file_paths() test")
	try:
		data = samplesFiles(program_auth_service, sample_barcode[args.program])
		logTest(logfile, args.program, args.tier, "Sample File Path Test", "PASS", "Number of files for sample: " + str(data['count']))
	except HttpError as exception:
		logTest(logfile, args.program, args.tier, "Sample File Path Test", "FAIL", exception)
	
	#Test User Endpoint
	#Don't test if CCLE, it doesn't have this
	if (args.program != "CCLE"):
		vPrint(args.verbose, "users().get() test")
		try:
			data = usersGet(program_auth_service)
			logTest(logfile, args.program, args.tier, "Users Get Test", "PASS", data['message'])
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Users Get Test", "FAIL", exception)
	
	#Check the annotations endpoints only if testing TCGA
	if (args.program == "TCGA"):
		
		#Test Aliquot Annotation
		vPrint(args.verbose, "aliquots().annotations() test")
		try:
			data = aliquotAnnotations(program_auth_service, aliquot_barcode[args.program])
			logTest(logfile, args.program, args.tier, "Aliquot Annotation Test", "PASS", "Number of aliquot annotations: " + str(data['count']))
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Aliquot Annotation Test", "FAIL",  exception)
			
		#Test Sample Annotation
		vPrint(args.verbose, "samples().annotations() test")
		try:
			data = sampleAnnotations(program_auth_service, sample_barcode[args.program])
			logTest(logfile, args.program, args.tier, "Sample Annotation Test", "PASS", "Number of sample annotations: " + str(data['count']))
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Sample Annotation Test", "FAIL", exception)
		
		#Test Case Annotation
		vPrint(args.verbose, "cases().annotations() test")
		try:
			data = caseAnnotations(program_auth_service, case_barcode[args.program])
			logTest(logfile, args.program, args.tier, "Case Annotation Test", "PASS", "Number of case annotations: " + str(data['count']))
		except HttpError as exception:
			logTest(logfile, args.program, args.tier, "Case Annotation Test", "FAIL", exception)


	logfile.close()
	
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback. Does not affect logging')
	tierchoice = ["mvm", "dev", "test", "prod"]
	parser.add_argument("-t", "--tier", required = True, type = str.lower, choices = tierchoice, help = "Tier that the tests will be run on")
	programchoice = ["TCGA", "TARGET", "CCLE"]
	parser.add_argument("-p", "--program", required = True, type = str.upper, choices = programchoice, help = "Program  (TCGA, TARGET, CCLE) that the tests will be run on")
	parser.add_argument("-c", "--credentialsfile", nargs = '?', const = None , help="File to use for credentials, will default to ~/.isb_credentials if left blank")
	args = parser.parse_args()
	main(args)
