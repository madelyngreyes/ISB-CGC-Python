#!/usr/bin/python
#Parse the CPTAC files into a tab delimited form suitable for loading BigQuery

import argparse
import pandas as pd
import os

#BQ Connections


##########################################
#
#   Parsing iTRAQ file stuff
##########################################
def getFileType(filename):
	fileType = "NA"
	allowedFileType = {"itraq.tsv":"itraq", "peptides.tsv":"peptides", "summary.tsv":"summary"}
	for fType in allowedFileType:
		if fType in filename:
			fileType = allowedFileType[fType] 
	return fileType
	
def getExperimentType(filename):
	experimentType = "NA"
	allowedExperimentType = ("Phosphoproteome", "Proteome", "Glycoproteome")
	for expType in allowedExperimentType:
		if expType in filename:
			experimentType = expType
	return experimentType 
	
def getVersion(filename):
	version = "r1"
	allowedVersions = ("r2", "r3")
	for aVersion in allowedVersions:
		if aVersion in filename:
			version = aVersion
	return version

def getStudy(filename):
	#If COAD, probably need to do a barcode check to see if COAD or READ
	study = "NA"
	allowedStudy = {"Breast": "TCGA-BRCA", "Colon": "TCGA-COAD", "Ovarian": "TCGA-OV"}
	for aStudy in allowedStudy:
		if aStudy in filename:
			study = allowedStudy[aStudy]
	return study
	
def getHeaders(filename):
	headers = []
	f = open(filename,"r")
	firstline = f.readline()
	firstline.strip()
	headers = firstline.split("\t")
	f.close
	return headers
	
def getGenes(filename):
	data = pd.read_csv(filename, sep = '\t', skiprows = (0,1,2))
	genes = data.iloc[:,0]
	return genes
	
def parseFile(filename, headers):
	finaldata = {}
	data = pd.read_csv(filename, sep = '\t', names = headers, skiprows = (0,1,2,3))
	i = 1
	while i < len(headers):
		row = data.loc[:,i]
		finaldata[headers[i]] = row
		i+=1
	return finaldata
	
def getColumnData(filename, index):
	data = pd.read_csv(filename, sep = '\t')
	columndata = data.loc[:,index]
	return columndata
	
def getSampleBarcode(shared,unshared):
	barcode = "Mismatch"
	temp1 = shared.split()
	temp2 = unshared.split()
	if temp1[0] == temp2[0]:
		barcode = "TGGA-" + temp1[0]
	return barcode
	

def vPrint(doit, message):
	if doit:
		print message
	
def main(args):
	fileType = getFileType(args.cptacfile)
	expType = getExperimentType(args.cptacfile)
	version = getVersion(args.cptacfile)
	study = getStudy(args.cptacfile)
	headers = getHeaders(args.cptacfile)
	numColumns = len(headers)
	genes = getGenes(args.cptacfile)
	description = getColumnData(args.cptacfile, 'Description')
	organism = getColumnData(args.cptacfile, 'Organism')
	chromosome = getColumnData(args.cptacfile, 'Chromosome')
	locus = getColumnData(args.cptacfile, 'Locus')
	
	headerlist = ["SampleBarcode","Study","ReportRevision","MeanLogRatio","MeanUnsharedLogRatio","MedianLogRatio","MedianUnsharedLogRatio",
	"StandardDeviationLogRatio","StandardDeviationUnsharedLogRatio","Gene","GeneLogRatio","GeneUnsharedLogRatio","Description","Organism",
	"Chromosome","Locus"]
	
	vPrint(args.verbose, "Opening output file")
	outfile = open(args.outputfile,"w")
	
	#Print a header only if verbose is specified
	if args.verbose:
		line = '\t'.join(headerlist)
		outfile.write(line + "\n")
		
	# i will track which column of the itraq speadsheet is being processed.  Skip the first (index 0) because it is gene names only
	# i will increment after each sample pair
	i=1
	#while i < numColumns:
	while i <= 3:
		#New sample, ne dataframe
		
		#Get the column header
		loglabel = headers[i].rstrip()
		
		#If the header isn't a barcode header, we want to ignore it.
		if loglabel not in headerlist:
			
			#iTRAQ files have paired columns (shared and unshared), so increment i to get the next column
			i +=1
			unsharedlabel = headers[i].rstrip()
			vPrint(args.verbose,("Shared:\t%s\tUnshared:\t%s" % (loglabel, unsharedlabel)))
			
			#Check that the paired columns have the same sample barcode and reformat to TCGA style
			sample = getSampleBarcode(loglabel, unsharedlabel)
			
			#Proceed if the barcodes from the column pairs match.  Bail if they don't
			if sample != 'Mismatch':
				
				#Get the data from the paired columns.  Each column has its own list
				logratio = getColumnData(args.cptacfile,loglabel)
				unsharedlog = getColumnData(args.cptacfile,unsharedlabel)
				vPrint(args.verbose,("Shared Size:\t%s\tUnshared Size:\t%s" % (str(len(logratio)), str(len(unsharedlog)))))
				
				#Now to start the printing
				genecount = 0
				while genecount < len(genes):
					row = []
					samplecount = 0
					row.append(sample)
					row.append(study)
					row.append(version)
					
					# The mean, median and std dev are the first three values in the lists and are constant for the entire sample.  Hardcode these.
					row.append(logratio[0]) #mean shared
					row.append(unsharedlog[0]) #mean unshared
					row.append(logratio[1]) #median shared
					row.append(unsharedlog[1]) #median unshared
					row.append(logratio[2]) #std dev shared
					row.append(unsharedlog[2]) #std dev unshared
					
					#The gene name and related data need to be incremented 
					row.append(genes[genecount]) #Gene name
					row.append(logratio[genecount + 3]) #shared gene value
					row.append(unsharedlog[genecount + 3]) #unshared gene value
					row.append(description[genecount + 3])
					row.append(organism[genecount + 3])
					row.append(chromosome[genecount + 3])
					row.append(locus[genecount+3])
					
					line = '\t'.join(str(item) for item in row)
					outfile.write(line + "\n")
					
					#On to the next gene
					genecount += 1
				
		else:
			#This causes non-sample columns to be ignored.  Those are handled elsewhere
			print "Else: " + loglabel

		#Increment to the next sample pair
		i+=1
	
	outfile.close()
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Parser for cptac2BQ program")
	parser.add_argument("-v", "--verbose", action = "store_true")
	parser.add_argument("-c", "--cptacfile", required = True, help = "Name of the file from CPTAC")
	parser.add_argument("-o", "--outputfile", required = True, help = "Name of the output file")
	
	args = parser.parse_args()
	
	main(args)
