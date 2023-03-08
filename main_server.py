# ======================================================================================
#
#                           recasserver  main.py
#
# 1. localhost 접속 실행 방법
#     1) mongod --dbpath=data/db 실행 (cmd 창에서)
#     2) uvicorn main:app --reload --host=0.0.0.0 --port=8000 실행
#                (port 번호 등은 필요에 따라 변경)
# 2. dims server 실행시
#     1) dims server 및 port 재 설정(변수 값 수정)
#        DIMSHost  = "localhost"
#        recasDBHost= "localhost"
#
#  3. dims schema 조정되면 아래 변수 초기값 수정
#       dbName         = "dimsTermDic"
#       colName        = "dictionary"
#       recasdbName    = "recasDB"
#       errcodecolName = "errCode"
#
# ======================================================================================

from fastapi.responses import HTMLResponse, JSONResponse
import requests
import json
import configparser

from recas.FastAPI_Server.structure import *
from recas.FastAPI_Server import *


# ---------------------------------------------------------------------
#    server 초기화
#    fastAPI() object 생성,
#    recas object 초기화 (dictionary load  등
# ---------------------------------------------------------------------


# debug 일 시 raise 방생
debug = True

# 전역 클래스
app: ServerFastApi
recas: ServerRecas
dims: ServerDims
result_cache: ServerResultCache


config_file_path = "config.ini"

# tcc_address = "http://localhost:9000/"
tcc_address = "http://222.117.104.40:10024/"

dims_config = ServerDIMSConfig(
    db_addr="localhost",
    db_port=27017,
    recas_db_name="dimsTermDic",
    recas_column_name="dictionary",
    error_db_name="recasDB",
    error_column_name="errCode",
    init_db=True,
    dict_file_path="data\\DimsWordsDict-210919_0.xlsx",
)

worker_config = ServerRecasWorkerConfig(
    use_worker=False,
    num_workers=0,
    num_sentences=10,
    server_dims_config=dims_config
)
recas_config = ServerRecasConfig(
    mfile_path='data\\sample\\model23.h5',
    komop_tag_path="data\\sample\\komop_tags.txt",
    chunk_tag_path="data\\sample\\chunk_tags.txt",
    chunk_rule_path='data\\sample\\chunk_rule.xlsx',
    komop_rule_path="data\\sample\\komop_rule.xlsx",
    user_dict_path="data\\sample\\user_dict.txt",
    result_path="result",
    worker_config=worker_config
)
result_cache_config = ServerResultCacheConfig(
    max_cache=300,
)
fast_api_config = ServerFastApiConfig(
    # ------------------------------------------------------------------------
    # usage URL : http://localhost:8000/documents/<filename>>
    # result    : documents/<filename> 내용
    # 특수 case: 파일 이름이 아래와 같을 경우, 사전에 정의된 파일읋 서브함
    #   확장할 때 아래 specFile에 정의할 것
    #   test : ./documents/recasCheck.js.html browser로 적합성 검사 테스트
    # ------------------------------------------------------------------------
    specFile={
        "test": './documents/recasCheck.js.html',
        "dims": './documents/DimsCRUD.html',
        "errcode": './documents/recasError.html'
    },
    port=8000,
    # -------------------------------------------------------------------------
    #    error code 및 의미
    #  후에 class로 구현할 것
    # -------------------------------------------------------------------------
    error={
        1000: "사전에 없는 단어"
    }
)


def init_config():
    global tcc_address, fast_api_config, dims_config, recas_config, worker_config
    try:
        config = configparser.ConfigParser()
        try:
            config.read(config_file_path)
        except UnicodeDecodeError:
            config.read(config_file_path, encoding="UTF-8")

        fast_api_config.port = int(config.get("Server", "reacs_server_port"))
        tcc_address = config.get("Server", "tcc_server")

        dims_config.db_addr = config.get("Cache DB", "cache_db_addr")
        dims_config.db_port = int(config.get("Cache DB", "cache_db_port"))
        dims_config.recas_db_name = config.get("Cache DB", "cache_db_name")
        dims_config.recas_column_name = config.get("Cache DB", "cache_column_name")
        dims_config.dict_file_path = config.get("Cache DB", "default_dict_file_path")

        recas_config.komop_tag_path = config.get("Recas", "komoran_plus_tag_file_path")
        recas_config.komop_rule_path = config.get("Recas", "komoran_plus_rule_file_path")
        recas_config.chunk_tag_path = config.get("Recas", "chunk_tag_file_path")
        recas_config.chunk_rule_path = config.get("Recas", "chunk_rule_file_path")
        recas_config.mfile_path = config.get("Recas", "model_file_path")
        recas_config.result_path = config.get("Recas", "result_dir_path")

        worker_config.use_worker = config.get("Worker", "use_worker").lower() in \
                                   ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']
        worker_config.num_workers = int(config.get("Worker", "num_workers"))
        worker_config.num_sentences = int(config.get("Worker", "num_sentences"))
        worker_config.server_dims_config = dims_config

    except Exception as ex:
        if debug:
            raise ex
        print("Fail to read config file")


