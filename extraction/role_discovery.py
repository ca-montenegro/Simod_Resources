# -*- coding: utf-8 -*-
from itertools import groupby

import scipy
from scipy.stats import pearsonr
import networkx as nx
import matplotlib.pyplot as plt
from support_modules import support as sup
from operator import itemgetter
import random
import numpy as np


# == support
def random_color(size):
    number_of_colors = size
    color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(number_of_colors)]
    return color

def find_index(dictionary, value):
    finish = False
    i = 0
    resp = -1
    while i<len(dictionary) and not finish:
        if dictionary[i]['data']==value:
            resp = dictionary[i]['index']
            finish = True
        i+=1
    return resp

def det_freq_matrix(unique, dictionary):
    freq_matrix = list()
    for u in unique:
        freq = 0
        for d in dictionary:
            if u == d:
                freq += 1
        freq_matrix.append(dict(task=u[0],user=u[1],freq=freq))
    return freq_matrix

def det_Act_freq_matrix(dictionary,usersLen):
    freq_matrix = dict()
    for vals in dictionary:
        userindex = vals[1]
        taskindex = vals[0]
        if taskindex in freq_matrix:
            count = freq_matrix[taskindex][userindex]
            count += 1
            freq_matrix[taskindex][userindex] = count
        else:
            taskis = [0, ] * usersLen
            taskis[userindex] = 1
            freq_matrix[taskindex] = taskis
    return freq_matrix

def get_tasks_by_k_users(freq_matrix,k=1):
    taskResources = list()
    for taskRes in freq_matrix:
        resour = freq_matrix[taskRes]
        if k > len(resour):
            k = len(resour) - 1
        highest_values = np.full(k,0)
        highest_index = np.full(k,-1)
        for key,val in enumerate(resour):
            if (val > np.min(highest_values)):
                highest_index[np.argmin(highest_values)] = key
                highest_values[np.argmin(highest_values)] = val
        taskResources.append(dict(task = taskRes, resources = highest_index, quantity = highest_values))
    return taskResources

def users_definition(tasks_by_user,users,tasks):
    taskResourcesNames = list()
    for task in tasks_by_user:
        names = list()
        for resource in task['resources']:
            if resource!=-1:
                name = users[resource]['data']
                names.append(name)
            else:
                name = 'None'
                #names.append(name)
        taskName = tasks[task['task']]['data']
        taskResourcesNames.append(dict(idTask = task['task'],task=taskName,resource = names, quantity = task['quantity'],lenRole = len(names) ))
    return taskResourcesNames

def build_profile(users,freq_matrix,prof_size):
    profiles=list()
    for user in users:
        exec_tasks = list(filter(lambda x: x['user']==user['index'],freq_matrix))
        profile = [0,] * prof_size
        for exec_task in exec_tasks:
            profile[exec_task['task']]=exec_task['freq']
        profiles.append(dict(user=user['index'],profile=profile))
    return profiles

def det_correlation_matrix(profiles):
    correlation_matrix = list()
    for profile_x in profiles:
        for profile_y in profiles:
            x = scipy.array(profile_x['profile'])
            y = scipy.array(profile_y['profile'])
            r_row, p_value = pearsonr(x, y)
            correlation_matrix.append(dict(x=profile_x['user'],y=profile_y['user'],distance=r_row))
    return correlation_matrix

# =============================================================================
# def graph_network(g):
#     pos = nx.spring_layout(g, k=0.5,scale=10)
#     nx.draw_networkx(g,pos,node_size=200,with_labels=True,font_size=11, font_color='#A0CBE2')
#     edge_labels=dict([((u,v,),round(d['weight'],2)) for u,v,d in g.edges(data=True)])
#     nx.draw_networkx_edge_labels(g,pos,edge_labels=edge_labels)
#     plt.draw()
#     plt.show()
# 
# =============================================================================
def graph_network(g, sub_graphs):
    #IDEA se debe calcular el centroide de los clusters....pos es un diccionario de posiciones y el centroide es el promedio de los puntos x y y
    #despues se debe determinar el punto mas lejano del centroide y ese sera el radio y con esos datos pintar un circulo con patches
    pos = nx.spring_layout(g, k=0.5,scale=10)
    color = random_color(len(sub_graphs))
    for i in range(0,len(sub_graphs)):
        subgraph = sub_graphs[i]
        nx.draw_networkx_nodes(g,pos, nodelist=list(subgraph), node_color=color[i], node_size=200, alpha=0.8)
        nx.draw_networkx_edges(g,pos,width=1.0,alpha=0.5)
        nx.draw_networkx_edges(g,pos, edgelist=subgraph.edges, width=8,alpha=0.5,edge_color=color[i])
    plt.draw()
    plt.show() # display


