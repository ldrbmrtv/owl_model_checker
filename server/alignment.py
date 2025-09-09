from main import *
import os
from google import genai
from dotenv import load_dotenv


# Getting files
dir_path = os.path.dirname(os.path.abspath(__file__))

data_file_name = 'test-case-cleaned.json'
schema_file_name = 'schema.json'
response_file_name = 'response.ttl'

data_path = os.path.join(dir_path, data_file_name)
schema_path = os.path.join(dir_path, schema_file_name)
response_path = os.path.join(dir_path, response_file_name)

prompt_path = os.path.join(dir_path, 'prompt.txt')

# Uploading files
load_dotenv()
api_key = os.environ.get('API_KEY')
client = genai.Client(api_key=api_key)

data_file_llm = client.files.upload(file=data_path, config={'mime_type': 'text/plain', 'display_name': data_file_name})
schema_file_llm = client.files.upload(file=schema_path, config={'mime_type': 'text/plain', 'display_name': schema_file_name})

# Getting prompt template
with open(prompt_path) as file:
    prompt_template = file.read()

prompt = prompt_template.replace('[data]', data_file_name)
prompt = prompt.replace('[schema]', schema_file_name)

# Iterating over rules
rules = get_rules()
for rule in rules:

    onto_path = get_rule(rule)
    onto_file_name = f'{rule}.txt'
    
    prompt = prompt.replace('[onto]', onto_file_name)
    
    onto_file_llm = client.files.upload(file=onto_path, config={'mime_type': 'text/plain', 'display_name': onto_file_name})
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[onto_file_llm, data_file_llm, schema_file_llm, prompt])
    
    response_text = str(response.text)
    response_text = response_text.replace("```turtle\n", '')
    response_text = response_text.replace("\n```", '')

    with open(response_path, 'w', encoding='utf-8') as file:
        file.write(response_text)
    
    client.files.delete(name=onto_file_llm.name)

    check_model(response_path)