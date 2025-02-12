from bson import ObjectId
from pymongo.synchronous.database import Database
from sentence_transformers import SentenceTransformer

from models import Record
from pymilvus import MilvusClient
def get_metadata(item)->dict:


    for i in range(len(item['creators'])):
        creator = item['creators'][i]
        if len(creator) == 2:
            item['creators'][i] = creator['creatorType']+' '+creator['name']
        else:
            item['creators'][i] = creator['creatorType']+' '+creator['firstName']+creator['lastName']


    string = ''
    for i in range(len(item['tags'])):
        string += item['tags'][i]['tag']
    item['tags']= string
    keys_to_remove = ['key', 'version', 'title', 'abstractNote', 'collections', 'relations', 'dateAdded',
                      'dateModified']
    for key in keys_to_remove:
        item.pop(key, None)
    item={k:v for k,v in item.items() if v is not None and v != ''}
    return item

def get_content(milvus:MilvusClient,mondb:Database,top_k:int,score_threshold:float,query:str,embedder:SentenceTransformer)->list[Record]:
    res = milvus.search(
        collection_name="chunks",
        anns_field="emd",
        data=embedder.encode([query]),
        limit=top_k,
        search_params = {"metric_type": "COSINE"}
    )
    collection=mondb['chunks']
    response=[]
    for i in res[0]:
        if i['distance'] > score_threshold:
            doc_chunk=collection.find_one({'_id':ObjectId(i['id'])})
            item_id=doc_chunk['item_id']
            content=doc_chunk['content']
            chunk_metadata=doc_chunk['chunk-metadata']
            doc_item=mondb['items'].find_one({'_id':ObjectId(item_id)})
            metadata=doc_item['item-metadata'] | chunk_metadata
            title=doc_item['title']
            record=Record(content=content,score=i['distance'],metadata=str(metadata),title=title)
            response.append(record)
    return response