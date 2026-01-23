from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn
from main import *


app = FastAPI()

@app.get('/api/rule')
async def api_get_rules():
    return get_rules()

@app.get('/api/rule/{id}')
async def api_get_rule(id: str):
    return FileResponse(get_rule(id))

@app.get('/api/rule/{id}/clauses')
async def api_get_clauses(id: str):
    return get_clauses(id)

@app.post('/api/check_model')
async def api_check_model(data_file: UploadFile = File(...),
                          rule_file: UploadFile = File(...)
):
    with open(temp_data, 'wb') as f:
        shutil.copyfileobj(data_file.file, f)
    
    with open(temp_rule, 'wb') as f:
        shutil.copyfileobj(rule_file.file, f)
    
    return check_model(temp_data, temp_rule)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)