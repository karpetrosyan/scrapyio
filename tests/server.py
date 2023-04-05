from fastapi import FastAPI
from fastapi import HTTPException

app = FastAPI()


@app.get("/")
async def root():
    return "Hello World"


@app.get("/403")
def status_403():
    HTTPException(status_code=403)