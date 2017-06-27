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
import pprint


def markdownDataframe(df):
	return dcc.Dropdown( id = 'cohort-dropdown', options = [	
		{'label' : index, 'value' : index } for (index, row) in df.iterrows()
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
	tabledata = []
	for cohort in jsondata['items']:
		temp = [cohort['name'], cohort['case_count'], cohort['sample_count']]
		tabledata.append(temp)
	df = pd.DataFrame(tabledata, columns=columns)
	return df.set_index('name')


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
		
app = dash.Dash()

app.layout = html.Div([
    html.H1('Available Cohorts'),
    markdownDataframe(dataframe),
    dcc.Graph(id = 'case-graph')
  ]
)
	
@app.callback(
dash.dependencies.Output('case-graph', 'figure'),
[dash.dependencies.Input('cohort-dropdown', 'value')]
)
def update_figure(selected_cohort):
	case_count = dataframe.loc[selected_cohort, 'cases']
	sample_count = dataframe.loc[selected_cohort,'samples']
	
	return {
		'data' : [
			{ 'x' : [1], 'y' :[case_count], 'type' : 'bar', 'name' : 'Cases' },
			{'x' : [1], 'y' : [sample_count], 'type' : 'bar', 'name' : 'Samples'}
		],
		'layout' : {'title' : 'Cases and Samples'}
	}
	



if __name__ == '__main__':
    app.run_server(debug=True)