init_config()


# ------------------------------------------------------------------------------------
#            recas server 초기화
#  1) fastAPI object 생성
#  2) DIMS 연결, recasdb(errCode 포함) 연결
#  3) recas 초기화
# ------------------------------------------------------------------------------------
# --1) fastAPI object 생성
app = ServerFastApi(fast_api_config, debug)


def init():
    global app, recas, dims, result_cache, debug
    global dims_config, recas_config, worker_config, result_cache_config

    try:
        # --2) DIMS object 생성
        print("\n++++ DIMS init 를 시작 합니다.")
        dims = ServerDims(dims_config, debug)
        print("\n++++ DIMS 가 정상적으로 작동합니다.")

        # --3) recas object 생성
        print("\n++++ recas init 를 시작 합니다.")
        recas = ServerRecas(recas_config, dims=dims, debug=debug)
        print(".... recas init 가 정상적 으로 종료되었습니다")

        # --4) result cache object 생성
        result_cache = ServerResultCache(result_cache_config, debug)
        result_cache.set_recas(recas)
    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


# init()


# ------------------------------------------------------------------------
#  usage URL : http://127.0.0.1:8000/recas
#  result    : index.html 화면(recas 메인 화면)
# ------------------------------------------------------------------------
@app.get("/recas")
async def read_root():
    try:
        view_file = open(file='index.html', mode="r", encoding='UTF8')  # 한글이 있는 경우,encoding 설정
        html_content = view_file.read()
        view_file.close()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)
            return "index.html 처리에 오류가 발생하였음"


# ------------------------------------------------------------------------
# usage URL : http://localhost:8000/clearCache
# result    : cache를 clear함
# ------------------------------------------------------------------------
@app.get("/recas/clearCache")
def reset_cache():
    global app, dims, recas, result_cache, debug

    try:
        result_cache.clear()
        recas.clear_result()
        return HTMLResponse(content="캐시가 초기화 되었음 ", status_code=200)
    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


# ------------------------------------------------------------------------
# usage URL : http://localhost:8000/file/filename
# result    : 파일
# ------------------------------------------------------------------------
@app.get("/recas/file/{filename}")
def handle_document(filename):
    global app, dims, recas, result_cache, debug

    try:
        print(" file name : ", filename)
        low_file_name = filename.lower()
        if low_file_name in app.config.specFile.keys():
            view_file = open(file=app.config.specFile[low_file_name], mode='r', encoding='utf-8')
        else:
            view_file = open(file='./documents/' + filename, mode='r', encoding='utf-8')
        html_content = view_file.read()
        view_file.close()
        return HTMLResponse(content=html_content, status_code=200)
    except IOError:
        msg = "화일 [ " + filename + " ] 을 찾을 수 없음"
        return HTMLResponse(content=msg, status_code=404)
    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


# ------------------------------------------------------------------------
# usage URL : http://localhost:8000/result/reqID
# result    : 해당 requirement의 parese tree 그림
# ------------------------------------------------------------------------
@app.get("/recas/result/{req_id}")
def handle_parsetree_image(req_id):
    global app, dims, recas, result_cache, debug

    try:
        html_content = result_cache.get_image(req_id)

        return HTMLResponse(content=html_content, status_code=200)
    except IOError:
        msg = "이미지 [ " + str(req_id) + " ] 을 찾을 수 없음"
        return HTMLResponse(content=msg, status_code=404)

    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


@app.get("/recas/result_2/{pm_id}/{req_id}")
def handle_parsetree_image_2(pm_id, req_id):
    global app, dims, recas, result_cache, debug

    try:
        html_content = result_cache.get_image(pm_id + "/" + req_id)

        return HTMLResponse(content=html_content, status_code=200)
    except IOError:
        msg = "이미지 [ " + str(pm_id) + "/" + str(req_id) + " ] 을 찾을 수 없음"
        return HTMLResponse(content=msg, status_code=404)

    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


