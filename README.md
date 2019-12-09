# Simod + Resources

Simod combines several process mining techniques to fully automate the generation and validation of BPS models. The only input required by the Simod method is an eventlog in XES format.
Simod + Resources combine the best futures of Simod, though also take into account the specific resources configuration in the process such as availability, costs and roles. Simod + Resources let the user define assignation policies based in their preferences. An assignation policy is defined as how the resources should be arrange in the business process model. Depending on the policy the tool will find the optimal model + resource configuration.

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### System Prerequisites
 - Python 3.x
 - Java SDK 1.8

### Data format

The tool assumes the input is composed by a case identifier, an activity label, a resource attribute (indicating which resource performed the activity), and two timestamps: the start timestamp and the end timestamp. The resource attribute is required in order to discover the available resource pools, their timetables, and the mapping between activities and resource pools, which are a required element in a BPS model. We require both start and endtimestamps for each activity instance,
in order to compute the processing time of activities, which is also a required element in a simulation model.
As an extra element for this thesis project, per input log in XES format, is required a description of each resource cost. E.g.
```
<resourcesCost>
		<resource key="Penn Osterwalder" value="10"/>
		....
</resourcesCost>
```


### Execution steps
```
cd Simod_recursos_scylla
pip3 install -r requirements1.txt
python3 main.py
```

### Process configuration
The process can be setup in the file config.ini to execute different user preferences:
```
[EXECUTION][FileName]: XES File name e.g: ProductionEditable.xes
[EXECUTION][Repetitions]: How many iterations of the simulation want to be perform e.g. 1
[EXECUTION][Flag]: Options = 1 or 2. Flag that determines which assignation policy will be perform. Either: 
 - (1) Preferences assignation policy: Finding 'm' clusters with the k most frequent resources performing an specific task, where 'm' represents the number of total activities.
 - (2) Similitude: Clustering resources by a defined percentage of similarity.
[EXECUTION][k]: Variable that represents the k most frequent resources. Range in the form of 'min_k, max_k' e.g '4,8'. Min_k represents the lowest value to start finding the clusters with the k most frequent resources performing an specific task, and max_k represents the upper value of this range.
[EXECUTION][sim_percentage]: Similarity percentage in case the flag 2 was selected. (Value between 0 and 100)
[EXECUTION][happy_path]: True or False variable that represents the quality assignation policy. In this case the tool will determine the happy path of the process.
[EXECUTION][simulator]: Choose the simulator of preference. For this project we are only using Scylla, for future implementations will be possible to include more simulators though.
[EXECUTION][optimization]: True or False variable that define whenever you want to optimize the search. If this is selected the [OPTIMIZATION] section must be fill out.

[OPTIMIZATION][objective]: Define the variable to optimize. Choose among: flowTime_avg, cost_total, waiting_avg, time_workload_avg.
[OPTIMIZATION][criteria]: Choose the optimization criteria. 'min' for minimization or 'max' for maximization.
```

## Authors

* SIMOD: **Manuel Camargo** [More info](https://www.researchgate.net/profile/Manuel_Camargo4)
* Resource extension in SIMOD: **Camilo Montenegro**. Portfolio [here](https://ca-montenegro.github.io/)
* **Oscar González-Rojas** [More info](https://www.researchgate.net/profile/Oscar_Gonzalez-Rojas)
* **Marlon Dumas** [More info](https://kodu.ut.ee/~dumas/)
