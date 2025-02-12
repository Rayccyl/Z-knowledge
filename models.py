from pydantic import BaseModel
from typing import List, Optional
class RetrievalSetting(BaseModel):
    top_k: int
    score_threshold: float

class Request(BaseModel):
    knowledge_id: str
    query: str
    retrieval_setting: RetrievalSetting

class Record(BaseModel):
    content: str
    score: float
    title: str
    metadata: str

class Response(BaseModel):
    records: List[Record]

class ErrorResponse(BaseModel):
    error_code: int
    error_msg: str


ERROR_MESSAGES = {
    1001: "Invalid Authorization header format. Expected 'Bearer <api-key>' format.",
    1002: "Authorization failed",
    2001: "The knowledge does not exist"
}

def error_response(code: int) -> ErrorResponse:
    return ErrorResponse(
        error_code=code,
        error_msg=ERROR_MESSAGES[code]
    )