# ------------------------------------------------------------------------
# usage URL : http://localhost:8000/result/reqID
# result    : 해당 requirement의 parese tree 그림
# ------------------------------------------------------------------------
@app.get("/recas/testcase/{req_id}")
def get_testcase(req_id):
    global app, dims, recas, result_cache, debug

    print("testcase requested, reqID: ", req_id)
    try:
        output = result_cache.get_testcase(req_id)
        return output

    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


@app.get("/recas/testcase_2/{pm_id}/{req_id}")
def get_testcase_2(pm_id, req_id):
    global app, dims, recas, result_cache, debug

    print("testcase requested, pmID/reqID: ", pm_id, "/", req_id)
    try:
        output = result_cache.get_testcase(pm_id + "/" + req_id)
        return output

    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


# ------------------------------------------------------------------------
#           RECAS  요청
# 요청 check : 요구사항의 적합성을 검사하는 post 요청
#
# 1. POST payload로 전달하는 테스트
#   (참고) URL "localhost:8000/docs"에 접속하면 쉽게 테스트 할 수 있음
#   1) request body에 실린 JSON 을 읽고 필요시 해당 데이터를 상응되는 타입으로 변환
#   2) 데이터 유효성 검사 결과 만약 invalid 이면 error를 반환
#   3) parameter인 request에 전달
#   4) request.dict() 을 호출하여 dict 처럼 사용함  # request.dict()는 request를 dict 형태로 변환함
#
# 2. 실행 예
#
#  POST payload
#  {
#   "method": "check",
#   "user": "Choi",
#   "param":
#       [
#          {
#             "req_ID": "ID-01234",
#             "req_str":"ID-강아지"
#          },
#          {
#             "req_ID": "ID-56789",
#             "req_str":"ID-토끼"
#          }
#       ]
#  }
#  응답 body
#  [
#    {
#     "req_ID": "ID-01234",
#     "req_str": "ID-강아지",
#     "status": "0"
#    },
#    {
#     "req_ID": "ID-56789",
#     "req_str": "ID-토끼",
#     "status": "0"
#    }
#  ]
# ------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
#  요청 예
# {
#   "method": "check",
#   "env": "choi",
#   "user": "choi",
#   "param": [{"req_ID":R123", "req_str":""시스템A는 가동하는 중인 도어상부표시등을 점멸한다."}
#            ]
# }
# --------------------------------------------------------------------------------------------
#  checkRequirement(sentence)
#  1. recas.py에 정의된 함수이며, 요구사항 한 문장의 적합성을 분석하고 그 결과를 return함
#  2. return 값 :
#    1) run_data
#       recas 처리 결과 objects(token list, parser tree 등 일체의 objects) list
#       RecasUtil.py의 def run_sentence()에 정의됨
#           run_data = {"ori_sentence": ori_sentence,
#                       "token_list": token_list,
#                       "recovered_position": recovered_position,
#                       "parse_tree": parse_tree,
#                       "quantity_report": quantity_report,
#                       "rebuild_parse_tree": rebuild_parse_tree,
#                       "unique_sentences_data": unique_sentences_data,
#                       "error_report": error_report,
#                       "error_code": error_code,
#                       "key_infos": sentences_string
#                       }
#    2) output(dictionary)
#      (1) rootNode
#         parsetree의 rootNode (자세한 내용은 recas main 참조)
#      (2) listSingleSentences
#        parsetree의 root 리스트와 문장의 구조 tree diagram  이미지 파일 URL 을 담은 다음과 같은 dict 리스트
#        {
#            "parseTree": tree의 root node,
#            "image": parse tree 이미지 파일 이름
#        }
#      (3) errorCodeList: error code와  위치가 저장된 dict  list
#        {
#            "errCode": error code,
#            "errPos": error 위치,
#            "errorTok":: error가 발생한 문장
#        }
#    3) image filename
# --------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


