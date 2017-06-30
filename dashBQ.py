#/usr/bin/env python
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python
#https://cloud.google.com/bigquery/create-simple-app-api#bigquery-simple-app-build-service-python

from google.cloud import bigquery

DEFAULT_PROJECT = 'cgc-05-0016'

def getProjects():
	client = bigquery.Client()
	query = ("""
		select project_short_name
		from `isb-cgc.TCGA_bioclin_v0.Clinical` 
		GROUP BY project_short_name
	""")
	
	results = client.run_sync_query(query)
	results.use_legacy_sql = False
	results.run()
	rows = results.fetch_data()
	return rows

def projectDropdown(projects):
	return dcc.Dropdown( id = 'project-dropdown', options = [	
		{'label' : project, 'value' : project } for project in projects
	])

def getGenes(project):
	client = bigquery.Client()
	query = ("""
		WITH 
		pathGenes AS (
			SELECT Symbol
			FROM `isb-cgc.QotM.WikiPathways_20170425_Annotated`
			WHERE pathway = 'Notch Signaling Pathway'
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
	""")
	query_parameters = ( bigquery.ScalarQueryParameter('project', 'STRING', project))
	results = client.run_sync_query(query, query_parameters = [query_parameters])
	results.use_legacy_sql = False
	results.run()
	rows = results.fetch_data()
	return rows

###Main Section######
app = dash.Dash()


projects = getProjects()

app.layout = html.Div([
    html.H1('Available Projects'),
    projectDropdown(projects),
    dcc.Graph(id = 'gene-mutations')
  ]
)

@app.callback(
dash.dependencies.Output('gene-mutations', 'figure'),
[dash.dependencies.Input('project-dropdown', 'value')]
)

def update_figure(selected_project):
	rows = getGenes(selected_project)
	return {
		'data' : [{'x' : [symbol], 'y' : [count], 'type' : 'bar', 'name' : selected_project } for (symbol,count) in rows]
	}
if __name__ == '__main__':
    app.run_server(debug=True)
