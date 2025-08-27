import os
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn
import rdflib
from owlready2 import *
import sys


dir_path = os.path.dirname(os.path.abspath(__file__))
rule_files = 'rules/'
rule_base = 'rules.json'
temp_data_ttl = 'temp_data.ttl'
temp_data_nt = 'temp_data.nt'
log_file = 'temp_log.txt'

rule_base_path = os.path.join(dir_path, rule_base)
with open(rule_base_path) as file:
    rules = json.load(file)

app = FastAPI()

@app.get('/api/rule')
async def get_rules():
    return list(rules.keys())

@app.get('/api/rule/{id}')
async def get_rule(id: str):
    file = os.path.join(dir_path, rule_files, rules[id]['file'])
    return FileResponse(file)

@app.post('/api/rule/{id}')
async def check_model(id: str, file: UploadFile=File(...)):
    
    file_path_ttl = os.path.join(dir_path, temp_data_ttl)
    with open(file_path_ttl, 'wb') as file_saved:
        file_saved.write(file.file.read())

    g = rdflib.Graph()
    g.parse(file_path_ttl)
    file_path_nt = os.path.join(dir_path, temp_data_nt)
    g.serialize(destination=file_path_nt, format='nt')

    #onto_path.append(file_path_nt)
    onto = get_ontology(os.path.join('file://', file_path_nt)).load()
    for inst in onto.individuals():
        close_world(inst)
    onto.save(file_path_nt)
    
    try:
        log_file_path = os.path.join(dir_path, log_file)
        sys.stdout = open(log_file_path, 'w')
        with onto:
                sync_reasoner_pellet(
                infer_property_values = True,
                infer_data_property_values = True,
                debug=2)
        sys.stdout.close()
        with open(log_file_path) as file:
            log = file.read()
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
            return e


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)