from fastapi import FastAPI
from fastapi import Request
from fastapi import Response

app = FastAPI()


@app.get("/")
def root():
    return "Root"


@app.get("/cookies")
def cookies(request: Request, response: Response):
    response.set_cookie(key="test", value="test")
    return request.cookies


@app.get("/headers")
def headers(request: Request):
    return request.headers


@app.get("/for_moving")
def moving():
    return 200


@app.get("/best_scraping_library")
def best_scraping_library():
    return "scrapyio"
