from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from cache import DIMS
from recas.FastAPI_Server.structure import *

debug = True

RECAS_SERVER_HOST = "localhost:8000"
SELF_PORT = "9000"

DIMSHost = "localhost"
db_name = "dimsTermDic"
column_name = "tccDictionary"
port_number = 27017


# ------------------------------------------------------------------------------------
#            recas server 초기화
#  1) fastAPI object 생성
# ------------------------------------------------------------------------------------
# --1) fastAPI object 생성
app = FastAPI()

# --2-1) DIMS 연결
dims = DIMS.DIMS(mongoHost=DIMSHost, port=port_number)
collection = dims.connect2Collection(dbName=db_name, collectionName=column_name)
try:
    doc = collection.find_one()
    print("\n++++ DIMS 가 정상적으로 작동합니다.")
except:
    print("\n+++++ DIMS를 위한  mongod 을 실행한 후, 다시 실행하시기 바랍니다.")
print(".... DIMS 처리 결과에 주의하시기 바랍니다.")


# -------------------------------------------------------------------------
# CORS(Cross-Origin Resource Sharing)
# cross-origin HTTP 요청을 제한하는 브라우저 보안기능
# 참고 : https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/how-to-cors.html
# -------------------------------------------------------------------------

from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://127.0.0.1:" + SELF_PORT,
    "http://localhost:" + SELF_PORT,
    "http://222.117.104.40:10024"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------------------------
#                      용어 및 오류 코드 검색 query 문장 구성
# key를 중심으로 검색함
# key의 종류는 다음과 같음
#   DIMS의 경우      : "text"    (용어)
#   적합성 오류의 경우 : "errCode" (코드)
# --------------------------------------------------------------------------------------------
def build_query_statement(key, instr):
    if instr == "":     # 처리 하지 않음
        return ""
    if instr[0] == '[':     # 매치되는 단어 찾기 (예)["진입", "신호"]] = > 진입, 신호, 진입신호
        query = {key: {"$in": json.loads(instr)}}
        return json.dumps(query)
    if instr[0] == '%':    # 문자가 포함된 용어 (예) % 진입 = > 진입, 역진입
        query = {key: {"$regex": instr[1:]}}
        return json.dumps(query)
    if instr[0] == '^':     # 문자로 시작되는 용어 (예) ^ 진입 = > 진입, 진입신호
        query = {key: {"$regex": "^" + instr[1:]}}
        return json.dumps(query)
    if instr[0] == '{':      # query 문장 자체
        # (예) {"$or": [{"text": "진입 신호"}, {"category": "Train"}]}
        return instr
    query = {key: instr}  # 입력과 일치하는 용어
    return json.dumps(query)


# -------------------------------------------------------------------------
# 단어 검색
# 쿼리를 사용하여 단어를 검색하는 기능
# get_Terminology()        :  용어 검색(검색 요청 형식)
#     매치되는 단어 찾기  (예)["진입", "신호"]] = > 진입, 신호, 진입신호
#     문자가 포함된 용어  (예) % 진입 = > 진입, 역진입
#     문자로 시작되는 용어 (예) ^ 진입 = > 진입, 진입신호
#     query 문장 자체    (예) {"$or": [{"text": "진입 신호"}, {"category": "Train"}]}
#     기타 : 입력과 일치하는 용어#
# -------------------------------------------------------------------------
@app.post("/getTerm")
def get_term(request_body: DefaultBody):
    try:
        param = GetTermParam.parse_obj(request_body.param)

        # 1) mongo db에 사용한 query 생성
        dims_query = build_query_statement("text", param.term_query)

        # 2) 생성한 query로 검색
        dims.connect2Collection(dbName=db_name, collectionName=column_name)
        docs, _ = dims.executeQuery(dims_query)
        print("---query term, query:", dims_query)

        # 3) response
        result = []
        for item in docs:
            result.append(TermData.parse_obj(item))
        response = JSendResponse(
            status=JSendResponse.Status.SUCCESS,
            data=TermListResponse(result=result)
        )
        return JSONResponse(response.json())
    except Exception as ex:
        response = JSendResponse(
            status=JSendResponse.Status.ERROR,
            message=str(ex)
        )
        return JSONResponse(response.json())


# -------------------------------------------------------------------------
# 단어 커밋
# Local 환경의 단어 정보 등록/수정을 중앙 DB에 반영
# -------------------------------------------------------------------------
@app.post("/updateTerm")
def update_term(request_body: DefaultBody, request: Request):
    try:
        param = UpdateTermParam.parse_obj(request_body.param)
        client = request.client
        # 병렬로 단어 커밋 수행
        # Thread(target=update_term_logs, args=(param.term_data, client, dims, db_name, column_name)).start()
        update_term_logs(param.term_data, client, dims, db_name, column_name)

        response = JSendResponse(
            status=JSendResponse.Status.SUCCESS,
            message="요청되었습니다."
        )
        return JSONResponse(response.json())
    except Exception as ex:
        if debug:
            raise ex
        response = JSendResponse(
            status=JSendResponse.Status.ERROR,
            message=str(ex)
        )
        return JSONResponse(response.json())


def update_term_logs(term_updated_logs: List[TermData], client, dims_, db_name_, column_name_):
    try:
        dims_.connect2Collection(dbName=db_name_, collectionName=column_name_)
        term_updated_logs_ = []
        for term_updated_log in term_updated_logs:
            term_updated_logs_.append(term_updated_log.dict())
        count, res = dims.addTermsListDictionary(term_updated_logs_)
        cnt_req = len(term_updated_logs)
        # 3) 메세지 생성
        if cnt_req == count:
            message = " 요청된 단어(총 " + str(count) + "개)가 모두 DB에 추가되었습니다."
        else:
            message = " 요청된 단어(총 " + str(cnt_req) + "개) 중에서 " + str(count) + "개 단어가 DB에 추가되었습니다."
        print(message)

        # 4) response
        update_term_ = UpdateTermParam(term_data=term_updated_logs)

        response = DefaultBody(
            method="synchronize_return",
            param=update_term_
        )
    except Exception as ex:
        if debug:
            raise ex

        response = DefaultBody(
            method="synchronize_return",
            param="update_term_logs_error"
        )

    try:
        client = "http://" + client.host + ':' + str(client.port)
        client_url = "/recas/synchronizeReturn"
        # requests.get(client.host + ":" + client.port + client_url, response, timeout=5)
        # requests.post("http://127.0.0.1:8000/recas/synchronizeReturn", response.json(), timeout=5)
        print("Response updating word logs success")
    except Exception as ex:
        if debug:
            raise ex
        print("Response updating word logs failed")


if __name__ == "__main__":
    import uvicorn
    # dims.insertDictionary(dbName=db_name, collectionName=column_name)
    uvicorn.run(app, host="0.0.0.0", port=int(SELF_PORT))
