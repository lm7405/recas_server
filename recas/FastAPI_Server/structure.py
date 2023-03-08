
from typing import List, Optional, Dict, Union, Any
from enum import Enum
from pydantic import BaseModel
from inspect import getmembers


class RecasRequirement(BaseModel):
    req_ID: str
    req_str: str
    status: Optional[str] = None
    errors: Optional[str] = None
    comment: Optional[str] = None
    structImage: Optional[str] = None
    fullStr: Optional[dict] = None
    nbOfSentences: Optional[int] = 0     # 단위 문장의 수
    key_infos: Optional[list] = None      # 주요 정보:req 분석 결과
    testcase: Optional[str] = None
    # 추천 등 필요한  field를 이곳에 추가할 것


class RecasRequirement2(BaseModel):
    pm_ID: str
    req_ID: str
    req_str: str
    status: Optional[str] = None
    errors: Optional[str] = None
    comment: Optional[str] = None
    structImage: Optional[str] = None
    fullStr: Optional[dict] = None
    nbOfSentences: Optional[int] = 0     # 단위 문장의 수
    key_infos: Optional[list] = None      # 주요 정보:req 분석 결과
    testcase: Optional[str] = None
    # 추천 등 필요한  field를 이곳에 추가할 것


class CheckReturn2(BaseModel):
    class CheckReturnData(BaseModel):
        status: int
        errors: str
        structImaage: str
        key_infos: Any
        nbOfSentences: int
        testcase: str


class RecasReq(BaseModel):
    method: str
    env: Optional[str] = None
    user: Optional[str] = None
    param: List[RecasRequirement] = []


class RecasReq2(BaseModel):
    method: Optional[str] = None
    param: List[RecasRequirement2] = []


class AddTerminologyQuery(BaseModel):
    class NewTerminologyReq(BaseModel):
        text: str
        recas_type: str
        recas_ver_type: str
        tokenizer: str
        tokenizer_type: str
        category: Optional[str] = None
        description: Optional[str] = None
        usage: Optional[str] = None

    method: str
    param: List[NewTerminologyReq] = []


class GetTerminologyQuery(BaseModel):
    method: str
    param: str


class DeleteTerminologyQuery(BaseModel):
    class DeleteTerminologyReq(BaseModel):
        text: str
        recas_type: Optional[str] = None
        recas_ver_type: Optional[str] = None
        tokenizer: Optional[str] = None
        tokenizer_type: Optional[str] = None
        category: str
        description: Optional[str] = None
        usage: Optional[str] = None

    method: str
    param: DeleteTerminologyReq
#
# class NewerrCodeReq(BaseModel):
#     errCode: str
#     description: Optional[str] = None
#     correction: Optional[str] = None
#
#
# class ListNewerrCodeReq(BaseModel):
#     method: str
#     param: List[NewerrCodeReq] = []
#
#
# class DeleteerrCodeQuery(BaseModel):
#     method: str
#     errCode: str


class ErrCodeQuery(BaseModel):
    method: str
    param: str


class TermData(BaseModel):
    text: str
    recas_type: str
    recas_ver_type: Optional[str]
    tokenizer: Optional[str]
    tokenizer_type: str
    category: Optional[str]
    description: Optional[str]
    usage: Optional[str]
    date: str
    synchronized: Optional[str] = False

    @classmethod
    def import_(cls, data):
        new_item = cls.__new__(cls)
        if isinstance(data, AddTerminologyQuery.NewTerminologyReq):
            for attr_str, value in getmembers(data):
                if not attr_str.startswith('_'):
                    new_item.__setattr__(attr_str, value)
        else:
            raise


class JSendResponse(BaseModel):
    class Status(str, Enum):
        SUCCESS = 'success'
        FAIL = 'fail'
        ERROR = 'error'

    status: Status
    data: Union[Dict, BaseModel] = {}
    message: Optional[str]


class TermListResponse(BaseModel):
    result: List[TermData]


class DefaultBody(BaseModel):
    method: str
    param: Any


class UpdateTermParam(BaseModel):
    term_data: List[TermData] = []


class GetTermParam(BaseModel):
    term_query: str
