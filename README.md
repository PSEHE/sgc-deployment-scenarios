# Overview
We first need to calculate distance matrices. This is done in the script
`calculate_distance_matrices.py` which calls code from `distance_matrix_functions.py`

We then need to build many different types of models. All the code for building
models are in `deploment_models.py` while the script `results_analysis.py` contains
example code for how to run a model as well as a useful function for pulling
statistics out of the result. `vulnerability_risk_functions.py` is a collection
of functions in progress that is aimed at easily integrating different vulnerability
and risk data.



# sgc-deployment-scenarios
Optimizing resilience hub deployment for overall population coverage, climate vulnerability, and more.

* Uses Networkx package to perform network analysis: https://automating-gis-processes.github.io/2017/lessons/L7/network-analysis.html
* Resilience hub locations based on prior PSE analysis with geofabrik OSM data
* Coverage maximized for climate vulnerabilities using various public datasets on air, fire, EJ, etc.
* Users should save large datasets that must be stored locally one directory up from this repo and write code accordingly
* Useful tutorial for using pyomo framework: https://www.osti.gov/servlets/purl/1376827
