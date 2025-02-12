from typing import Mapping, Any
from pymilvus import MilvusClient, FieldSchema, DataType, CollectionSchema
from fastapi import HTTPException
from pymongo.synchronous.database import Database
from pyzotero import zotero
import os
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
import requests
from langchain_text_splitters import MarkdownHeaderTextSplitter

from getzotero import get_metadata
from sentence_transformers import SentenceTransformer
import os

def update_status(user_id,header,lib:zotero.Zotero,mondb:Database[Mapping[str, Any],]):
    every_top=lib.everything(lib.top())
    directory='/tmp/Z-knowledge'
    client = MilvusClient("./milvus_demo.db")
    embedding_model = SentenceTransformer('moka-ai/m3e-base')
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i in every_top:
        if not mondb['items'].find_one({"top-key": i['key']}):
            for item in lib.children(i['key']):
                if item['data']['contentType'] == 'application/pdf':
                    url = 'https://api.zotero.org/users/'+user_id+'/items/'+item['data']['key']+'/file'
                    response = requests.get(url, headers=header, stream=True)
                    if response.status_code == 200:
                        path=directory+'/'+item['data']['key']+'.pdf'
                        with open(path, 'wb') as file:
                            for chunk in response.iter_content(chunk_size=2**12):
                                file.write(chunk)
                    else:
                        raise HTTPException(status_code=500,detail="failed to download PDF")

            name_without_suff = path.split(".")[0]
            local_image_dir, local_md_dir = name_without_suff+"/images", name_without_suff
            image_dir = str(os.path.basename(local_image_dir))
            os.makedirs(local_image_dir, exist_ok=True)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(
                local_md_dir
            )
            reader1 = FileBasedDataReader("")
            pdf_bytes = reader1.read(path)
            ds = PymuDocDataset(pdf_bytes)
            if ds.classify() == SupportedPdfParseMethod.OCR:
                infer_result = ds.apply(doc_analyze, ocr=True)
                pipe_result = infer_result.pipe_ocr_mode(image_writer)
            else:
                infer_result = ds.apply(doc_analyze, ocr=False)
                pipe_result = infer_result.pipe_txt_mode(image_writer)
            md_content = pipe_result.get_markdown(image_dir)

            headers_to_split_on = [
                ("#", "Section"),
                ("##", "Subsection"),
                ("###", "Sub-subsection"),
            ]
            chunks = MarkdownHeaderTextSplitter(headers_to_split_on,strip_headers=False).split_text(md_content)
            item_in_mongo={
                "knowledge-id": user_id,
                "top-key": i['key'],
                "title": i['data']['title'],
                "item-metadata":get_metadata(i['data']),
            }
            result = mondb['items'].insert_one(item_in_mongo)
            item_id = result.inserted_id

            documents=[]
            chunk_ids=[]
            for chunk in chunks:
                record={
                    "item_id": str(item_id),
                    "content":chunk.page_content,
                    "chunk-metadata":chunk.metadata,
                }
                result=mondb['chunks'].insert_one(record)
                chunk_id=result.inserted_id
                chunk_ids.append(str(chunk_id))
                documents.append(chunk.page_content)

            documents_embedding=embedding_model.encode(documents)

            embedded=[{"id":chunk_ids[i],"emd":documents_embedding[i]}for i in range(len(chunks))]
            pre_deal_milvus(documents_embedding.shape[1], client)
            client.insert("chunks",embedded)

    top_keys=[i['key'] for i in every_top]
    for doc in mondb['items'].find({'top-key': {'$nin': top_keys}}):
        client.delete(collection_name='chunks',ids=[str(i['_id']) for i in mondb['chunks'].find({'item_id':str(doc['_id'])})])
        mondb['chunks'].delete_many({'item_id':str(doc['_id'])})
        mondb['items'].delete_one({'top-key':doc['top-key']})


    return client,embedding_model


def pre_deal_milvus(dimension: int, client: MilvusClient):
    collections = client.list_collections()
    if "chunks" in collections:
        return
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True,max_length=12),
        FieldSchema(name="emd", dtype=DataType.FLOAT_VECTOR, dim=dimension)
    ]

    schema = CollectionSchema(fields, description="chunks collection")
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="emd",
        index_type="AUTOINDEX",
        metric_type="COSINE"
    )
    client.create_collection(collection_name="chunks", schema=schema,index_params=index_params)
    print(f"Collection 'chunks' created with dimension {dimension}.")








