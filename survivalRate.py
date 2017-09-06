#!/usr/bin/env python
# A Python/Dash version of David Gibb's August Query of the Month
# http://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/QueryOfTheMonthClub.html
# https://github.com/plotly/dash-recipes


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, Event, State

from oauth2client.client import GoogleCredentials
from google.cloud import bigquery
import pandas as pd
from pandas.io import gbq
from lifelines import KaplanMeierFitter
import plotly.graph_objs as go


def runSyncQuery(query, parameters, project):
	bq = bigquery.Client(project=project)
	if parameters is not None:
		query_results = bq.run_sync_query(query, query_parameters = parameters)
	else:
		query_results = bq.run_sync_query(query)
	query_results.use_legacy_sql = False
	query_results.run()
	rows = query_results.fetch_data()
	return rows
	
def getProjects(project):
	rows = []
	query = ("""
		select project_short_name
		from `isb-cgc.TCGA_bioclin_v0.Clinical` 
		GROUP BY project_short_name
		ORDER BY project_short_name ASC
	""")
	rows = runSyncQuery(query, None, project)
	return rows

def getData(project,study, genename):
	rows = []
	query = ("""
		WITH clin_table AS (
		SELECT 
			case_barcode, days_to_last_known_alive, vital_status
		FROM
			`isb-cgc.TCGA_bioclin_v0.Clinical`
		WHERE
			project_short_name = @study ),
		mut_table AS (
		SELECT
			case_barcode,
		IF ( case_barcode IN (
			SELECT
				case_barcode
			FROM
				`isb-cgc.TCGA_hg38_data_v0.Somatic_Mutation`
		WHERE
		SYMBOL = @genename
		AND Variant_Classification <> 'Silent'
		AND Variant_Type = 'SNP'
		AND IMPACT <> 'LOW'), 'Mutant', 'WT') AS mutation_status
		FROM
			`isb-cgc.TCGA_hg38_data_v0.Somatic_Mutation` )
		SELECT
			mut_table.case_barcode, days_to_last_known_alive, vital_status, mutation_status
		FROM
			clin_table
		JOIN
			mut_table
		ON
			clin_table.case_barcode = mut_table.case_barcode
		GROUP BY
			mut_table.case_barcode,
			days_to_last_known_alive,
			vital_status,
			mutation_status
	""")
	
	query_parameters = ( bigquery.ScalarQueryParameter('study', 'STRING', study),
						bigquery.ScalarQueryParameter('genename', 'STRING', genename)
						)
	rows = runSyncQuery(query, query_parameters, project)
	return rows

###Main Section######
app = dash.Dash()

app.layout = html.Div([
	html.Div([
		html.Button( ['Login via Google'],
			id = 'loginbutton'
		),
		html.P('Project ID'),
		dcc.Input(
			id = 'projectid',
			placeholder = 'Enter Project ID Here',
			type = 'text',
			value = ''
		),
		html.P('Cohort'),
		dcc.Dropdown(id = 'project-dropdown'),
		html.P('Gene Symbol'),
		dcc.Input(
			id = 'genename',
			placeholder = 'Enter gene name here',
			type = 'text',
			value = ''
		),
		html.P('Click to graph'),
		html.Button(['Submit'],
			id = 'submitbutton')
	
	],
	style = {"width" : '20%'}
	),
	html.Div([
		dcc.Graph(id = 'graph')
	])
])

# https://github.com/plotly/dash-recipes/blob/master/sql_dash_dropdown.py
@app.callback(
	Output('project-dropdown', 'options'),
	state = [State ('projectid', 'value')],
	events = [Event('loginbutton', 'click')]
)
def doLogin(project):
	projects = []
	credentials = GoogleCredentials.get_application_default()
	print credentials
	projects = getProjects(project)
	return[ {'label' : project[0], 'value' : project[0]} for project in projects]

#https://github.com/plotly/dash-recipes/blob/master/dash-click.py
@app.callback(
	Output('graph', 'figure'),
	state = [ State('genename','value'),
	State('project-dropdown', 'value'),
	State('projectid', 'value')],
	events = [Event('submitbutton', 'click')]
)
def graphQuery(gene, study, project):
	print "Graph query"
	wt_time = []
	wt_state = []
	mut_time = []
	mut_state = []
	wtdf = KaplanMeierFitter()
	mutdf = KaplanMeierFitter()
	
	rows = getData(project, study, gene)
	print "Starting row parse"
	for (barcode, days, vital, mutation) in rows:
		if mutation == 'WT':
			#There are negative day values, set to 0
			if days >= 0:
				wt_time.append(days)
			else:
				wt_time.append(0)
			if vital == 'Alive':
				wt_state.append(1)
			else:
				wt_state.append(0)
		elif mutation == 'Mutant':
			if days >= 0:
				mut_time.append(days)
			else:
				mut_time.append(0)
			if vital == 'Alive':
				mut_state.append(1)
			else:
				mut_state.append(0)
		else:
			print "Neither WT nor Mutant"
	
	wtdf.fit(wt_time, event_observed=wt_state)
	mutdf.fit(mut_time, event_observed=mut_state)
		
	#https://plot.ly/ipython-notebooks/survival-analysis-r-vs-python/#using-python
	#In lifelines, once the fit is done, survival_function_ is a dataframe
	#https://github.com/plotly/dash-wind-streaming/blob/master/app.py
	trace0 = go.Scatter(
		y = wtdf.survival_function_['KM_estimate'],
		x = wtdf.survival_function_.index,
		mode = 'lines',
		name = 'Wild Type'
		)
	trace1 = go.Scatter(	
		y = mutdf.survival_function_['KM_estimate'],
		x = mutdf.survival_function_.index,
		mode = 'lines',
		name = 'Mutant'
	)
	
	return go.Figure (data=[trace0,trace1])
	
if __name__ == '__main__':
    app.run_server(debug=True)
