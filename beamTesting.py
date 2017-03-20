#!/usr/bin/python
#https://github.com/apache/beam/tree/master/sdks/python

import apache_beam as beam
import os
import time


project = 'cgc-05-0016'
input_table = 'isb-cgc.test.TCGA_Annotation'

filename = "names"
directory = "."


def runQuery():
	input_query = 'SELECT annotation_gdc_id, category, classification, status, entity_type, project_short_name, entity_barcode ' \
		'FROM `isb-cgc.test.TCGA_Annotation` ' \
		'WHERE classification = \'Observation\' ' \
		'LIMIT 10'
	
	p = beam.Pipeline(argv=['--project', project])
	(p 
		| 'read' >> beam.Read(beam.io.BigQuerySource(query=input_query)) 
		| 'save' >> beam.Write(beam.io.WriteToText('./beam_test.txt')))
	p.run()
	 
def beamBasic():
	p = beam.Pipeline('DirectRunner')
	(p
		| 'add names' >> beam.Create(['Larry', 'Curly', 'Moe'])
		| 'save' >> beam.io.WriteToText(directory +"/"+filename))
		
	p.run()
	
def beamMap():
	#The Github example is somewhat misleading.  The WriteToText as shown in the example doesn't save the 
	#filename, it adds an additional extention.  And that causes the later ReadFromText to not find the file
	#So when reading and writing files wtih Beam, you need to use exact file names.
	
	p = beam.Pipeline('DirectRunner')
	for file in os.listdir(directory):
		if file.startswith(filename):
			print file
			(p
				| 'load names' >> beam.io.ReadFromText(file)
				| 'add greeting' >> beam.Map(lambda names, msg: '%s, %s!' %(msg, names), 'Nyuk!')
				| 'save' >> beam.io.WriteToText('./greetings'))
			p.run()
			
def basicFlatmap():
	p = beam.Pipeline('DirectRunner')
	for file in os.listdir(directory):
		if file.startswith(filename):
			(p
				| 'load names' >> beam.io.ReadFromText(file)
				| 'add greetings' >> beam.FlatMap(
					lambda name, messages: ['%s %s!' % (msg,name) for msg in messages],
					['Nyuk', 'Soitanley'])
				| 'save' >> beam.io.WriteToText('./multi_greetings'))
			p.run()

def add_greetings(name, messages):
	for msg in messages:
		yield '%s %s#' % (msg,name)
		
def complexFlatMap():
	p = beam.Pipeline('DirectRunner')
	for file in os.listdir(directory):
		if file.startswith(filename):
			(p
				| 'load names' >> beam.io.ReadFromText(file)
				| 'add greetings' >> beam.FlatMap(add_greetings, ['Nyuk', 'Soitanley'])
				| 'save' >> beam.io.WriteToText('./complex_greetings'))
				
			p.run()
			
def main():
	#runQuery()
	print "Running beamBasic"
	beamBasic()
	#Need to sleep otherwise beamMap reads temporary files and blows up
	time.sleep(1)
	print "Running beamMap"
	beamMap()
	time.sleep(1)
	print "Running basicFlatMap"
	basicFlatmap()
	print "Running complexFlatMap"
	complexFlatMap()
	
if __name__ == '__main__':
	main()
