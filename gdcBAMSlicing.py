#!/usr/bin/python
import argparse
import datetime
import time
import os
import pprint
import requests
import json


def getAuthToken(tokenfilename):
	tokenfile = open(tokenfilename,"r")
	token = tokenfile.readline() 
	tokenfile.close()
	return token

def sliceByGene(token, gene, bamfileid, outputfile, loghandle):
	baseURL = "https://gdc-api.nci.nih.gov/slicing/view/"

	#Set up the headers
	headers = {
		"X-Auth-Token" : token,
		"Content-Type" : "application/json"
	}

	logIt(loghandle, headers)

	#Request a single gene
	requestJSON = {
		"hgnc" : [
			gene
		]
	}
	logIt(loghandle, requestJSON)

	#Append the bam file ID to create the request
	url = baseURL + bamfileid
	logIt(loghandle,url)

	runQuery(url, headers, queryJSON, outputfile, loghandle)

def sliceByRange(token, genomerange, bamfileid, outputfile, loghandle):
	baseURL = "https://gdc-api.nci.nih.gov/slicing/view/"
        #Set up the headers
        headers = {
                "X-Auth-Token" : token,
                "Content-Type" : "application/json"
        }

	#Set up query
	queryJSON = {
		"regions" : [ genomerange ]
	}

	url = baseURL + bamfileid
        logIt(loghandle,url)

	runQuery(url, headers, queryJSON, outputfile, loghandle)

def runQuery(url, headers, query, outputfile, loghandle):
	#Make the Request
        #http://docs.python-requests.org/en/master/user/advanced/
        #http://stackoverflow.com/questions/10768522/python-send-post-with-header
        logIt(loghandle,"Starting request")
        data = requests.post(url, headers=headers, data=json.dumps(query))
        logIt(loghandle,("Request Complete Status Code: %s" % str(data.status_code)))
        #write the data to a file
        logIt(loghandle,("Writing data to %s" % outputfile))
        outfile = open(outputfile,"w")
        outfile.write(data.content)
        logIt(loghandle, "Writing done")
        outfile.close()

def vPrint(doit, message):
	if doit:
		pprint.pprint(message)

def logIt(filehandle, logtext):
	now = datetime.datetime.now()
	timestamp = "%s-%s-%s_%s:%s:%s" % (now.month, now.day, now.year, now.hour, now.minute, now.second)
	filehandle.write(("%s\t%s\n") % (timestamp, logtext))

def main(args):
	#Get start time to measure how long the whole process takes
	starttime = time.time()
	vPrint(args.verbose,str(starttime))

	#Create the log file
	if args.logfile is not None:
		filename = args.logfile
	else:
		now = datetime.datetime.now()
		filename = "%s_%s_%s_gdc-log.tsv" % (now.month, now.day, now.year)

	log_header = "Timestamp\tMessage\n"
	vPrint(args.verbose,("Log file: %s" % (filename)))

	if os.path.isfile(filename):
		logfile = open(filename, "a")
	else:
		logfile = open(filename,"w")
	logfile.write(log_header)

	#Get the authorization token
	gdctoken = getAuthToken(args.token)
	vPrint(args.verbose,gdctoken)
	logIt(logfile, gdctoken)

	#Test BAM File
	testbamfileid = '9419c6a0-48cb-4db5-a3cb-357ad56aba20'

	if args.genename is not None:
		sliceByGene(gdctoken, args.genename, testbamfileid, args.bamfilename, logfile)
	elif args.range is not None:
		sliceByRange(gdctoken, args.range, testbamfileid, args.bamfilename, logfile)
	else:
		print "No gene or range specified, aborting"
		logIt(logfile,"No gene or range specified")

	elapsedtime = str(datetime.timedelta(seconds = (time.time() - starttime)))

	logIt(logfile, ("Elapsed time: %s" % str(elapsedtime)))
	logfile.close()




if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback.')
	parser.add_argument("-l", "--logfile", nargs = '?', const = None, help="Log file.  Will default to gdc-log.txt if left blank")
	parser.add_argument("-g", "--genename", nargs = '?', const = None, help="Name of the gene to slice")
	parser.add_argument("-r", "--range", nargs = '?', const = None, help="Genomic range to slice (chr:start-end)")
	parser.add_argument("-b", "--bamfilename", required = True, help = "Name for the output bam file")
	parser.add_argument("-t","--token", nargs = '?', required = True, help = "GDC Authoriation Token file")

	args = parser.parse_args()
	main(args)

