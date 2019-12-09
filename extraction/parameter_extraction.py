# -*- coding: utf-8 -*-
from support_modules import support as sup
from extraction import log_replayer as rpl
from extraction import task_duration_distribution as td
from extraction import interarrival_definition as arr
from extraction import gateways_probabilities as gt
from extraction import role_discovery as rl
from extraction import schedule_tables as sch
from support_modules.writers import xml_writer_scylla as xml_scylla

import networkx as nx
import itertools
import hashlib
import pandas as pd
import warnings
import matplotlib.pyplot as plt


# -- Extract parameters --
def extract_parameters(log, bpmn, process_graph, flag, k, sim_percentage, simulator, quantity_by_cost, reverse_cost,
                       happy_path=False, graph_roles_flag=False):
    if bpmn is not None and log is not None:
        bpmnId = bpmn.getProcessId()
        startEventId = bpmn.getStartEventId()
        # Creation of process graph
        # -------------------------------------------------------------------
        # Analysing resource pool LV917 or 247
        if flag == 1:
            roles, resource_table = rl.read_resource_pool(log, sim_percentage=0.0, k=k,
                                                          quantity_by_cost=quantity_by_cost, reverse_cost=reverse_cost,
                                                          happy_path=False)
        elif flag == 2:
            roles, resource_table = rl.read_resource_pool(log, drawing=False, sim_percentage=sim_percentage,
                                                          quantity_by_cost=quantity_by_cost, reverse_cost=reverse_cost,
                                                          happy_path=False)

        print("--- Initial Resource Pool ---")
        rolesdf = pd.DataFrame(columns=['Role', 'Quantity', 'Members'])
        for role in roles:
            if flag == 1:
                rolesdf = rolesdf.append(
                    {'Role': role['role'], 'Quantity': role['lenRole'], 'Members': role['resource']}, ignore_index=True)
            elif flag == 2:
                rolesdf = rolesdf.append(
                    {'Role': role['role'], 'Quantity': role['quantity'], 'Members': role['members']}, ignore_index=True)

        print(rolesdf.to_string())
        graph_roles = None
        graph_roles_new = None
        if graph_roles_flag:
            graph_roles = pd.DataFrame(columns=['Role', 'Member'])
            for role in roles:
                if flag == 1:
                    for member in role['resource']:
                        graph_roles = graph_roles.append({'Role': role['role'].split()[1], 'Member': member},
                                                         ignore_index=True)
                elif flag == 2:
                    for member in role['members']:
                        graph_roles = graph_roles.append({'Role': role['role'].split()[1], 'Member': member},
                                                         ignore_index=True)

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
        prev_roles = []
        prev_resource_table = []
        if happy_path:
            prev_roles = roles
            prev_resource_table = resource_table
            sup.print_performed_task('Discovering Happy Path ')
            hash_dict = dict()
            array_errors = []
            count_traces_dict = dict()
            i = 0
            for trace in conformed_traces:
                sup.print_progress(((i / (len(conformed_traces) - 1)) * 100), 'Discovering Happy Path ')
                string_tasks = []
                task_ID_case = 0
                resource_list = list()
                for case in trace:
                    task_ID_case = case['caseid']
                    task_name_case = case['task']
                    resource_list.append(
                        dict(caseid=task_ID_case, task=task_name_case, user=case['user'], costxhour=case['costxhour'],
                             dif_timestamp=case['dif_timestamp']))
                    string_tasks.append(task_name_case)
                # string_tasks.append(task_ID_case)
                string_tasks = ",".join(string_tasks)
                hash_object_key = hashlib.md5(string_tasks.encode())
                # print(hash_object_key.hexdigest())
                if hash_object_key.hexdigest() not in hash_dict:
                    hash_dict[hash_object_key.hexdigest()] = [
                        dict(caseid=task_ID_case, resource_list=resource_list, string_tasks=string_tasks)]
                else:
                    hash_dict[hash_object_key.hexdigest()].append(
                        dict(caseid=task_ID_case, resource_list=resource_list))
                if hash_object_key.hexdigest() not in count_traces_dict:
                    count_traces_dict[hash_object_key.hexdigest()] = 1
                else:
                    count_traces_dict[hash_object_key.hexdigest()] += 1
                i += 1
            max_key = 0
            max_count = 0
            for key, v in count_traces_dict.items():
                if v > max_count:
                    max_count = v
                    max_key = key
            resources_list_happy = list()
            if max_count == 1:
                print()
                warnings.warn("Happy Path impossible to discover: All traces are different", Warning)
            else:
                for cases in hash_dict[max_key]:
                    for resources in cases['resource_list']:
                        resources_list_happy.append(
                            dict(case_id=resources['caseid'], task=resources['task'], user=resources['user'],
                                 costxhour=resources['costxhour'],
                                 dif_timestamp=resources['dif_timestamp']))
                sup.print_done_task()
                print("Happy Path Discovered:")
                i = 1
                for taski in hash_dict[max_key][0]['string_tasks'].split(","):
                    print('Task', i, ':', taski)
                    i += 1

                # Analysing resource pool LV917 or 247
                if (flag == 1):
                    roles, resource_table = rl.read_resource_pool(resources_list_happy, sim_percentage=0.0, k=k,
                                                                  quantity_by_cost=quantity_by_cost,
                                                                  reverse_cost=reverse_cost, happy_path=happy_path)
                elif (flag == 2):
                    roles, resource_table = rl.read_resource_pool(resources_list_happy, drawing=False,
                                                                  sim_percentage=sim_percentage,
                                                                  quantity_by_cost=quantity_by_cost,
                                                                  reverse_cost=reverse_cost, happy_path=happy_path)

                print("--- Modified Resource Pool ---")
                rolesdf = pd.DataFrame(columns=['Role', 'Quantity', 'Members'])
                for role in roles:
                    if flag == 1:
                        rolesdf = rolesdf.append(
                            {'Role': role['role'], 'Quantity': role['lenRole'], 'Members': role['resource']},
                            ignore_index=True)
                    elif flag == 2:
                        rolesdf = rolesdf.append(
                            {'Role': role['role'], 'Quantity': role['quantity'], 'Members': role['members']},
                            ignore_index=True)

                if graph_roles_flag:
                    graph_roles_new = pd.DataFrame(columns=['Role', 'Member'])
                    for role in roles:
                        if flag == 1:
                            for member in role['resource']:
                                graph_roles_new = graph_roles_new.append(
                                    {'Role': role['role'].split()[1], 'Member': member},
                                    ignore_index=True)
                        elif flag == 2:
                            for member in role['members']:
                                graph_roles_new = graph_roles_new.append(
                                    {'Role': role['role'].split()[1], 'Member': member},
                                    ignore_index=True)

                print(rolesdf.to_string())
                # TODO: Create array of possible time tables based on the log and return so it can be print in the global config file for scylla
                resource_pool, time_table, resource_table = sch.analize_schedules(resource_table, log, True,
                                                                                  'LV917')
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
        role_not_set = find_resource_role(resource_pool, 'NOT_SET', True)
        task_list = list(filter(lambda x: process_graph.node[x]['type'] == 'task', list(nx.nodes(process_graph))))
        for sim in simulator:
            for task in task_list:
                task_name = process_graph.node[task]['name']
                task_id = process_graph.node[task]['id']
                values = list(filter(lambda x: x['task'] == task_name, process_stats))
                task_processing = [x['processing_time'] for x in values]

                if sim == 'bimp':
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
                elif sim == 'scylla':
                    dist_scylla = td.get_task_distribution(task_processing, simulator=sim)
                    if flag == 1:
                        role_per_task = list(filter(lambda x: x['task'] == task_name, roles))

                        if (len(role_per_task) > 0):
                            role_per_task = role_per_task[0]['role']
                            elements_data_scylla.append(
                                dict(id=sup.gen_id(), elementid=task_id, type=dist_scylla['dname'], name=task_name,
                                     mean=str(dist_scylla['dparams']['mean']), arg1=str(dist_scylla['dparams']['arg1']),
                                     arg2=str(dist_scylla['dparams']['arg2']),
                                     resource=find_resource_id(resource_pool, role_per_task)))
                        else:
                            # print(task_name)
                            continue
                    elif flag == 2:
                        max_role, max_count = '', 0
                        role_sorted = sorted(values, key=lambda x: x['role'])
                        filter1 = False
                        groupby_role = itertools.groupby(role_sorted, key=lambda x: x['role'])
                        counter = 0
                        max_role_not_set, max_count_not_set = '', 0
                        for key2, group2 in groupby_role:
                            group_count = list(group2)
                            if len(group_count) > max_count:
                                # any_resource = group_count[0]['resource']
                                if key2 == role_not_set:
                                    max_count_not_set = len(group_count)
                                    max_role_not_set = key2
                                    filter1 = True
                                else:
                                    max_count = len(group_count)
                                    max_role = key2
                                counter += 1
                        if counter == 1 and filter1 is True:
                            max_role = max_role_not_set
                            max_count = max_count_not_set
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
                                       bpmnId=bpmnId, resource_table=resource_table, roles=roles, flag=flag,
                                       prev_roles=prev_roles, prev_resource_table=prev_resource_table)
                parameters['bimp'] = parameters_bimp
            elif sim == 'scylla':
                parameters_scylla = dict(arrival_rate=arrival_rate_scylla, time_table=time_table,
                                         resource_pool=resource_pool,
                                         elements_data=elements_data_scylla, sequences=sequences,
                                         instances=len(conformed_traces),
                                         bpmnId=bpmnId, resource_table=resource_table, roles=roles, flag=flag,
                                         prev_roles=prev_roles, prev_resource_table=prev_resource_table,
                                         graph_roles=graph_roles, k=k, sim_percentage=sim_percentage,
                                         graph_roles_new=graph_roles_new)
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


def find_resource_role(resource_pool, resource_name, name):
    role = ''
    found = False
    for resource in resource_pool:
        for instance in resource['instances']:
            if instance['resource'] == resource_name:
                role = resource['name'] if name else resource['id']
                found = True
                break
        if found:
            break
    return role
