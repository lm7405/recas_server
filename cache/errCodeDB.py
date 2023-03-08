# errCodeDb.py
# errocr code db 초기화

import pandas as pd
from pymongo import MongoClient
import copy
import json


class errCodeDB:
    # 사전에 기록되는 column 이름
    dicdocKeyList = ["errCode", "description", "correction"]

    def __init__(self,mongoHost="localhost",port=27017):
        self.df = None
        self.colLen = 0
        self.host = mongoHost
        self.port = port
        self.dbName = ""
        self.collectionName = ""
        self.db = None
        self.collection = None

        try:
            pass
            self.mgc = MongoClient(self.host,self.port)
            print("checking mongod 주소 = ",mongoHost,":",self.port, self.mgc)
            print("list_database_names:",self.mgc.list_database_names())
        except:
            print(".......MongoClinet 생성 exception. check environment ",self.host,":",self.port)
            print(".......cmd 창에서 $mongod --dbpath=data/db 실행")
            return
        print(".......Ok to connect to mongodb")
        print("...............................")


    #----------------------------------------------------------------------
    def loaderrCodeExcel(self,file=None):
        # error code 파일을 pandas을 이용하여 DataFrame으로 만듦
        # self.df     : panda의 DataFrame object임
        # self.cNames : heading 들의 list(errdb document의 key로 사용됨)
        # self.colLen : self.cNames의 key들 갯수
        if file == None:
            return
        try:
            self.df = pd.read_excel(file,dtype={'errCode':str})
            self.df.fillna('', inplace=True)
            # NaN 삭제
            self.df = self.df.dropna(subset=['errCode'])
            self.cNames = list(self.df)  # column 이름 리스트
            if self.cNames[0] == "Unnamed: 0":
                del self.cNames[0]
            self.colLen = len(self.cNames)
        except:
            self.df = None
            self.cNames = []
            self.colLen = 0
        return


    #----------------------------------------------------------------------
    def connect2Collection(self,dbName=None,collectionName=None):
        # self.db, seld.collection을 세팅하고 collection을 return함
        # collection은 일련의 query에서 사용할 수 있음
        if dbName == None or collectionName == None:
            return None
        try:
            self.dbName = dbName
            self.collectionName = collectionName
            self.db = self.mgc[self.dbName]
            self.collection = self.db[self.collectionName]
            return self.collection
        except:
            self.dbName = ""
            self.collectionName = ""
            return None

    #-----------------------------------------------------------------------
    def inserterrCode(self,dbName=None,collectionName=None):
        # self.df 의 내용(단어들)을 MongoDb에 저장
        # db: <dbName>, collection:<collection>에 insert 함
        # DataFrame을 dictionary list로 변환한 후, insert 됨
        # return : insert된 doc 갯수
        if dbName == None or collectionName == None:
            return
        try:
            docList = self.__convertDataFrame2List()
            db = self.mgc[dbName]
            col = db[collectionName]
            res = col.insert_many(docList)
            print("Insert_many:",len(res.inserted_ids))
        except:
            print("\n++++exception in inserterrCode()")
        return
    def __convertDataFrame2List(self):
        docList = []
        count = len(self.df)
        for k in range(count):
            doc = {}
            for m in range(self.colLen):
                doc[self.cNames[m]] = self.df.iloc[k,m+1]
            docList.append(doc)
        return docList
    def print_DataFrame(self):
        try:
            docList = self.__convertDataDrame2List()
            print("---- list from data frame ")
            for k, item in enumerate(docList):
                print(k, ":", item)
        except:
            pass

    #----------------------------------------------------------------------
    def adderrNewCodeList(self,itemList):
        count = 0
        try:
            res = self.collection.insert_many(itemList)
            count = len(res.inserted_ids)
        except:
            pass
        return count
    #----------------------------------------------------------------------
    def makedoc2Dict(self,doc):
        item = {}
        keys = doc.keys()
        for key in keys:
            if key == '_id': continue
            # _id 까지 reply에 넣는 경우, fastAPi main에서 client로 return할 때 문제 발생
            item[key] = doc[key]
        return item
    def executeQuery(self, queryString):
        # query:
        #     relational operator("$or", "$and" 등),
        #     logical operator("$gt", "$ㅣs" 등) 과 {}. []로 표현된 query 문장임
        # query 예
        #     {"$or":[{"errCode":"1010"},{"description":"주어"}]}
        #     {"errCode":"1010"}               "1010" 단어
        #     {"errCode":{"$regex":"10"}}    "10"로 시작하는 단어
        # return
        #     reply : document list
        #     count : 갯수
        reply = []
        query = json.loads(queryString)
        print("Query:",query)
        try:
            col = self.collection
            #print("----- before find(query):",query)
            docs = col.find(query)
            for doc in docs:
                item = self.makedoc2Dict(doc)
                reply.append(copy.deepcopy(item))
                #print("----- end of find(query):", item)
        except:
            pass
        return reply, len(reply)

    # ----------------------------------------------------------------------
    def updateDocumenmts(self,queryString,setString):
        # query :  query 때와 같은 형식의 조건이며, 이 조건에 해당하는 document가 수정됨
        # setString : 수정할 값들을 정의하는 document
        # (setString 예) { "key1": value, "key2":value }처럼 key와 값들 dict 구조임
        query = json.loads(queryString)
        setValueDic = json.loads(setString)
        setObject = {"$set": setValueDic}
        try:
            col = self.collection
            print("----- before update(query):",query," ", setObject)
            result = col.update_many(query,setObject,upsert=False)
            return result.matched_count, result.modified_count
        except:
            pass
        return 0

    # ----------------------------------------------------------------------
    def deleteDocuments(self,queryString):
        # query :  query 때와 같은 형식의 조건이며, 이 조건에 해당하는 document가 삭제됨
        try:
            col = self.collection
            query = json.loads(queryString)
            print("----- before delete(query):",query)
            result = col.delete_many(query)
            print("----- after delete(query) count:", result.deleted_count)
            return result.deleted_count
        except:
            pass
        return 0

    # ----------------------------------------------------------------------
    def print_queryNdocs(self,query):
        # find(query)결과를 출력
        if  self.errdbStatus == 0:
            return
        list = self.executeQuery(query)
        for k, item in enumerate(list):
            print("[query]",query," ", k,":",item["errCode"], "\t",item["description"])
