# -*- coding: utf-8 -*-
import uuid
from lxml import etree
from lxml.builder import ElementMaker # lxml only !
import pandas as pd
import xml.etree.ElementTree as ET

import os
import re

# print(uuid.uuid4())

#--------------- General methods ----------------
def create_file(output_file, element):
	file_exist = os.path.exists(output_file)
	with open(output_file, 'wb') as f:
		f.write(element)
	f.close()

#-------------- kernel --------------

def xml_templateConfig(arrival_rate, time_table, resource_pool, elements_data, sequences,instances):
	# TODO: avgCost of resources for the default cost
	E = ElementMaker(namespace="http://bsim.hpi.uni-potsdam.de/scylla/simModel",
					 nsmap={'bsim': "http://bsim.hpi.uni-potsdam.de/scylla/simModel"})
	GLOBALCONFIGURATION = E.globalConfiguration
	RESOURCEASSIGNMENTORDER = E.resourceAssignmentOrder
	RANDOMSEED = E.randomSeed
	ZONEOFFSET = E.zoneOffset
	TIMETABLES = E.timetables
	TIMETABLE = E.timetable
	TIMETABLEITEM = E.timetableItem
	RESOURCEDATA = E.resourceData
	DYNAMICRESOURCE = E.dynamicResource
	INSTANCE = E.instance

	rootid = 'GlobalConf_' + str(uuid.uuid4())
	randomSeed = 3096

	print(resource_pool)
	print()
	print(resource_pool[0]['instances'])

	my_doc = GLOBALCONFIGURATION(
		RESOURCEASSIGNMENTORDER("priority,simulationTime"),
		RANDOMSEED(str(randomSeed)),
		TIMETABLES(*[
			TIMETABLE(
				TIMETABLEITEM(from_=table['from_w'],
							  to=table['to_w'],
							  beginTime=table['from_t'],
							  endTime=table['to_t']),
				id=table['id_t']) for table in time_table
		]),
		RESOURCEDATA(*[
			DYNAMICRESOURCE(id=resource['id'],
							name=resource['name'],
							defaultQuantity=resource['total_amount'],
							defaultCost=str(resource['avg_costxhour']),
							defaultTimetableId=resource['timetable_id'],
							defaultTimeUnit='SECONDS',
											* [INSTANCE(name=instance['resource'], timetableId=resource['timetable_id'],
														cost=instance['costxhour']) for instance in
											   resource['instances']]
							) for resource in resource_pool
		]),
		id=rootid, targetNamespace="http://www.hpi.de"
	)
	return my_doc

def verifyArrivalRate(arrival_rate):
	E = ElementMaker(namespace="http://bsim.hpi.uni-potsdam.de/scylla/simModel",
					 nsmap={'bsim': "http://bsim.hpi.uni-potsdam.de/scylla/simModel"})
	NORMALDISTRIBUTION = E.normalDistribution
	EXPONENTIALDISTRIBUTION = E.exponentialDistribution
	UNIFORMDISTRIBUTION = E.uniformDistribution
	TRIANGULARDISTRIBUTION = E.triangularDistribution
	ERLANGDISTRIBUTION = E.erlangDistribution
	CONSTANTDISTRIBUTION = E.constantDistribution
	BINOMIALDISTRIBUTION = E.binomialDistribution
	ORDER = E.order
	MEAN = E.mean
	LOWER = E.lower
	UPPER = E.upper
	PEAK = E.peak
	STANDARDDEVIATION = E.standardDeviation
	CONSTANTVALUE = E.constantValue
	PROBABILITY = E.probability
	AMOUNT = E.amount
	type = arrival_rate['dname']
	if(type=='normalDistribution'):
		return NORMALDISTRIBUTION(
			MEAN(str(arrival_rate['dparams']['mean'])),
			STANDARDDEVIATION(str(arrival_rate['dparams']['arg1']))
		)
	elif(type=='exponentialDistribution'):
		return EXPONENTIALDISTRIBUTION(
			MEAN(str(arrival_rate['dparams']['mean']))
		)
	elif(type=='uniformDistribution'):
		return UNIFORMDISTRIBUTION(
			LOWER(str(arrival_rate['dparams']['arg1'])),
			UPPER(str(arrival_rate['dparams']['arg2']))
		)
	elif(type=='triangularDistribution'):
		return TRIANGULARDISTRIBUTION(
			LOWER(str(arrival_rate['dparams']['arg1'])),
			UPPER(str(arrival_rate['dparams']['arg2'])),
			PEAK(str(arrival_rate['dparams']['mean']))
		)
	elif(type=='erlangDistribution'):
		return ERLANGDISTRIBUTION(
			ORDER(str(arrival_rate['dparams']['arg1'])),
			MEAN(str(arrival_rate['dparams']['mean']))
		)
	elif (type == 'constantDistribution'):
		return CONSTANTDISTRIBUTION(
			CONSTANTVALUE(str(arrival_rate['dparams']['mean']))
		)
	elif (type == 'binomialDistribution'):
		return BINOMIALDISTRIBUTION(
			PROBABILITY(str(arrival_rate['dparams']['mean'])),
			AMOUNT(str(arrival_rate['dparams']['arg1']))
		)
	elif (type == 'binomialDistribution'):
		return BINOMIALDISTRIBUTION(
			PROBABILITY(str(arrival_rate['dparams']['mean'])),
			AMOUNT(str(arrival_rate['dparams']['arg1']))
		)
	#TO-do

