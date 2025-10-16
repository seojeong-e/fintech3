from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from naver_search import naver_api

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html",{"request":request})

@app.post("/search")
def search(request: Request, keyword=Form(...)): 
    # 변수 이름 꼭 맞춰야함 키워드로 보냈기 때문에 키워드로 받아준 것
    
    results = naver_api(keyword)
    print(results)
    return templates.TemplateResponse(
         "results.html",
         {"request":request, "keyword":keyword, "results":results}
    )