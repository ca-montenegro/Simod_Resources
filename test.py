# -*- coding: utf-8 -*-
"""
Created on Mon May 13 16:18:33 2019

@author: Manuel Camargo
"""

import sys
import re
import os
import subprocess
import configparser as cp
from shutil import copyfile

import pandas as pd
import numpy as np

from hyperopt import tpe
from hyperopt import Trials, hp, fmin, STATUS_OK, STATUS_FAIL

from support_modules import support as sup
#from support_modules.readers import log_reader as lr
from support_modules.readers import bpmn_reader as br
from support_modules.readers import process_structure as gph
from support_modules.writers import xml_writer as xml
from support_modules.writers import xml_writer_scylla as xml_scylla
from support_modules.analyzers import generalization as gen
from support_modules.log_repairing import conformance_checking as chk

from extraction import parameter_extraction as par
from extraction import log_replayer as rpl

from support_modules.readers import log_reader as lr
import simod as sim

#input_file='C:\\Users\\Manuel Camargo\\Documents\\Repositorio\\experiments\\sc_simo\\inputs\\PurchasingExample.xes.gz'



def mining_structure(settings, epsilon, eta):
    """Execute splitminer for bpmn structure mining.
    Args:
        settings (dict): Path to jar and file names
        epsilon (double): Parallelism threshold (epsilon) in [0,1]
        eta (double): Percentile for frequency threshold (eta) in [0,1]
    """
    print(" -- Mining Process Structure --")
    args = ['java', '-jar', settings['miner_path'],
            str(epsilon), str(eta),
            os.path.join(settings['output'], settings['file']),
            os.path.join(settings['output'], settings['file'].split('.')[0])]
    subprocess.call(args)
def simulate(settings, rep):
    """Executes BIMP Simulations.
    Args:
        settings (dict): Path to jar and file names
        rep (int): repetition number
    """
    print("-- Executing BIMP Simulations --")
    args = ['java', '-jar', settings['bimp_path'],
            os.path.join(settings['output'],
                         settings['file'].split('.')[0]+'.bpmn'),
            '-csv',
            os.path.join(settings['output'], 'sim_data',
                         settings['file'].split('.')[0]+'_'+str(rep+1)+'.csv')]
    subprocess.call(args)

def measure_stats(settings, bpmn, rep,resource_table):
    """Executes BIMP Simulations.
    Args:
        settings (dict): Path to jar and file names
        rep (int): repetition number
    """
    timeformat = '%Y-%m-%d %H:%M:%S.%f'
    temp = lr.LogReader(os.path.join(settings['output'], 'sim_data',
                                     settings['file'].split('.')[0] + '_'+str(rep + 1)+'.csv'),
                        timeformat)
    process_graph = gph.create_process_structure(bpmn)
    _, _, temp_stats = rpl.replay(process_graph, temp,resource_table=resource_table, source='simulation', run_num=rep + 1)
    temp_stats = pd.DataFrame.from_records(temp_stats)
    role = lambda x: x['resource']
    temp_stats['role'] = temp_stats.apply(role, axis=1)
    return temp_stats


