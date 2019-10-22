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
import hashlib


# -- Extract parameters --
def extract_parameters(log, bpmn, process_graph, flag, k, sim_percentage, simulator, quantity_by_cost, reverse_cost,
                       happy_path=False):
    if bpmn != None and log != None:
        bpmnId = bpmn.getProcessId()
        startEventId = bpmn.getStartEventId()
        # Creation of process graph
        # -------------------------------------------------------------------
        # Analysing resource pool LV917 or 247
        if (flag == 1):
            roles, resource_table = rl.read_resource_pool(log, sim_percentage=0.0, k=k,
                                                          quantity_by_cost=quantity_by_cost, reverse_cost=reverse_cost,
                                                          happy_path=False)
        elif (flag == 2):
            roles, resource_table = rl.read_resource_pool(log, drawing=False, sim_percentage=sim_percentage,
                                                          quantity_by_cost=quantity_by_cost, reverse_cost=reverse_cost,
                                                          happy_path=False)
        # TODO: Create array of possible time tables based on the log and return so it can be print in the global config file for scylla
        resource_pool, time_table, resource_table = sch.analize_schedules(resource_table, log, True, 'LV917')
        # -------------------------------------------------------------------
        # Process replaying
        conformed_traces, not_conformed_traces, process_stats = rpl.replay(process_graph, log,
                                                                           resource_table=resource_table)
        # -------------------------------------------------------------------
        # Adding role to process stats
        for stat in process_stats:
            roleArray = list(filter(lambda x: x['resource'] == stat['resource'], resource_table))
            # print(roleArray)
            if (roleArray != []):
                role = roleArray[0]['role']
            stat['role'] = role
            # stat['diff_time_res'] = (stat['end_timestamp']-stat['start_timestamp']).total_seconds()
        if happy_path:
            hash_dict = dict()
            array_errors = []
            count_traces_dict = dict()
            for trace in conformed_traces:
                string_tasks = []
                task_ID_case = 0
                resource_list = list()
                for case in trace:
                    task_ID_case = case['caseid']
                    task_name_case = case['task']
                    resource_list.append(dict(caseid=task_ID_case, task=task_name_case, user=case['user'], costxhour=case['costxhour'],
                                 dif_timestamp=case['dif_timestamp']))
                    string_tasks.append(task_name_case)
                # string_tasks.append(task_ID_case)
                string_tasks = ",".join(string_tasks)
                hash_object_key = hashlib.md5(string_tasks.encode())
                # print(hash_object_key.hexdigest())
                if (hash_object_key.hexdigest() not in hash_dict):
                    hash_dict[hash_object_key.hexdigest()] = [dict(caseid=task_ID_case, resource_list=resource_list )]
                else:
                    hash_dict[hash_object_key.hexdigest()].append(dict(caseid=task_ID_case, resource_list=resource_list))
                if (hash_object_key.hexdigest() not in count_traces_dict):
                    count_traces_dict[hash_object_key.hexdigest()] = 1
                else:
                    count_traces_dict[hash_object_key.hexdigest()] += 1
            max_key = 0
            max_count = 0
            for k, v in count_traces_dict.items():
                if v > max_count:
                    max_count = v
                    max_key = k
            resources_list_happy = list()
            for cases in hash_dict[max_key]:
                for resources in cases['resource_list']:
                    resources_list_happy.append(
                        dict(case_id=resources['caseid'], task=resources['task'], user=resources['user'], costxhour=resources['costxhour'],
                             dif_timestamp=resources['dif_timestamp']))
            print(resources_list_happy)
            # resources_list_happy = list()
            # for trace in conformed_traces:
            #     if len(trace)==len(log.happy_path):
            #         for i,j in zip(trace, log.happy_path):
            #             if(i['task']!=j['task']):
            #                 resources_list_happy = list()
            #                 break
            #             resources_list_happy.append(dict(caseid = i['caseid'],task=i['task'],user=i['user'],costxhour=i['costxhour'],dif_timestamp=i['dif_timestamp']))
            # # Analysing resource pool LV917 or 247
            # if (flag == 1):
            #     roles, resource_table = rl.read_resource_pool(resources_list_happy, sim_percentage=0.0, k=k,
            #                                                   quantity_by_cost=quantity_by_cost,
            #                                                   reverse_cost=reverse_cost,happy_path=happy_path)
            # elif (flag == 2):
            #     roles, resource_table = rl.read_resource_pool(resources_list_happy, drawing=False,
            #                                                   sim_percentage=sim_percentage,
            #                                                   quantity_by_cost=quantity_by_cost,
            #                                                   reverse_cost=reverse_cost,happy_path=happy_path)
            # # TODO: Create array of possible time tables based on the log and return so it can be print in the global config file for scylla
            # resource_pool, time_table, resource_table = sch.analize_schedules(resource_table, log, True,
            #                                                                   'LV917')
            # # -------------------------------------------------------------------
            # # Process replaying
            # conformed_traces, not_conformed_traces, process_stats = rpl.replay(process_graph, log,
            #                                                                    resource_table=resource_table)
            # # -------------------------------------------------------------------
            # # Adding role to process stats
            # for stat in process_stats:
            #     roleArray = list(filter(lambda x: x['resource'] == stat['resource'], resource_table))
            #     # print(roleArray)
            #     if (roleArray != []):
            #         role = roleArray[0]['role']
            #     stat['role'] = role

        # for resource in resource_table:
        #     total_diff_time = 0
        #     statArray = list(filter(lambda x: x['resource']==resource['resource'],process_stats))
        #     if(statArray!=[]):
        #         for stat in statArray:
        #             total_diff_time+=stat['diff_time_res']
        #     resource['diff_time_res'] = total_diff_time

        # for key, group in itertools.groupby(resource_table, key=lambda x: x['role']):
        #     weight_sum_cost_hour = 0
        #     values = list(group)
        #     for val in values:
        #         weight_sum_cost_hour += ((float(val['diff_time_res'])/3600) * float(val['costxhour']))
        #     for val in values:
        #         val['weight_sum_cost_hour'] = weight_sum_cost_hour

        # -------------------------------------------------------------------
        # Determination of first tasks for calculate the arrival rate
        inter_arrival_times = arr.define_interarrival_tasks(process_graph, conformed_traces)
        for sim in simulator:
            if (sim == 'bimp'):
                arrival_rate_bimp = (td.get_task_distribution(inter_arrival_times, simulator=sim, bins=50))
                arrival_rate_bimp['startEventId'] = startEventId
            elif (sim == 'scylla'):
                arrival_rate_scylla = (td.get_task_distribution(inter_arrival_times, simulator=sim, bins=50))
                arrival_rate_scylla['startEventId'] = startEventId
        # -------------------------------------------------------------------
        # Gateways probabilities 1=Historycal, 2=Random, 3=Equiprobable
        sequences = gt.define_probabilities(process_graph, bpmn, log, 1)
        # -------------------------------------------------------------------
        # Tasks id information
        elements_data_scylla = list()
        elements_data_bimp = list()
        i = 0
        task_list = list(filter(lambda x: process_graph.node[x]['type'] == 'task', list(nx.nodes(process_graph))))
        for sim in simulator:
            for task in task_list:
                task_name = process_graph.node[task]['name']
                task_id = process_graph.node[task]['id']
                values = list(filter(lambda x: x['task'] == task_name, process_stats))
                task_processing = [x['processing_time'] for x in values]

                if (sim == 'bimp'):
                    dist_bimp = td.get_task_distribution(task_processing, simulator=sim)
                    max_role, max_count = '', 0
                    role_sorted = sorted(values, key=lambda x: x['role'])
                    for key2, group2 in itertools.groupby(role_sorted, key=lambda x: x['role']):
                        group_count = list(group2)
                        if len(group_count) > max_count:
                            max_count = len(group_count)
                            max_role = key2
                    elements_data_bimp.append(
                        dict(id=sup.gen_id(), elementid=task_id, type=dist_bimp['dname'], name=task_name,
                             mean=str(dist_bimp['dparams']['mean']), arg1=str(dist_bimp['dparams']['arg1']),
                             arg2=str(dist_bimp['dparams']['arg2']),
                             resource=find_resource_id(resource_pool, max_role)))
                    sup.print_progress(((i / (len(task_list) - 1)) * 100), 'Analysing tasks data ')
                elif (sim == 'scylla'):
                    dist_scylla = td.get_task_distribution(task_processing, simulator=sim)
                    max_role, max_count = '', 0
                    role_sorted = sorted(values, key=lambda x: x['role'])
                    for key2, group2 in itertools.groupby(role_sorted, key=lambda x: x['role']):
                        group_count = list(group2)
                        if len(group_count) > max_count:
                            max_count = len(group_count)
                            max_role = key2
                    elements_data_scylla.append(
                        dict(id=sup.gen_id(), elementid=task_id, type=dist_scylla['dname'], name=task_name,
                             mean=str(dist_scylla['dparams']['mean']), arg1=str(dist_scylla['dparams']['arg1']),
                             arg2=str(dist_scylla['dparams']['arg2']),
                             resource=find_resource_id(resource_pool, max_role)))
                    sup.print_progress(((i / (len(task_list) - 1)) * 100), 'Analysing tasks data ')
                i += 1
        sup.print_done_task()
        parameters = dict()
        for sim in simulator:
            if sim == 'bimp':
                parameters_bimp = dict(arrival_rate=arrival_rate_bimp, time_table=time_table,
                                       resource_pool=resource_pool,
                                       elements_data=elements_data_bimp, sequences=sequences,
                                       instances=len(conformed_traces),
                                       bpmnId=bpmnId, resource_table=resource_table, roles=roles, flag=flag)
                parameters['bimp'] = parameters_bimp
            elif sim == 'scylla':
                parameters_scylla = dict(arrival_rate=arrival_rate_scylla, time_table=time_table,
                                         resource_pool=resource_pool,
                                         elements_data=elements_data_scylla, sequences=sequences,
                                         instances=len(conformed_traces),
                                         bpmnId=bpmnId, resource_table=resource_table, roles=roles, flag=flag)
                parameters['scylla'] = parameters_scylla
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
