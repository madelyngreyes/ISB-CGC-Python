#!/usr/bin/python
import argparse
import datetime
import time
import os
import pprint


def getAuthToken(tokenfilename):
	tokenfile = open(tokenfilename,"r")
	token = tokenfile.readline() 
	tokenfile.close()
	return token

def sliceByGene(token, gene, bamfileid, outputfile):
	baseURL = "https://gdc-api.nci.nih.gov/slicing/view/"
	
	requestJSON = {
		"gencode" : [
			gene
		]
	} 
	
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
	
	elapsedtime = str(datetime.timedelta(seconds = (time.time() - starttime)))
	
	logIt(logfile, "Elapsed time: elapsedtime")
	logfile.close()




if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action = "store_true", help = 'Enable verbose feedback.')
	parser.add_argument("-l", "--logfile", nargs = '?', const = None , help="Log file.  Will default to gdc-log.txt if left blank")
	parser.add_argument("-t","--token", nargs = '?', required = True, help = "GDC Authoriation Token file")
	
	args = parser.parse_args()
	main(args)

