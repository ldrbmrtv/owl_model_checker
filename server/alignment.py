from main import *
import os
from google import genai
from dotenv import load_dotenv


# Getting files
dir_path = os.path.dirname(os.path.abspath(__file__))
input_path = 'input/'
output_path = 'output/'

data_file = 'test-case-cleaned.json'
source_schema_file = 'schema.json'

data_path = os.path.join(dir_path, input_path, data_file)
source_schema_path = os.path.join(dir_path, input_path, source_schema_file)

prompt_path = os.path.join(dir_path, 'prompt.txt')

# Uploading files
load_dotenv()
api_key = os.environ.get('API_KEY')
client = genai.Client(api_key=api_key)

data_llm = client.files.upload(file=data_path, config={'mime_type': 'text/plain', 'display_name': data_file})
source_schema_llm = client.files.upload(file=source_schema_path, config={'mime_type': 'text/plain', 'display_name': source_schema_file})

# Getting prompt template
with open(prompt_path) as file:
    prompt_template = file.read()

# Iterating over rules
rules = get_rules()
for key, value in rules.items():

    target_schema = value['schema']
    if target_schema == 'owl':
        ext = 'ttl'
    elif target_schema == 'ids':
        ext = 'xml'
    
    response_file = f'{key}.{ext}'
    response_path = os.path.join(dir_path, output_path, response_file)

    target_schema_path = get_rule(key)
    target_schema_file = f'{key}.txt'
    
    prompt = str(prompt_template).replace('[data]', data_file)
    prompt = prompt.replace('[source_schema]', source_schema_file)
    prompt = prompt.replace('[target_schema]', target_schema_file)
  
    target_schema_llm = client.files.upload(file=target_schema_path, config={'mime_type': 'text/plain', 'display_name': target_schema_file})
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[target_schema_llm, data_llm, source_schema_llm, prompt])
    
    response_text = str(response.text)

    if target_schema == 'owl':
        response_text = response_text.replace("```turtle\n", '')
    elif target_schema == 'ids':
        response_text = response_text.replace("```xml\n", '')
    response_text = response_text.replace("\n```", '')

    with open(response_path, 'w', encoding='utf-8') as file:
        file.write(response_text)
    
    client.files.delete(name=target_schema_llm.name)

    if target_schema == 'owl':
        check_model(response_path)