def verifyDistribution(element_data):
	E = ElementMaker(namespace="http://bsim.hpi.uni-potsdam.de/scylla/simModel",
					 nsmap={'bsim': "http://bsim.hpi.uni-potsdam.de/scylla/simModel"})
	NORMALDISTRIBUTION = E.normalDistribution
	EXPONENTIALDISTRIBUTION = E.exponentialDistribution
	UNIFORMDISTRIBUTION = E.uniformDistribution
	TRIANGULARDISTRIBUTION = E.triangularDistribution
	ERLANGDISTRIBUTION = E.erlangDistribution
	CONSTANTDISTRIBUTION = E.constantDistribution
	ORDER = E.order
	MEAN = E.mean
	LOWER = E.lower
	UPPER = E.upper
	PEAK = E.peak
	STANDARDDEVIATION = E.standardDeviation
	CONSTANTVALUE = E.constantValue
	type = element_data['type']
	if (type == 'normalDistribution'):
		return NORMALDISTRIBUTION(
			MEAN(str(element_data['mean'])),
			STANDARDDEVIATION(str(element_data['arg1']))
		)
	elif (type == 'exponentialDistribution'):
		return EXPONENTIALDISTRIBUTION(
			MEAN(str(element_data['mean']))
		)
	elif (type == 'uniformDistribution'):
		return UNIFORMDISTRIBUTION(
			LOWER(str(element_data['arg1'])),
			UPPER(str(element_data['arg2']))
		)
	elif (type == 'triangularDistribution'):
		return TRIANGULARDISTRIBUTION(
			LOWER(str(element_data['arg1'])),
			UPPER(str(element_data['arg2'])),
			PEAK(str(element_data['mean']))
		)
	elif (type == 'erlangDistribution'):
		return ERLANGDISTRIBUTION(
			ORDER(str(element_data['arg1'])),
			MEAN(str(element_data['mean']))
		)
	elif (type == 'constantDistribution'):
		return CONSTANTDISTRIBUTION(
			CONSTANTVALUE(str(element_data['mean']))
		)

def outgoingFlow(arr):
	E = ElementMaker(namespace="http://bsim.hpi.uni-potsdam.de/scylla/simModel",
					 nsmap={'bsim': "http://bsim.hpi.uni-potsdam.de/scylla/simModel"})
	OUTGOINGSEQUENCEFLOW = E.outgoingSequenceFlow
	BRANCHINGPROBABILITY = E.branchingProbability
	EXCLUSIVEGATEWAY = E.exclusiveGateway

	#return EXCLUSIVEGATEWAY(
	#	*[
	#		OUTGOINGSEQUENCEFLOW(
	#			BRANCHINGPROBABILITY(element['prob']),
	#			id=element['elementid']
	#		)
	#	] for element in arr
	#)

