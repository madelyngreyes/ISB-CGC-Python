#!/usr/bin/python
#########################
#   Stuff I use a lot	#
#########################

import pprint
import datetime
import os
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

#For APIs, will regutn and authorized servcie
def get_authorized_service(api, version, site, credentials, verbose):
    discovery_url = '%s/_ah/api/discovery/v1/apis/%s/%s/rest' % (site, api, version)
    if verbose:
		print discovery_url
    http = credentials.authorize(httplib2.Http())
    if credentials.access_token_expired or credentials.invalid:
        credentials.refresh(http)
    authorized_service = build(api, version, discoveryServiceUrl=discovery_url, http=http)
    return authorized_service

#Returns the URL for the ISB tiers
def getSite(tier):
	sites = {"mvm" : "https://api-dot-mvm-dot-isb-cgc.appspot.com",
			"dev" : "https://api-dot-mvm-dot-isb-cgc.appspot.com",
			"test" : "https://api-dot-isb-cgc-test.appspot.com",
			"prod" : "https://api-dot-isb-cgc.appspot.com" }
	return sites[tier]