def role_definition(sub_graphs,users,taskResourcesNames,data,quantity_by_cost=0,reverse_cost=False):
    records = list()
    if sub_graphs!=None:
        for i in range(0,len(sub_graphs)):
            users_names = list()
            for user in sub_graphs[i]:
                users_names.append(list(filter(lambda x: x['index']==user,users))[0]['data'])
            records.append(dict(role='Role '+ str(i + 1),quantity =len(sub_graphs[i]),members=users_names))
        #Sort roles by number of resources
        records = sorted(records, key=itemgetter('quantity'), reverse=True)
        for i in range(0,len(records)):
            records[i]['role']='Role '+ str(i + 1)
            sum_costxhour = 0
            for mem in records[i]['members']:
              sum_costxhour += int(list(filter(lambda x:x[1]==mem,data))[0][2])
            records[i]['avg_costxhour'] = sum_costxhour/len(records[i]['members'])
        resource_table = list()
        for record in records:
            for member in record['members']:
                diff_time = 0
                registers = list(filter(lambda x:x[1]==member,data))
                for register in registers:
                    diff_time+=register[3].total_seconds()
                resource_table.append(dict(role=record['role'], resource=member,costxhour=int(list(filter(lambda x:x[1]==member,data))[0][2]),avg_costxhour=record['avg_costxhour'],dif_timestamp=diff_time))
        if quantity_by_cost>0:
            resource_table_group_by_role = groupby(resource_table, key=itemgetter('role'))
            temp = []
            for role,members in resource_table_group_by_role:
                members = sorted(members,key=itemgetter('costxhour'),reverse=reverse_cost)
                for mem in members[:quantity_by_cost]:
                    temp.append(mem)
            resource_table = temp
        return records, resource_table
    elif taskResourcesNames!=None:
        for i in range(0,len(taskResourcesNames)):
            taskResourcesNames[i]['role']='Role '+str(i+1)
            sum_costxhour = 0
            for mem in taskResourcesNames[i]['resource']:
                sum_costxhour += int(list(filter(lambda x: x[1] == mem, data))[0][2])
            taskResourcesNames[i]['avg_costxhour'] = sum_costxhour / len(taskResourcesNames[i]['resource'])
        resource_table = list()
        for taskRes in taskResourcesNames:
            quantity = 0
            for member in taskRes['resource']:
                if member != 'None':
                    quantity+=1
                    diff_time = 0
                    registers = list(filter(lambda x: x[1] == member, data))
                    for register in registers:
                        diff_time += register[3].total_seconds()
                    resource_table.append(dict(role=taskRes['role'],resource=member,avg_costxhour = taskRes['avg_costxhour'],costxhour=int(list(filter(lambda x:x[1]==member,data))[0][2]),dif_timestamp=diff_time))
        if quantity_by_cost>0:
            print(quantity_by_cost)
            print(resource_table)
            resource_table_group_by_role = groupby(resource_table, key=itemgetter('role'))
            temp = []
            for role,members in resource_table_group_by_role:
                print(role)
                print(members)
                members = sorted(members,key=itemgetter('costxhour'),reverse=reverse_cost)
                print(members)
                for mem in members[:quantity_by_cost]:
                    temp.append(mem)
            print(temp)
            resource_table = temp
        return taskResourcesNames,resource_table


# --kernel--

def role_discovery(data, drawing, sim_percentage,quantity_by_cost,reverse_cost):
    datos = map(lambda x: x[0], data)
    tasks = list(set(list(datos)))
    try:
        tasks.remove('Start')
    except Exception:
    	pass
    tasks = [dict(index=i,data=tasks[i]) for i in range(0,len(tasks))]
    users = list(set(list(map(lambda x: x[1], data))))
    try:
        users.remove('Start')
    except Exception:
    	pass
    users = [dict(index=i,data=users[i]) for i in range(0,len(users))]
    data_transform = list(map(lambda x: [find_index(tasks, x[0]),find_index(users, x[1])], data ))
    unique = list(set(tuple(i) for i in data_transform))
    unique = [list(i) for i in unique]
    # [print(uni) for uni in users]
    # building of a task-size profile of task execution per resource
    profiles = build_profile(users,det_freq_matrix(unique,data_transform),len(tasks))
    sup.print_progress(((20 / 100)* 100),'Analysing resource pool ')
    # building of a correlation matrix between resouces profiles
    correlation_matrix = det_correlation_matrix(profiles)
    sup.print_progress(((40 / 100)* 100),'Analysing resource pool ')
    # creation of a relation network between resouces
    g = nx.Graph()
    for user in users:
        g.add_node(user['index'])
    for relation in correlation_matrix:
        # creation of edges between nodes excluding the same element correlation
        # and those below the 0.7 threshold of similarity
        if relation['distance'] > sim_percentage and relation['x']!=relation['y'] :
            g.add_edge(relation['x'],relation['y'],weight=relation['distance'])
    sup.print_progress(((60 / 100)* 100),'Analysing resource pool ')
    # extraction of fully conected subgraphs as roles
    sub_graphs = list(nx.connected_component_subgraphs(g))
    sup.print_progress(((80 / 100)* 100),'Analysing resource pool ')
    # role definition from graph
    roles = role_definition(sub_graphs,users, taskResourcesNames = None,data = data,quantity_by_cost=quantity_by_cost,reverse_cost=reverse_cost)
    # plot creation (optional)
    if drawing == True:
        graph_network(g, sub_graphs)
    sup.print_progress(((100 / 100)* 100),'Analysing resource pool ')
    sup.print_done_task()
    return roles

