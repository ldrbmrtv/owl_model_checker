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

@app.post('/api/rule/{id}')
async def api_check_model(id: str, file: UploadFile=File(...)):
    return check_model(id, file)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)