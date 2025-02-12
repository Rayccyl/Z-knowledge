from typing import Annotated, Union
from fastapi import FastAPI,Header, HTTPException
from fastapi.params import Depends
from pyzotero import zotero
from models import *
from getzotero import get_content
from mongodb import update_status
description = """
Zotero-Dify API provide Zotero items as knowledge for dify.ai . 🚀
"""
app = FastAPI(
    title="Z-knowledge",
    description=description,
    summary="Zotero knowledge for Dify",
    version="0.0.1",
    contact={
        "name": "邢郑苑",
        "url": "https://rayccyl.github.io",
        "email": "jufecimswsy@gmail.com",
    },
)
@app.get("/retrieval")
async def retrieval():
    return {'status': 'ok'}
@app.post("/retrieval",response_model=Response)
async def main(item:Request,authorization: Annotated[str | None, Header()] = None):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403,detail=error_response(1001))
    api_key=authorization.split(' ')[1]
    library_id=item.knowledge_id.split('&')[1]
    library_type=item.knowledge_id.split('&')[0]
    top_k=item.retrieval_setting.top_k
    score_threshold=item.retrieval_setting.score_threshold
    query=item.query
    #knowledge_id structure:{user/groups}&library_id
    try:
        lib=zotero.Zotero(library_id,library_type,api_key)
        lib.key_info()
    except:
        raise HTTPException(status_code=403,detail=error_response(1002))
    try:
        from typing import Mapping, Any
        from pymongo.synchronous.database import Database
        import pymongo
        my_client = pymongo.MongoClient("mongodb://localhost:27017/")
        mondb = my_client["chunked"]
    except:
        raise HTTPException(status_code=500,detail="Failed to connect to MongoDB")
    client,embedder=update_status(library_id,{'Zotero-API-Key': api_key},lib,mondb)
    return {'records':get_content(client,mondb,top_k,score_threshold,query,embedder)}

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)