def xml_templateSimulation(arrival_rate, time_table, resource_pool, elements_data, sequences,bpmnId):
	E = ElementMaker(namespace="http://bsim.hpi.uni-potsdam.de/scylla/simModel", nsmap={'bsim' : "http://bsim.hpi.uni-potsdam.de/scylla/simModel"})
	DEFINITIONS = E.definitions
	SIMULATIONCONFIGURATION = E.simulationConfiguration
	PROCESSSIMULATIONINFO = E.globalConfiguration
	STARTEVENT = E.startEvent
	ARRIVALRATE = E.arrivalRate
	ARRIVALRATEDISTRIBUTION = E.arrivalRateDistribution
	PRIORITY = E.priority
	ORDER = E.order
	MEAN = E.mean
	LOWER = E.lower
	UPPER = E.upper
	PEAK = E.peak
	TASK = E.task
	ASSIGNMENTDEFINITION = E.assignmentDefinition
	TRIANGULARDISTRIBUTION = E.triangularDistribution
	ERLANGDISTRIBUTION = E.erlangDistribution
	EXPONENTIALDISTRIBUTION = E.exponentialDistribution
	DURATION = E.duration
	TIMEUNIT = E.timeUnit
	TIMETABLES = E.timetables
	TIMETABLE = E.timetable
	RULES = E.rules
	RULE = E.rule
	RESOURCES = E.resources
	RESOURCE = E.resource
	EXCLUSIVEGATEWAY = E.exclusiveGateway
	OUTGOINGSEQUENCEFLOW = E.outgoingSequenceFlow
	BRANCHINGPROBABILITY = E.branchingProbability
	ELEMENTS = E.elements
	ELEMENT = E.element

	RESOURCESIDS = E.resourceIds
	RESOURCESID = E.resourceId
	SEQUENCEFLOWS = E.sequenceFlows
	SEQUENCEFLOW = E.sequenceFlow

	rootid="qbp_"+str(uuid.uuid4())

	array_s = []

	for seq in sequences:
		encontro = False
		if (len(array_s) == 0):
			firstGt = []
			firstGt.append(seq)
			array_s.append(firstGt)
		else:
			for arr in array_s:
				if (arr[0]['gatewayid']==seq['gatewayid']):
					arr.append(seq)
					encontro=True
					break
			if (encontro == False):
				newArray = []
				newArray.append(seq)
				array_s.append(newArray)

	doc_simu = DEFINITIONS(
		SIMULATIONCONFIGURATION(
			*[
				TASK(
					DURATION(
						verifyDistribution(e),
						timeUnit="SECONDS"
					),
					RESOURCES(
						RESOURCE(
							id=str(e['resource']), amount="1")
					),
					id=e['elementid'], name=e['name']
				) for e in elements_data
			],
			*[EXCLUSIVEGATEWAY(
				*[
					OUTGOINGSEQUENCEFLOW(
						BRANCHINGPROBABILITY(str(element['prob'])),
						id = element['elementid']
					)for element in arr
				], id = arr[0]['gatewayid']
			)for arr in array_s

			],	# (EXCLUSIVEGATEWAY(
				# 	*[
				# 		OUTGOINGSEQUENCEFLOW(
				# 			BRANCHINGPROBABILITY(str(element['prob'])), id = element['elementid']
				# 		)for element in arr
				# 	], id = arr[0]['gatewayid']
				# ) for arr in array_s)

			STARTEVENT(
				ARRIVALRATE(
					verifyArrivalRate(arrival_rate), timeUnit = "SECONDS"
				)
				,id = arrival_rate['startEventId']
			),
			id = rootid,processRef = bpmnId, processInstances="225", startDateTime="2017-08-14T08:00:00.000Z", resourceAssignmentOrder="priority,simulationTime"
		),
		targetNamespace="http://www.hpi.de"
	)
	return doc_simu

def append_parameters(bpmn_input,my_doc):
	node=etree.fromstring(etree.tostring(my_doc, pretty_print=True))
	tree = etree.parse(bpmn_input)
	root = tree.getroot()
	froot= etree.fromstring(etree.tostring(root, pretty_print=True))
	froot.append(node)
	return froot

def create_resourceTable_file(output_file,resource_table,roles,flag,sim_percentage):
	if flag==1:
		title = ['Activity table: Activities grouped by K frequent resources']
		activityTable = pd.DataFrame(title)
		res = pd.DataFrame(resource_table)
		roles = pd.DataFrame(roles)
		activityTable = pd.concat([activityTable, roles, res])
		activityTable.to_csv(output_file.split('.')[0] + 'ActivityTable.csv')
	elif flag==2:
		title = ['Resource table: Resources grouped by tasks performed ' + str(sim_percentage)]
		resourcesTable = pd.DataFrame(title)
		res = pd.DataFrame(resource_table)
		roles = pd.DataFrame(roles)
		resourcesTable = pd.concat([resourcesTable, roles, res])
		resourcesTable.to_csv(output_file.split('.')[0] + 'ResourceTable.csv')


def print_parameters(bpmn_input, output_file, parameters, sim_percentage):
	# time_table = [
	# 	dict(id_t="QBP_DEFAULT_TIMETABLE",default="true",name="Default",from_t = "09:00",to_t="17:00",from_w="MONDAY",to_w="FRIDAY"),
	# 	dict(id_t="QBP_247_TIMETABLE",default="false",name="24/7",from_t = "00:00",to_t="23:59",from_w="MONDAY",to_w="SUNDAY")
	# 	]
	my_doc_gloConfig = xml_templateConfig(parameters['arrival_rate'], parameters['time_table'],
		parameters['resource_pool'], parameters['elements_data'], parameters['sequences'],parameters['instances'])
	my_doc_simu = xml_templateSimulation(parameters['arrival_rate'], parameters['time_table'],
		parameters['resource_pool'], parameters['elements_data'], parameters['sequences'], parameters['bpmnId'])
	#root = append_parameters(bpmn_input,my_doc)
	#output_file = str.split(output_file, '.')
	create_file(output_file.split('.')[0] + 'GlobalConfig.xml',
				etree.tostring(my_doc_gloConfig, pretty_print=True, xml_declaration=True))
	create_file(output_file.split('.')[0] + 'SimuConfig.xml',
				etree.tostring(my_doc_simu, pretty_print=True, xml_declaration=True))
	create_resourceTable_file(output_file, parameters['resource_table'], parameters['roles'], parameters['flag'],
							  sim_percentage)
	#create_file('..'+output_file[2]+'conf.'+output_file[3], etree.tostring(my_doc_gloConfig, pretty_print=True))
	#create_file('..'+output_file[2]+'simu.'+output_file[3], etree.tostring(my_doc_simu, pretty_print=True))
