#!/usr/bin/python
# https://github.com/NCIP/gdc-docs/blob/Visualization-Docs/docs/Visualization_Documentation/API_Endpoints.md
import json
import requests
import pprint
import urllib
import argparse


BASE_URL = 'https://gdc-api-staging.datacommons.io/'

def getQuery(url):
	response = requests.get(url)
	data = response.content
	return data
	
def postQuery(url, headers, query):
	response = requests.post(url, headers=headers, data=json.dumps(query))
	data = response.content
	return data
	
def jsonEncode(json_query):
	encoded = urllib.quote_plus(json_query)
	return encoded
	

def main(args):
	ENDPOINT = 'genes'
	QUERY = 'ZMPSTE24'
	GENE_ID = 'ENSG00000084073'
	FIELD = 'symbol'
	TAIL = "?pretty=true"
	if args.mutation:
		ENDPOINT = 'ssm_occurrences'
		QUERY = 'TCGA-DJ-A3US'
		FIELD = "case.submitter_id"
		 
	
	json_get = """{
		"op" : "in", 
		"content" : {
			"field" : "%s" ,
			"value" : ["%s" ] 
		}
	}""" % (FIELD, QUERY)
	
	json_post = {
		"filters" : {
			"op" : "and",
			"content" : [{
				"op" : "in",
				"content" : {
					"field" : FIELD,
					"value" : [QUERY]
				}
			}]
		},
		"fields" : "ssm.chromosome",
		"size" : 1000
	}
	headers = {
                "Content-Type" : "application/json"
        }
	
	if args.get:
		pprint.pprint(json_get)
		encoded = jsonEncode(json_get)
		pprint.pprint(encoded)
		url = BASE_URL + ENDPOINT + "?pretty=true&filters=" + encoded
		pprint.pprint(url)
		data = getQuery(url)
		pprint.pprint(data)
	elif args.post:
		url = BASE_URL + ENDPOINT
		data = postQuery(url, headers, json_post)
		pprint.pprint(data)
	else:
		print "No query type selected"

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback.')
	parser.add_argument("-g", "--get", action = "store_true", help = 'Query via GET')
	parser.add_argument("-p", "--post", action = "store_true", help = 'Query via POST')
	parser.add_argument("-m", "--mutation", action = "store_true", help = "Run a mutation query")
	
	args = parser.parse_args()
	main(args)