def role_freqAct_discovery(data,k,quantity_by_cost,reverse_cost):
    datos = map(lambda x: x[0], data)
    tasks = list(set(list(datos)))
    try:
        tasks.remove('Start')
    except Exception:
        pass
    tasks = [dict(index=i, data=tasks[i]) for i in range(0, len(tasks))]
    users = list(set(list(map(lambda x: x[1], data))))
    try:
        users.remove('Start')
    except Exception:
        pass
    sup.print_progress(((20 / 100) * 100), 'Analysing resource pool by task frequency')
    users = [dict(index=i, data=users[i]) for i in range(0, len(users))]
    sup.print_progress(((40 / 100) * 100), 'Analysing resource pool by task frequency')
    data_transform = list(map(lambda x: [find_index(tasks, x[0]), find_index(users, x[1])], data))
    #unique = list(set(tuple(i) for i in data_transform))
    #unique = [list(i) for i in unique]
    # [print(uni) for uni in users]
    # building of a task-size profile of task execution per resource
    sup.print_progress(((60 / 100) * 100), 'Analysing resource pool by task frequency ')
    freq_matrix = det_Act_freq_matrix(data_transform,len(users))
    sup.print_progress(((80 / 100) * 100), 'Analysing resource pool by task frequency ')
    tasks_by_user = get_tasks_by_k_users(freq_matrix,k)
    taskResourcesNames = users_definition(tasks_by_user,users,tasks)
    roles = role_definition(sub_graphs=None,users=users,taskResourcesNames=taskResourcesNames,data=data,quantity_by_cost=quantity_by_cost,reverse_cost=reverse_cost)
    sup.print_progress(((100 / 100) * 100), 'Analysing resource pool by task frequency ')
    sup.print_done_task()
    return roles


def cost(elem):
    return elem['data'][0][2]

def role_discovery_high_cost(data,quantity_cost):
    datos = map(lambda x: x[0], data)
    tasks = list(set(list(datos)))
    try:
        tasks.remove('Start')
    except Exception:
        pass
    tasks = [dict(index=i, data=tasks[i]) for i in range(0, len(tasks))]
    users = list(set(list(map(lambda x: [x[1],x[2]], data))))
    users = [dict(index=i, data=users[i]) for i in range(0, len(users))]
    try:
        users.remove('Start')
    except Exception:
        pass
    users.sort(key=cost)

def read_roles_from_columns(raw_data, filtered_data, separator):
	records = list()
	role_list= list()
	pool_list= list()
	raw_splited= list()
	for row in raw_data:
		temp = row.split(separator)
		if temp[0] != 'End':
			raw_splited.append(dict(role=temp[1],resource=temp[0]))
	for row in filtered_data:
		temp = row.split(separator)
		if temp[0] != 'End':
			pool_list.append(dict(role=temp[1],resource=temp[0]))
			role_list.append(temp[1])
	role_list = list(set(role_list))
	for role in role_list:
		members = list(filter(lambda person: person['role'] == role, pool_list))
		members = list(map(lambda x: x['resource'],members))
		quantity = len(members)
		#freq = len(list(filter(lambda person: person['role'] == role, raw_splited)))
		records.append(dict(role=role,quantity =quantity,members=members))
	return records

def read_resource_pool(log, separator=None, drawing=False, sim_percentage=0.0,k=0,quantity_by_cost=0,reverse_cost=0,happy_path=False):
    if separator == None and k == 0:
        filtered_list = list()
        if happy_path:
            for row in log:
                if row['task'] != 'End' and row['user'] != 'AUTO':
                    filtered_list.append([row['task'],row['user'],row['costxhour'],row['dif_timestamp']])
        else:
            for row in log.data:
                if row['task'] != 'End' and row['user'] != 'AUTO':
                    filtered_list.append([row['task'],row['user'],row['costxhour'],row['dif_timestamp']])
        return role_discovery(filtered_list, drawing, sim_percentage,quantity_by_cost,reverse_cost=reverse_cost)
    elif separator == None and k > 0:
        filtered_list = list()
        if happy_path:
            for row in log:
                if row['task'] != 'End' and row['user'] != 'AUTO':
                    filtered_list.append([row['task'], row['user'],row['costxhour'],row['dif_timestamp']])
        else:
            for row in log.data:
                if row['task'] != 'End' and row['user'] != 'AUTO':
                    filtered_list.append([row['task'], row['user'],row['costxhour'],row['dif_timestamp']])
        return role_freqAct_discovery(filtered_list,k,quantity_by_cost,reverse_cost=reverse_cost)
    else:
        raw_list = list()
        filtered_list = list()
        for row in log.data:
            raw_list.append(row['user'])
        filtered_list = list(set(raw_list))
        return read_roles_from_columns(raw_list, filtered_list, separator)
