#! /usr/bin/python
#
# This is a utility to take the Case JSON file downloaded from GDC and convert it to tab so it can be uploaded to BigQuery

import json
import argparse


def main(args):
	inputfile = open(args.inputfile,'r')
	outputfile = open(args.outputfile,'w')
	
	header = "project_short_name\tprimary_site\tgdc_case_id\tgender\n"
	outputfile.write(header)
	
	data = json.load(inputfile)
	
	for entry in data:
		project = entry['project']['project_id']
		site = entry['project']['primary_site']
		case = entry['case_id']
		gender = entry['demographic']['gender']
		
		outputfile.write(("%s\t%s\t%s\t%s\n") % (project,site,case,gender))
	
	outputfile.close()
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--inputfile", required = True, help = "JSON file from GDC")
	parser.add_argument("-o", "--outputfile", required = True, help = "File to save")
	args = parser.parse_args()
	
	main(args)

