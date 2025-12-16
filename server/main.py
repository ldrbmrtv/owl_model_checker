import os
import rdflib
from owlready2 import *
import json
import sys
from explain_owlapy import *


dir_path = os.path.dirname(os.path.abspath(__file__))
rule_files = 'rules/'
rule_base = 'rules.json'
temp_data_ttl = 'temp_data.ttl'
temp_data_nt = 'temp_data.nt'
log_file = 'temp_log.txt'

rule_base_path = os.path.join(dir_path, rule_base)
with open(rule_base_path) as file:
    rules = json.load(file)


def get_rules():
    return rules

def get_rule(id: str):
    return os.path.join(dir_path, rule_files, rules[id]['file'])

def check_model(response_path: str):
    
    g = rdflib.Graph()
    g.parse(response_path)
    file_path_nt = os.path.join(dir_path, temp_data_nt)
    g.serialize(destination=file_path_nt, format='nt')

    onto = get_ontology(os.path.join('file://', file_path_nt)).load()
    #for inst in onto.individuals():
    #    close_world(inst)
    onto.save(file_path_nt)
    
    try:
        #log_file_path = os.path.join(dir_path, log_file)
        #sys.stdout = open(log_file_path, 'w')
        with onto:
            #sync_reasoner_pellet(
            #    infer_property_values = True,
            #    infer_data_property_values = True,
            #    debug=2)
            sync_reasoner_pellet()
        #sys.stdout.close()
        #with open(log_file_path) as file:
        #    log = file.read()

        reasoner = SyncReasonerJustifications(ontology=response_path, reasoner="Openllet")
        ontology_id = reasoner.ontology.get_ontology_id()
        onto_iri = ontology_id._ontology_iri.str
        fail_class_owlapy = OWLClass(f'{onto_iri}#NotCompliant')
        individuals_owlapy = reasoner.instances(fail_class_owlapy, direct=False)
        explanations_owlapy = reasoner.create_justifications(set(individuals_owlapy), fail_class_owlapy)
        for key, value in explanations_owlapy.items():
            explanation = []
            for x in value[0]:
                if 'Assertion' in x:
                    x = x.replace(f'{onto_iri}#', '')
                    x = x.replace('<', '')
                    x = x.replace('>', '')
                    x = x.replace('Object', '')
                    if 'DataPropertyAssertion' in x:
                        x = x.replace('DataPropertyAssertion', '')
                        x = x[1:-1]
                        x = x.split(' ')
                        order = [1, 0, 2]
                        x = [x[i] for i in order]
                        x = ' '.join(x)
                    if 'ClassAssertion' in x:
                        x = x.replace('ClassAssertion', '')
                        x = x[1:-1]
                        if 'AllValuesFrom' in x:
                            x = x.replace('AllValuesFrom', '')
                            x = x.rsplit(' ', 1)
                            x[0] = x[0][1:-1]
                            if 'OneOf' in x[0]:
                                x[0] = x[0].split(' OneOf')
                                x[0][1] = x[0][1].replace(' ', ', ')
                                x[0] = ' '.join(x[0])
                            x = [x[1], x[0]]
                            x = ' '.join(x)
                        if 'ComplementOf' in x:
                            x = x.replace('ComplementOf', 'Not')
                            x = x.split(' ')
                            x = [x[1], x[0]]
                            x = ' '.join(x)
                    explanation.append(x)
                    explanation = sorted(explanation)
            explanations_owlapy[key] = explanation

        fail_class = onto['NotCompliant']
        individuals = fail_class.instances()
        if len(individuals) > 0:
            equivalent_to = fail_class.INDIRECT_equivalent_to[0]
            
            requirement = equivalent_to.is_a[1]
            requirement = requirement.Class
            requirement = requirement.INDIRECT_equivalent_to[0]
            requirement = str(requirement).replace(f'{onto.name}.', '')
            
            rationale = equivalent_to.is_a[0]
            rationale = rationale.INDIRECT_equivalent_to[0].Classes
            rationale = [str(x).replace(f'{onto.name}.', '') for x in rationale]

            explanations = []

            for ind in individuals:
                data = [str(x).replace(f'{onto.name}.', '') for x in ind.is_a]
                data = list(set(data))
                data.remove('NotCompliant')
                explanations.append({
                    'object': ind.name,
                    'rationale': rationale,
                    'requirement': requirement,
                    'factually': explanations_owlapy[ind.name]
                })

            res = {
                'valid': False,
                'explanation': explanations
            }
            onto.destroy(update_relation=True, update_is_a=True)    
            return res
        
        res = {
            'valid': True
        }
        onto.destroy(update_relation=True, update_is_a=True)
        return res
    except Exception as e:
        if type(e).__name__ == 'OwlReadyInconsistentOntologyError':
            res = {
                'valid': False,
                'log': str(e)
            }
            onto.destroy(update_relation=True, update_is_a=True)
            return res
        else:
            onto.destroy(update_relation=True, update_is_a=True)
            return str(e)


onto_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), 'test/', 'test_v1.rdf')
res = check_model(onto_path)
with open('test.json', 'w') as file:
    json.dump(res, file)