@app.post("/recas/check")
def check_requirement(request: RecasReq):
    global app, dims, recas, result_cache, debug
    global recas_config

    try:
        if recas is False:
            recas = ServerRecas(recas_config, dims, debug)
            print("\n+++ recas 초기화를 다시 시도한 결과: ", recas is True)
            if recas is False:
                return "recas를 초기화할 수 없습니다.  관리자에게 연락 부탁드립니다."

        print("\n+++ post param: ", str(request))
        reply = {}
        for req in request.param:
            output = recas.run_sentence(req.req_str)
            req_id, req = result_cache.save_cache_old(output, req)
            reply[req_id] = req
            reply[req_id]["testcase"] = get_testcase(req_id)
        return reply

    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


@app.post("/recas/check_2")
def check_requirement_2(request: RecasReq2):
    global app, dims, recas, result_cache, debug

    try:
        if recas is False:
            recas = ServerRecas(recas_config, dims=dims, debug=debug)
            print("\n+++ recas 초기화를 다시 시도한 결과: ", recas is True)
            if recas is False:
                return "recas를 초기화할 수 없습니다.  관리자에게 연락 부탁드립니다."

        print("\n+++ post param: ", str(request))
        reply: Dict[str, Dict] = {}
        checking_result_list: List[dict] = recas.run_sentences(request.param)
        for i, checking_result in enumerate(checking_result_list):
            key, req = result_cache.save_cache(checking_result, request.param[i])
            reply[key] = req
        return reply

    except Exception as ex:
        if debug:
            raise ex
        else:
            print(ex)


# --------------------------------------------------------------------------------------------
#
#                                       DIMS 용어
#
#  1)get_Terminology()        :  용어 검색(검색 요청 형식)
#     매치되는 단어 찾기  (예)["진입", "신호"]] = > 진입, 신호, 진입신호
#     문자가 포함된 용어  (예) % 진입 = > 진입, 역진입
#     문자로 시작되는 용어 (예) ^ 진입 = > 진입, 진입신호
#     query 문장 자체    (예) {"$or": [{"text": "진입 신호"}, {"category": "Train"}]}
#     기타 : 입력과 일치하는 용어#
#  2) add_new_Terminology()    :  새로운 용어를 DIMS 사전에 insert함
#  3) parameter type
#     문자열
# --------------------------------------------------------------------------------------------


@app.post("/recas/getTerm")
def get_terminology(request_body: GetTerminologyQuery):
    global app, dims, recas, result_cache, debug

    try:
        # 1) mongo db에 사용한 query 생성
        dims_query = dims.build_query_statement("text", request_body.param)
        print("---query term, query:", dims_query)

        # 2) 생성한 query로 검색
        docs, _ = dims.executeQuery(dims_query)

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
        if debug:
            raise ex
        else:
            message = "요청 pattern이나 DIMS에 오류가 있습니다. 확인 후 다시 시도하여 주시기 바랍니다."

            response = JSendResponse(
                status=JSendResponse.Status.ERROR,
                message=message
            )
            return JSONResponse(response.json())


@app.post("/recas/addTerm")
def add_terminology(request_body: AddTerminologyQuery):
    global app, dims, recas, result_cache, debug

    try:
        term_list = request_body.param

        # 1) local db 업데이트
        count, _ = dims.addTermsListDictionary(term_list)

        # 2) recas 업데이트
        for term in term_list:
            recas.add_dict(term.dict())
            # recas.recas.komop_tokenizer.add_dict(term.dict())

        # 2) 메세지 생성
        cnt_req = len(term_list)
        if cnt_req == count:
            message = " 요청된 단어(총 " + str(count) + "개)가 모두 DB에 추가되었습니다."
        else:
            message = " 요청된 단어(총 " + str(cnt_req) + "개) 중에서 " + str(count) + "개 단어가 DB에 추가되었습니다."

        # 3) response
        response = JSendResponse(
            status=JSendResponse.Status.SUCCESS,
            message=message
        )
        return JSONResponse(response.json())
    except Exception as ex:
        if debug:
            raise ex
        else:
            response = JSendResponse(
                status=JSendResponse.Status.ERROR,
                message=str(ex)
            )
            return JSONResponse(response.json())


