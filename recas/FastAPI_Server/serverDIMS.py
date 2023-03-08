from typing import Tuple
from cache import DIMS
from cache import errCodeDB
from pydantic import BaseModel
import json


class ServerDIMSConfig(BaseModel):
    db_addr: str
    db_port: int

    recas_db_name: str
    recas_column_name: str

    error_db_name: str
    error_column_name: str

    init_db: bool
    dict_file_path: str


class ServerDims(DIMS.DIMS):
    def __init__(self, config: ServerDIMSConfig, debug: bool):
        super().__init__(mongoHost=config.db_addr, port=config.db_port)
        self.config = config
        self.debug = debug
        self.init_db(check=False)

        collection = self.connect2Collection()
        try:
            collection.find_one()
        except Exception as ex:
            if self.debug:
                raise ex
            else:
                raise Exception("\n+++++ DIMS를 위한  mongod 을 실행한 후, 다시 실행하시기 바랍니다."
                                "\n....err code DB 처리 결과에 주의하시기 바랍니다.")

        # --2-2) recas error code DB 연결
        codedb = errCodeDB.errCodeDB(mongoHost=config.db_addr, port=config.db_port)
        err_collection = codedb.connect2Collection(dbName=config.error_db_name, collectionName=config.error_column_name)
        try:
            err_collection.find_one()
        except Exception as ex:
            if self.debug:
                raise ex
            else:
                raise Exception("\n+++++ err code DB를 위한  mongod 을 실행한 후, 다시 실행하시기 바랍니다."
                                "\n....err code DB 처리 결과에 주의하시기 바랍니다.")

    def init_db(self, check=False):
        # mongodb를 사용하기 위한 모의 환경 시작
        dic_file = self.config.dict_file_path

        if check is False or \
                self.mgc[self.config.recas_db_name][self.config.recas_column_name].list_indexes().alive is False:
            print("Start to init db")
            self.loadDictionaryExcel(file=dic_file)
            self.print_DataFrame()
            self.mgc[self.config.recas_db_name][self.config.recas_column_name].drop()
            self.insertDictionary(dbName=self.config.recas_db_name, collectionName=self.config.recas_column_name)

    # --------------------------------------------------------------------------------------------
    #                      용어 및 오류 코드 검색 query 문장 구성
    # key를 중심으로 검색함
    # key의 종류는 다음과 같음
    #   DIMS의 경우      : "text"    (용어)
    #   적합성 오류의 경우 : "errCode" (코드)
    # --------------------------------------------------------------------------------------------
    @staticmethod
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

    def connect2Collection(self, db_name=None, collection_ame=None):
        if db_name is None:
            db_name = self.config.recas_db_name
        if collection_ame is None:
            collection_ame = self.config.recas_column_name
        return super().connect2Collection(dbName=db_name, collectionName=collection_ame)

    def addTermsListDictionary(self, item_list):
        term_list_ = []
        for term_ in item_list:
            term_list_.append(term_.dict())
        self.connect2Collection()
        # local_dict_cache().add(TermData.import_(term_list_))
        return super().addTermsListDictionary(term_list_)

    def deleteDocuments(self, query_string):
        self.connect2Collection()
        # local_dict_cache().delete(TermData.import_(param))
        return super().deleteDocuments(query_string)

    def executeErrorQuery(self, query_string=None):
        self.connect2Collection(db_name=self.config.error_db_name, collection_ame=self.config.error_column_name)
        return self.executeQuery(query_string)

    def get_commit_data(self):
        self.connect2Collection()
        query = {"synchronized": False}
        col = self.collection
        docs = col.find(query)
        item_list = []
        for doc in docs:
            item = self.makedoc2Dict(doc)
            del item['synchronized']
            item_list.append(item)
            if len(item_list) > 10:
                break
        return item_list

    def apply_commit(self, update_term_list: list):
        for term in update_term_list:
            synchronized = {'synchronized': True}

            query = {"text": term.text}
            setObject = {"$set": synchronized}

            col = self.collection
            print("----- before update(query):", query, " ", setObject)
            col.update_one(query, setObject, upsert=False)
