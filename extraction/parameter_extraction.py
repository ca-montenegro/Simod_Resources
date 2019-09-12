# -*- coding: utf-8 -*-
from support_modules import support as sup
from extraction import log_replayer as rpl
from extraction import task_duration_distribution as td
from extraction import interarrival_definition as arr
from extraction import gateways_probabilities as gt
from extraction import role_discovery as rl
from extraction import schedule_tables as sch

import networkx as nx
import itertools

# -- Extract parameters --
def extract_parameters(log, bpmn, process_graph,flag,k,sim_percentage):
    if bpmn != None and log != None:
        bpmnId = bpmn.getProcessId()
        startEventId = bpmn.getStartEventId()
        # Creation of process graph
        #-------------------------------------------------------------------
        # Analysing resource pool LV917 or 247
        if(flag==1):
            roles, resource_table = rl.read_resource_pool(log,sim_percentage=0.0,k=k)
        elif(flag==2):
            roles, resource_table = rl.read_resource_pool(log, drawing=False, sim_percentage=sim_percentage)
        resource_pool, time_table, resource_table = sch.analize_schedules(resource_table, log, True, '247')
        #-------------------------------------------------------------------
        # Process replaying
        conformed_traces, not_conformed_traces, process_stats = rpl.replay(process_graph, log)
        # -------------------------------------------------------------------
        # Adding role to process stats
        for stat in process_stats:
            roleArray = list(filter(lambda x: x['resource']==stat['resource'],resource_table))
            if(roleArray!=[]):
                role = roleArray[0]['role']
            stat['role'] = role
            stat['diff_time_res'] = (stat['end_timestamp']-stat['start_timestamp']).total_seconds()

        for resource in resource_table:
            total_diff_time = 0
            statArray = list(filter(lambda x: x['resource']==resource['resource'],process_stats))
            if(statArray!=[]):
                for stat in statArray:
                    total_diff_time+=stat['diff_time_res']
            resource['diff_time_res'] = total_diff_time

        #-------------------------------------------------------------------
        # Determination of first tasks for calculate the arrival rate
        inter_arrival_times = arr.define_interarrival_tasks(process_graph, conformed_traces)
        arrival_rate_bimp = (td.get_task_distribution(inter_arrival_times, 50))
        arrival_rate_bimp['startEventId'] = startEventId
        #-------------------------------------------------------------------
        # Gateways probabilities 1=Historycal, 2=Random, 3=Equiprobable
        sequences = gt.define_probabilities(process_graph, bpmn, log, 1)
        #-------------------------------------------------------------------
        # Tasks id information
        elements_data = list()
        i = 0
        task_list = list(filter(lambda x: process_graph.node[x]['type']=='task' , list(nx.nodes(process_graph))))
        for task in task_list:
            task_name = process_graph.node[task]['name']
            task_id = process_graph.node[task]['id']
            values = list(filter(lambda x: x['task'] == task_name, process_stats))
            task_processing = [x['processing_time'] for x in values]
            dist = td.get_task_distribution(task_processing)
            max_role, max_count = '', 0
            role_sorted = sorted(values, key=lambda x:x['role'])
            for key2, group2 in itertools.groupby(role_sorted, key=lambda x:x['role']):
                group_count = list(group2)
                if len(group_count)>max_count:
                    max_count = len(group_count)
                    max_role = key2
            elements_data.append(dict(id=sup.gen_id(), elementid=task_id, type=dist['dname'],name = task_name,
                         mean=str(dist['dparams']['mean']), arg1=str(dist['dparams']['arg1']),
                         arg2=str(dist['dparams']['arg2']), resource=find_resource_id(resource_pool, max_role)))
            sup.print_progress(((i / (len(task_list) - 1)) * 100), 'Analysing tasks data ')
            i += 1
        sup.print_done_task()
        parameters = dict(arrival_rate=arrival_rate_bimp, time_table=time_table, resource_pool=resource_pool,
                              elements_data=elements_data, sequences=sequences, instances=len(conformed_traces),
                              bpmnId=bpmnId, resource_table=resource_table,roles=roles,flag=flag)
        return parameters, process_stats
#        return len(conformed_traces)/(len(conformed_traces)+ len(not_conformed_traces))

# --support --
def find_resource_id(resource_pool, resource_name):
    id = 0
    for resource in resource_pool:
        # print(resource)
        if resource['name'] == resource_name:
            id = resource['id']
            break
    return id
