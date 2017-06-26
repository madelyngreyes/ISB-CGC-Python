#/usr/bin/env python
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import pihlStuff as pihl
import httplib2
import json
from googleapiclient.errors import HttpError

#app = dash.Dash()

'''
app.layout = html.Div(children = [
	html.H1(children='Available Cohorts'),
	html.Select(children = [
		html.Option(children = 'One'),
		html.Option(children = 'Two'),
		html.Option(children = 'Three')
	])
]
)
'''
def cohortsList(service):
	try:
		data = service.cohorts().list().execute()
		return data
	except HttpError as exception:
		raise exception
		

def main():
	cohort_names = []
	credentials = pihl.get_credentials(None, 'prod',False)
	endpoint = pihl.getProgram("COMMON")
	site = pihl.getSite("prod")
	version = "v3"
	service = pihl.get_authorized_service(endpoint, version, site, credentials, False)
	
	try:
		data = cohortsList(service)
	except HttpError as exception:
		print exception
		
	for cohort in data['items']:
		cohort_names.append(cohort['name'])
	
	print cohort_names
	

if __name__ == '__main__':
    #app.run_server(debug=True)
    main()


