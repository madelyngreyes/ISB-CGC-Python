#/usr/bin/env python
# -*- coding: utf-8 -*-
#Users need to run gcloud auth application-default login before this will work

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python
#https://cloud.google.com/bigquery/create-simple-app-api#bigquery-simple-app-build-service-python

from google.cloud import bigquery

DEFAULT_PROJECT = 'cgc-05-0016'

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
	rows = runSyncQuery(query, None, DEFAULT_PROJECT)
	return rows
	
def getPathways():
	rows = []
	query = ("""
		select pathway
		from `isb-cgc.QotM.WikiPathways_20170425_Annotated` 
		group by pathway
		ORDER BY pathway ASC
	""")
	rows = runSyncQuery(query, None, DEFAULT_PROJECT)
	return rows

	
def projectDropdown(projects):
	return dcc.Dropdown( id = 'project-dropdown', 
						options = [	
						{'label' : project[0], 'value' : project[0] } for project in projects
						])

def pathwayDropdown(pathways):
	return dcc.Dropdown( id = 'pathway-dropdown', 
						options = [
						{'label': pathway[0], 'value' : pathway[0] } for pathway in pathways
						])

def getGenes(project, pathway):
	query = ("""
		WITH 
		pathGenes AS (
			SELECT Symbol
			FROM `isb-cgc.QotM.WikiPathways_20170425_Annotated`
			WHERE pathway = @pathway
			GROUP BY Symbol
		),
		varsMC3 AS (
			SELECT project_short_name, case_barcode, Hugo_Symbol
			FROM `isb-cgc.TCGA_hg19_data_v0.Somatic_Mutation_MC3`
			WHERE
				Variant_Type = 'SNP'
				AND Consequence = 'missense_variant'
				AND biotype = 'protein_coding'
				AND SWISSPROT IS NOT NULL
				AND REGEXP_CONTAINS(PolyPhen, 'damaging')
				AND REGEXP_CONTAINS(SIFT, 'deleterious')
				AND Hugo_Symbol IN (select Symbol as Hugo_Symbol from pathGenes)
			GROUP BY project_short_name, case_barcode, Hugo_Symbol
		)
		--
		--
		SELECT Hugo_Symbol, count(Hugo_Symbol) as gene_count
		FROM varsMC3
		WHERE project_short_name = @project
		GROUP BY Hugo_Symbol
		ORDER BY
		gene_count DESC	
		LIMIT 10
	""")
	query_parameters = ( bigquery.ScalarQueryParameter('project', 'STRING', project),
						bigquery.ScalarQueryParameter('pathway', 'STRING', pathway)
						)
	rows = runSyncQuery(query, query_parameters, DEFAULT_PROJECT)
	return rows

###Main Section######
app = dash.Dash()

projects = getProjects()
pathways = getPathways()

app.layout = html.Div([
	html.Div([
		html.P('Available Projects'),
		projectDropdown(projects),
		html.P('Available Pathways'),
		pathwayDropdown(pathways)
	]),
    html.Div([
		dcc.Graph(id = 'gene-mutations')
		])
  ]
)


@app.callback(
dash.dependencies.Output('gene-mutations', 'figure'),
[dash.dependencies.Input('project-dropdown', 'value'),
dash.dependencies.Input('pathway-dropdown', 'value')]
)
def update_figure(selected_project, selected_pathway):
	rows = getGenes(selected_project, selected_pathway)
	return {
		'data' : [{'x' : [symbol], 'y' : [count], 'type' : 'bar', 'name' : selected_project } for (symbol,count) in rows]
	}

if __name__ == '__main__':
    app.run_server(debug=True)
