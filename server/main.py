import os
import rdflib
from owlready2 import *
import json
from explain_owlapy import *
import shutil


dir_path = os.path.dirname(os.path.abspath(__file__))
rule_files = 'rules/'
rule_base = 'rules.json'
temp_dir = 'temp/'
temp_rule = os.path.join(dir_path, temp_dir, 'temp_rule.owl')
temp_data = os.path.join(dir_path, temp_dir, 'temp_data.owl')
temp_nt = os.path.join(dir_path, temp_dir, 'temp.nt')
temp_merged = os.path.join(dir_path, temp_dir, 'temp_merged.owl')
temp_classified = os.path.join(dir_path, temp_dir, 'temp_classified.owl')
log_file = 'temp_log.txt'

rule_base_path = os.path.join(dir_path, rule_base)
with open(rule_base_path) as file:
    rules = json.load(file)


def get_rules():
    return rules


def get_rule(id: str):
    return os.path.join(dir_path, rule_files, rules[id]['file'])


def get_onto(response_path: str):
    g = rdflib.Graph()
    g.parse(response_path)
    g.serialize(destination=temp_nt, format='nt')

    onto = get_ontology(os.path.join('file://', temp_nt)).load()
    #for inst in onto.individuals():
    #    close_world(inst)
    #onto.save(temp_nt)
    return onto


def get_clauses(id: str):

    onto_path = get_rule(id)
    onto = get_onto(onto_path)
    
    classes = list(onto.classes())

    fail_class = onto['NotCompliant']
    equivalent_to = fail_class.INDIRECT_equivalent_to[0]
    
    requirement = equivalent_to.is_a[1]
    requirement = requirement.Class
    #requirement = requirement.INDIRECT_equivalent_to[0]
    requirement = {
        'id': str(requirement).replace(f'{onto.name}.', ''),
        'description': requirement.label[0],
        'code': str(requirement.INDIRECT_equivalent_to[0]).replace(f'{onto.name}.', '')
    }
    
    rationale = equivalent_to.is_a[0]
    rationale = rationale.INDIRECT_equivalent_to[0].Classes
    rationale = [{
        'id': str(x).replace(f'{onto.name}.', ''),
        'description': x.label[0],
        'code': str(x.INDIRECT_equivalent_to[0]).replace(f'{onto.name}.', '')
    } for x in rationale]

    res = {
        'id': id,
        'rationale': rationale,
        'requirement': requirement
    }

    onto.destroy(update_relation=True, update_is_a=True)

    return res


def copy_instances(source_path, target_path):

    source_onto = rdflib.Graph().parse(source_path)
    target_onto = rdflib.Graph().parse(target_path)
    merged = source_onto + target_onto
    merged.serialize(temp_merged, format='xml')
    return temp_merged


def check_model(data_path: str, rule_path: str):

    onto_path = copy_instances(data_path, rule_path)

    onto = get_onto(onto_path)    

    try:
        #log_file_path = os.path.join(dir_path, log_file)
        #sys.stdout = open(log_file_path, 'w')
        with onto:
            sync_reasoner_pellet(
                infer_property_values = True,
                infer_data_property_values = True,
                debug=2)
            #sync_reasoner_pellet()
            onto.save(temp_classified)

        classes = list(onto.classes())
        for cl in classes:
            if cl.name == 'NotCompliant':
                fail_class_iri = cl.iri
                break

        #sys.stdout.close()
        #with open(log_file_path) as file:
        #    log = file.read()

        reasoner = SyncReasonerJustifications(ontology=temp_classified, reasoner="Openllet")
        #ontology_id = reasoner.ontology.get_ontology_id()
        #onto_iri = ontology_id._ontology_iri.str
        #fail_class_owlapy = OWLClass(f'{onto_iri}#NotCompliant')
        fail_class_owlapy = OWLClass(fail_class_iri)
        onto_iri = fail_class_owlapy.iri._namespace
        individuals_owlapy = reasoner.instances(fail_class_owlapy, direct=False)
        explanations_owlapy = reasoner.create_justifications(set(individuals_owlapy), fail_class_owlapy)
        for key, value in explanations_owlapy.items():
            explanation = []
            for x in value[0]:
                if 'Assertion' in x:

                    #Formatting owlapy
                    x = x.replace(onto_iri, '')
                    x = x.replace('<', '')
                    x = x.replace('>', '')
                    x = x.replace('Object', '')
                    if 'DataPropertyAssertion' in x:
                        x = x.replace('DataPropertyAssertion', '')
                        x = x[1:-1]
                        x = x.split(' ')
                        order = [1, 0, 2]
                        x = [x[i] for i in order]
                        x[2] = x[2].replace('"', '')
                        x[2] = x[2].replace('^^xsd:decimal', '')
                    if 'ClassAssertion' in x:
                        x = x.replace('ClassAssertion', '')
                        x = x[1:-1]
                        if 'AllValuesFrom' in x:
                            x = x.replace('AllValuesFrom', '')
                            x = x.rsplit(' ', 1)
                            x[0] = x[0][1:-1]
                            x = [x[1]] + x[0].split(' ', 1)
                            if 'OneOf' in x[2]:
                                x[2] = x[2].replace('OneOf', '')
                                x[2] = x[2].replace('(', '')
                                x[2] = x[2].replace(')', '')
                                x[2] = x[2].split(' ')
                        if 'ComplementOf' in x:
                            x = x.replace('ComplementOf', '')
                            x = x.split(' ')
                            x = [x[1], 'Not', x[0]]
                    explanation.append(x)
                    #explanation = sorted(explanation)

            #Grouping by subject
            grouped = {}
            for triple in explanation:
                if grouped.get(triple[0]) == None:
                    grouped[triple[0]] = {triple[1]: triple[2]}
                else:
                    grouped[triple[0]][triple[1]] = triple[2]
            explanation = grouped

            explanations_owlapy[key] = explanation

        if len(explanations_owlapy) > 0:
            res = {
                'valid': False,
                'explanation': explanations_owlapy
            }
        else:
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


#data_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), 'test/', 'test_v1.rdf')
#rule_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), 'server/', 'rules/', 'OWL_test_1.owl')
#res = check_model(data_path, rule_path)
#with open('test.json', 'w') as file:
#    json.dump(res, file)