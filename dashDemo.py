#/usr/bin/env python
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pihlStuff as pihl
import httplib2
import json
from googleapiclient.errors import HttpError
import pandas as pd


def selectLayout(cohortList):
 return html.Select(children = [
			html.Option(children = cohort) for cohort in cohortList
	])
	
def markdownLayout(cohortList):
	return dcc.Dropdown( options = [
		{'label' : cohort, 'value' : cohort } for cohort in cohortList
	])

def markdownDataframe(df):
	return dcc.Dropdown( options = [
		{'label' : row.loc['name'], 'value' : row.loc['name'] } for (index, row) in df.iterrows()
	])
		
def cohortsList(service):
	try:
		data = service.cohorts().list().execute()
		return data
	except HttpError as exception:
		raise exception
		
def json2df(jsondata):
	columns = ['name', 'cases', 'samples']
	count = jsondata['count']
	#df = pd.DataFrame(columns = columns, index = count)
	tabledata = []
	for cohort in jsondata['items']:
		temp = [cohort['name'], cohort['case_count'], cohort['sample_count']]
		tabledata.append(temp)
	df = pd.DataFrame(tabledata, columns=columns)
	return df	
	
		

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
	
	dataframe = json2df(data)

		
	#for cohort in data['items']:
	#	cohort_names.append(cohort['name'])
		
	app = dash.Dash()
	app.layout = html.Div(children = [
	    html.H1(children='Available Cohorts'),
	    #selectLayout(cohort_names)
	    #markdownLayout(cohort_names)
	    markdownDataframe(dataframe)
	  ]
	)
	
	app.run_server(debug=True)

if __name__ == '__main__':
    main()