@app.post("/recas/deleteTerm")
def delete_terminology(request_body: DeleteTerminologyQuery):
    global app, dims, recas, result_cache, debug

    try:
        param = DeleteTerminologyQuery.DeleteTerminologyReq.parse_obj(request_body.param)
        # 1) 쿼리 생성
        query_text = dims.build_query_statement("text", param.text)
        query_category = {"category": param.category}
        query = {"$and": [json.loads(query_text), query_category]}

        # 2) recas 업데이트
        recas.remove_dict(param.dict())
        # recas.recas.komop_tokenizer.remove_dict(param.dict())

        # 2) 생성한 쿼리로 local db 업데이트
        count = dims.deleteDocuments(json.dumps(query))
        print("--- deleted terms:", count, ", query:", query)
        message = " 총 " + str(count) + "개의 documents가 삭제되었습니다."

        # 3) response
        response = JSendResponse(
            status=JSendResponse.Status.SUCCESS,
            message=message
        )
        return JSONResponse(response.json())

    except Exception as ex:
        if debug:
            raise ex
        message = "요청 pattern이나 DIMS에 오류가 있습니다. 확인 후 다시 시도하여 주시기 바랍니다."
        response = JSendResponse(
            status=JSendResponse.Status.ERROR,
            message=message
        )
        return JSONResponse(response.json())


# --------------------------------------------------------------------------------------------
#
#                                       Error Code
#
#  1)get_Terminology()        :  용어 검색(검색 요청 형식)
#     매치되는 단어 찾기  (예)["진입", "신호"]] = > 진입, 신호, 진입신호
#     문자가 포함된 용어  (예) % 진입 = > 진입, 역진입
#     문자로 시작되는 용어 (예) ^ 진입 = > 진입, 진입신호
#     query 문장 자체    (예) {"$or": [{"text": "진입 신호"}, {"category": "Train"}]}
#     기타 : 입력과 일치하는 용어#
#  2) add_new_Terminology()    :  새로운 용어를 DIMS 사전에 insert함
#  3) parameter type
#     문자열
# --------------------------------------------------------------------------------------------


@app.post("/recas/geterrCode")
def get_err_code(request_body: ErrCodeQuery):
    global app, dims, recas, result_cache, debug

    try:
        paradoc = request_body.dict()
        query = dims.build_query_statement("errCode", paradoc["param"])
        docs, count = dims.executeErrorQuery(query)
        print("result of query:", query, " count = ", count)
        return docs
    except Exception as ex:
        if debug:
            raise ex
        return "요청 pattern이나 recas DB(error code)에 오류가 있습니다. 확인 후 다시 시도하여 주시기 바랍니다."


# Not Use
# @app.post("/recas/adderrCode")
# def add_new_errCode(errCodeList: ListNewerrCodeReq):
#     # 예) {"method":"adderrCode",
#     #     "param":[{ "errCode":"1010","description": "str", "correction": "str"}]}
#     paradoc = errCodeList.dict()
#     docList = paradoc["param"]
#     cntReq = len(docList)
#     codedb.connect2Collection(dbName=recasdbName, collectionName=errcodecolName)
#     count = codedb.adderrNewCodeList(docList)
#     print("\n---- add new code. 요청 items :",cntReq," 처리 items 수:",count, " query:",docList)
#     if cntReq == count:
#         return " 요청된 코드(총 " + str(count) + "개)가 모두 DB에 추가되었습니다."
#     else:
#         return " 요청된 코드(총 " + str(cntReq) + "개) 중에서 " + str(count) + "개 코드가 DB에 추가되었습니다."
#
#
# @app.post("/recas/deleteerrCode")
# def delete_errCode(q:DeleteerrCodeQuery):
#     try:
#         paradoc = q.dict()
#         codequery = BuildQueryStatement("errCode",paradoc["errCode"])
#         codedb.connect2Collection(dbName=recasdbName,collectionName=errcodecolName)
#         count = codedb.deleteDocuments(codequery)
#         print("/n----- delete code, query:",codequery," number of deleted documents:",count)
#         return " 총 " + str(count) + "개의 documents가 삭제되었습니다."
#     except:
#         return "요청 pattern이나 error code db에 오류가 있습니다. 확인 후 다시 시도하여 주시기 바랍니다."


@app.post("/recas/synchronize")
def synchronize_word_log():
    try:
        # 1) TTC로 보낼 메세지 작성
        url_ = tcc_address
        update_term_list = dims.get_commit_data()
        request_body = DefaultBody(
            method="updateTerm",
            param=UpdateTermParam(term_data=update_term_list)
        )
        # 2) TTC로 전송
        requests.post(url_ + "updateTerm", request_body.json(), timeout=5)

        # 3) 에러가 없다면 캐시 업데이트
        dims.apply_commit(update_term_list.term_data)

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


if __name__ == "__main__":
    import uvicorn
    init()
    uvicorn.run(app, host="0.0.0.0", port=8000)