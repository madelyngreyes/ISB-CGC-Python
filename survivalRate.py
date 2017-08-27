#!/usr/bin/env python
# A Python/Dash version of David Gibb's August Query of the Month
# http://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/QueryOfTheMonthClub.html

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from oauth2client.client import GoogleCredentials

import pihlStuff as pihl



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
	
def getProjects():
	rows = []
	query = ("""
		select project_short_name
		from `isb-cgc.TCGA_bioclin_v0.Clinical` 
		GROUP BY project_short_name
		ORDER BY project_short_name ASC
	""")
	rows = runSyncQuery(query, None, project)
	return rows

def projectDropdown(projects):
	return dcc.Dropdown( id = 'project-dropdown', 
						options = [	
						{'label' : project[0], 'value' : project[0] } for project in projects
						])	


###Main Section######
app = dash.Dash()

projects = ('TCGA-BRCA', 'TCGA-ACC', 'TCGA-ESCA')

app.layout = html.Div([
	html.Div(id = 'main_div'),
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
	projectDropdown(projects),
	html.P('Gene Symbol'),
	dcc.Input(
		id = 'genename',
		placeholder = 'Enter gene name here',
		type = 'text',
		value = ''
	),
	html.P('Click to graph'),
	html.Button(['Submit'])
	
  ],
  style = {"width" : '10%'}
)

@app.callback(
dash.dependencies.Output(component_id = 'main_div',component_property = 'children'),
[dash.dependencies.Input("loginbutton","value")]
)
def doLogin(value):
	#pihl.get_credentials(None, "prod", True)
	credentials = GoogleCredentials.get_application_default()
	print credentials
	
@app.callback(
dash.dependencies.Output(component_id = "project-dropdown", component_property = 'value'),
[dash.dependencies.Input("loginbutton", "value")]
)
def doProjects(value):
	projects = getProjects()
	

if __name__ == '__main__':
    app.run_server(debug=True)