def objective(params):
    for f in params['flag']:
        if f==1:
            for k in range(params['k'][0], params['k'][1] + 1):
                print('k = ' + str(k))
                settings = sim.read_settings(params)
                params['output'] = settings['output']
                # Output folder creation
                if not os.path.exists(settings['output']):
                    os.makedirs(settings['output'])
                    os.makedirs(os.path.join(settings['output'], 'sim_data'))
                copyfile(os.path.join(settings['input'], settings['file']),
                         os.path.join(settings['output'], settings['file']))
                log = lr.LogReader(os.path.join(settings['output'], settings['file']),
                                   settings['timeformat'])
                # Execution steps
                mining_structure(settings, params['epsilon'], params['eta'])
                bpmn = br.BpmnReader(os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + '.bpmn'))
                process_graph = gph.create_process_structure(bpmn)

                # Evaluate alignment
                # chk.evaluate_alignment(process_graph, log, settings)

                print("-- Mining Simulation Parameters --")
                parameters, process_stats = par.extract_parameters(log, bpmn, process_graph, flag=f, k=k,
                                                                   sim_percentage=0.0)
                xml.print_parameters(os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + '.bpmn'),
                                     os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + '.bpmn'),
                                     parameters,sim_percentage=0)

                response = dict()
                status = STATUS_OK
                sim_values = list()
                if settings['simulation']:
                    if settings['analysis']:
                        process_stats = pd.DataFrame.from_records(process_stats)
                    for rep in range(settings['repetitions']):
                        print("Experiment #" + str(rep + 1))
                        try:
                            simulate(settings, rep)
                            if settings['analysis']:
                                process_stats = process_stats.append(measure_stats(settings,
                                                                                   bpmn, rep,resource_table=parameters['resource_table']),
                                                                     ignore_index=True,
                                                                     sort=False)
                                sim_values.append(gen.mesurement(process_stats, settings, rep))
                        except Exception as e:
                            print('Failed ' + str(e))
                            status = STATUS_FAIL
                            break

                if status == STATUS_OK:
                    loss = (1 - np.mean([x['act_norm'] for x in sim_values]))
                    if loss < 0:
                        response = {'loss': loss, 'params': params, 'status': STATUS_FAIL}
                    else:
                        response = {'loss': loss, 'params': params, 'status': status}
                else:
                    response = {'params': params, 'status': status}
                print(response)
        else:
            for sim_percentageRaw in range(params['sim_percentage'],110,10):
                sim_percentage = sim_percentageRaw/100
                print('sim_percentage ' + str(sim_percentage))
                settings = sim.read_settings(params)
                params['output'] = settings['output']
                # Output folder creation
                if not os.path.exists(settings['output']):
                    os.makedirs(settings['output'])
                    os.makedirs(os.path.join(settings['output'], 'sim_data'))
                copyfile(os.path.join(settings['input'], settings['file']),
                         os.path.join(settings['output'], settings['file']))
                log = lr.LogReader(os.path.join(settings['output'], settings['file']),
                                   settings['timeformat'])
                # Execution steps
                mining_structure(settings, params['epsilon'], params['eta'])
                bpmn = br.BpmnReader(os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + '.bpmn'))
                process_graph = gph.create_process_structure(bpmn)

                # Evaluate alignment
                # chk.evaluate_alignment(process_graph, log, settings)

                print("-- Mining Simulation Parameters --")
                parameters, process_stats = par.extract_parameters(log, bpmn, process_graph, flag=f, k=0,simulator=params['simulator'],
                                                                   sim_percentage=sim_percentage)
                xml.print_parameters(os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + '.bpmn'),
                                     os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + 'Bimp.bpmn'),
                                     parameters['bimp'],sim_percentage=sim_percentage)
                xml_scylla.print_parameters(os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + '.bpmn'),
                                     os.path.join(settings['output'],
                                                  settings['file'].split('.')[0] + 'Scylla.bpmn'),
                                     parameters['scylla'], sim_percentage=sim_percentage)

                response = dict()
                status = STATUS_OK
                sim_values = list()
                if settings['simulation']:
                    if settings['analysis']:
                        process_stats = pd.DataFrame.from_records(process_stats)
                    for rep in range(settings['repetitions']):
                        print("Experiment #" + str(rep + 1))
                        try:
                            simulate(settings, rep)
                            if settings['analysis']:
                                process_stats = process_stats.append(measure_stats(settings,
                                                                                   bpmn, rep,resource_table=parameters['resource_table']),
                                                                     ignore_index=True,
                                                                     sort=False)
                                sim_values.append(gen.mesurement(process_stats, settings, rep))
                        except Exception as e:
                            print('Failed ' + str(e))
                            status = STATUS_FAIL
                            break

                if status == STATUS_OK:
                    loss = (1 - np.mean([x['act_norm'] for x in sim_values]))
                    if loss < 0:
                        response = {'loss': loss, 'params': params, 'status': STATUS_FAIL}
                    else:
                        response = {'loss': loss, 'params': params, 'status': status}
                else:
                    response = {'params': params, 'status': status}
                print(response)
    return response
def main(argv):
    space = {
        'file': 'PurchasingExampleEditable1.xes',
        #'epsilon': hp.uniform('epsilon', 0.0, 1.0),
        'epsilon':1,
        'eta':1,
        #'eta': hp.uniform('eta', 0.0, 1.0),
        'alg_manag': hp.choice('alg_manag', ['replacement',
                                             'trace_alignment',
                                             'removal']),
        'repetitions': 2,
        'simulation': False,
        'analysis':True,
        'flag':[2],
        'k':[1,2],
        'sim_percentage':70,
        'simulator':['bimp','scylla']
    }
    objective(space)
    ## Trials object to track progress
    #bayes_trials = Trials()
    #max_evals = 50
    ## Optimize
    #best = fmin(fn=objective, space=space, algo=tpe.suggest,
    #           max_evals=max_evals, trials=bayes_trials, show_progressbar=False)
    #print('Printing best')
    #print(best)
    # Save results
    #measurements = list()
    # for res in bayes_trials.results:
    #     measurements.append({
    #         'loss': res['loss'],
    #         'alg_manag': res['params']['alg_manag'],
    #         'epsilon': res['params']['epsilon'],
    #         'eta': res['params']['eta'],
    #         'status': res['status'],
    #         'output': res['params']['output']
    #     })
    # config = cp.ConfigParser(interpolation=None)
    # config.read("./config.ini")
    # sup.create_csv_file_header(measurements,
    #                            os.path.join(config.get('FOLDERS', 'outputs'),
    #                                         config.get('EXECUTION', 'filename')
    #                                         .split('.')[0] + '_' +
    #                                         sup.folder_id() + '.csv'))
#print(parameters.resource_pool)
#print()
#print(parameters.time_table)

# =============================================================================
# Main function
# =============================================================================

if __name__ == "__main__":
    main(sys.argv[1:])