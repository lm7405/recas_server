from pydantic import BaseModel
import copy
from typing import Dict

from .serverRecas import ServerRecas
from recas.FastAPI_Server.structure import RecasRequirement, RecasRequirement2


class ServerResultCacheConfig(BaseModel):
    max_cache: int


# ---------------------------------------------------------------------------------------
#  검사후 적합하다고 판단된 요구사항 처리결과를 caching 함
#  maxCache: cache의 크기
#  cache 가 차면 FIFO로 replacement 함
# ---------------------------------------------------------------------------------------
class ServerResultCache:
    recas: ServerRecas

    def __init__(self, config: ServerResultCacheConfig, debug: bool):
        self.config = config
        self.debug = debug

        self.reqCache = {}
        self.reqList = []

    def clear(self):
        for key in self.reqCache.keys():
            del(self.reqCache[key])
        del self.reqList[0:-1]
        self.reqCache = {}
        self.reqList = []

    def set_recas(self, recas: ServerRecas):
        self.recas = recas

    def get_image(self, req_id):
        if req_id in self.reqCache.keys():
            file_name = self.reqCache[req_id]["image"]
            print("\n+++ recas/result/image file name:", file_name)
            rd = self.reqCache[req_id]["run_data"]

            self.recas.recas.draw_sentence(
                sentence_chunk=rd["sentence_chunk"],
                parse_tree_restored=rd["parse_tree_restored"],
                parse_tree_err=rd["parse_tree_err"],
                error_list=rd["error_list"],
                save_name=file_name
            )
            file_name = file_name + ".jpg"
            view_file = open(file=file_name, mode='rb')

            html_content = view_file.read()
            view_file.close()

            return html_content

    def get_testcase(self, req_id):
        if req_id in self.reqCache.keys():
            run_data = self.reqCache[req_id]["run_data"]
            return run_data["testcase_text"]
        else:
            return "Invalid requirement ID"

    def save_cache_old(self, output, req: RecasRequirement):
        # reqID는 req["req_ID"], 요구사항은 req["req_str"] 등으로 접근
        # print("ID: ",req["req_ID"], "  요구사항:", req["req_str"])
        # 각 요구사항 별로 적합성 체크 모듈을 호출하여 적합성을 검사하고, return 값을 status에 저장

        print(" image file_name :", output["save_name"])
        req.fullStr = copy.deepcopy(output)
        req.status = len(output["error_list"])
        for k, err in enumerate(output["error_list"]):
            if k == 0:
                req.errors = err[0]
            else:
                req.errors = err[1] + ", " + err[0]
        req.structImage = req.req_ID
        req.key_infos = output["unit_sentence_info"]
        req.nbOfSentences = len(output["unit_sentence_info"])
        # ['req_ID', 'req_str', 'status', 'errors', 'comment',  'structImage', 'fullStr', 'nbOfSentences',
        # 'key_infos']

        print("문장의 수", req.nbOfSentences)
        for s in output["unit_sentence_info"]:
            print("주요정보:", s)
        self.cache_results(req, output, output["save_name"])
        req_dict = {
            "status": req.status,
            "errors": req.errors,
            "structImage": req.structImage,
            "key_infos": req.key_infos,
            "nbOfSentences": req.nbOfSentences,
            "testcase": output["testcase"]
        }

        return req.req_ID, req_dict

    def save_cache(self, checking_result, req: RecasRequirement2):
        # reqID는 req["req_ID"], 요구사항은 req["req_str"] 등으로 접근
        # print("ID: ",req["req_ID"], "  요구사항:", req["req_str"])
        # 각 요구사항 별로 적합성 체크 모듈을 호출하여 적합성을 검사하고, return 값을 status에 저장
        key = req.req_ID + '/' + req.pm_ID

        print(" image file_name :", checking_result["save_name"])
        req.fullStr = copy.deepcopy(checking_result)
        req.status = len(checking_result["error_list"])
        for k, err in enumerate(checking_result["error_list"]):
            if k == 0:
                req.errors = err[0]
            else:
                print(err)
                req.errors = req.errors + ", " + err[0]
        req.structImage = key
        req.key_infos = checking_result["unit_sentence_info"]
        req.nbOfSentences = len(checking_result["unit_sentence_info"])
        # ['req_ID', 'req_str', 'status', 'errors', 'comment',  'structImage', 'fullStr', 'nbOfSentences',
        # 'key_infos']

        print("문장의 수", req.nbOfSentences)
        for s in checking_result["unit_sentence_info"]:
            print("주요정보:", s)
        self.cache_results(req, checking_result, checking_result["save_name"])
        req_dict = {
            "status": req.status,
            "errors": req.errors,
            "structImage": req.structImage,
            "key_infos": req.key_infos,
            "nbOfSentences": req.nbOfSentences,
        }

        return key, req_dict

    def run_recas_2(self, output, req):
        # reqID는 req["req_ID"], 요구사항은 req["req_str"] 등으로 접근
        # print("ID: ",req["req_ID"], "  요구사항:", req["req_str"])
        # 각 요구사항 별로 적합성 체크 모듈을 호출하여 적합성을 검사하고, return 값을 status에 저장

        print(" image file_name :", output["save_name"])
        req.fullStr = copy.deepcopy(output)
        req.status = len(output["error_list"])
        for k, err in enumerate(output["error_list"]):
            if k == 0:
                req.errors = err[0]
            else:
                req.errors = req.req_str + ", " + err[0]
        req.structImage = req.pm_ID + "/" + req.req_ID
        req.key_infos = output["unit_sentence_info"]
        req.nbOfSentences = len(output["unit_sentence_info"])

        print("문장의 수", req.nbOfSentences)
        for s in output["unit_sentence_info"]:
            print("주요정보:", s)
        self.cache_results(req, output, output["save_name"])

        return req.pm_ID + "/" + req.req_ID, copy.deepcopy(req)

    # ---------------------------------------------------------------------------------------
    #  검사후 적합하다고 판단된 요구사항 처리결과를 caching 함
    # ---------------------------------------------------------------------------------------
    def cache_results(self, req, run_data, file_name):
        if len(self.reqCache) >= 200:
            try:
                del self.reqCache[self.reqList[0]]
                self.reqList.pop(0)
            except:
                pass
        self.reqCache[req.req_ID] = {
            "req_ID": req.req_ID,
            "req": copy.deepcopy(req),
            "run_data": run_data,
            "image": file_name,
        }
        self.reqList.append(req.req_ID)
