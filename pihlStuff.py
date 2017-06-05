#!/usr/bin/python
#########################
#   Stuff I use a lot	#
#########################

import pprint
import datetime
import os
import httplib2
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.discovery import build

#########################
#	Global variables	#
#########################
# the CLIENT_ID for the ISB-CGC site
CLIENT_ID = '907668440978-0ol0griu70qkeb6k3gnn2vipfa5mgl60.apps.googleusercontent.com'
# The google-specified 'installed application' OAuth pattern
CLIENT_SECRET = 'To_WJH7-1V-TofhNGcEqmEYi'
# The google defined scope for authorization
EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
# where a default credentials file will be stored for use by the endpoints
DEFAULT_STORAGE_FILE = os.path.join(os.path.expanduser("~"), '.isb_credentials')

#########################
#	Routines			#
#########################

#Print out any message if doit is True
def vPrint(doit, message):
	if doit:
		pprint.pprint(message)

#Print a timestamped string to a log file
def printLog (filehandle, message):
	now = datetime.datetime.now()
	timestamp = "%s-%s-%s_%s:%s:%s" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
	filehandle.write(("%s\t%s\n") % (timestamp, message))

#Read authentication from a file or authenticate against Google
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

#For APIs, will regutn and authorized servcie
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
