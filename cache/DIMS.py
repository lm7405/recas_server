# -*- coding: utf-8 -*-

# dims.py
# dims db 초기화

import pandas as pd
from pymongo import MongoClient
import pymongo
import copy
import json
import numpy as np

# TODO


def correct_encoding(dictionary):
    """Correct the encoding of python dictionaries so they can be encoded to mongodb
    inputs
    -------
    dictionary : dictionary instance to add as document
    output
    -------
    new : new dictionary with (hopefully) corrected encodings"""

    new = {}
    for key1, val1 in dictionary.items():
        # Nested dictionaries
        if isinstance(val1, dict):
            val1 = correct_encoding(val1)

        if isinstance(val1, np.bool_):
            val1 = bool(val1)

        if isinstance(val1, np.int64):
            val1 = int(val1)

        if isinstance(val1, np.float64):
            val1 = float(val1)

        new[key1] = val1

    return new


class DIMS:
    """
    DIMS class for initializing dims db.

    Attributes:
        dicdocKeyList (list): List of column names to be recorded in the dictionary.

    """
    # 사전에 기록되는 column 이름
    dicdocKeyList = ["text", "recas_type", "category",
                     "description", "usage",
                     "tokenizer", "tokenizer_type"]

    def __init__(self, mongoHost="localhost", port=27017):
        """
        Initialize the DIMS class.

        Args:
            mongoHost (str): MongoDB host.
            port (int): MongoDB port.

        """
        self.df = None
        self.colLen = 0
        self.host = mongoHost
        self.port = port
        self.dbName = ""
        self.collectionName = ""
        self.db = None
        self.collection = None

        try:
            self.mgc = MongoClient(self.host, self.port)
            print("checking mongod 주소 = ", mongoHost, ":", self.port, self.mgc)
            print("list_database_names:", self.mgc.list_database_names())
        except:
            print(".......MongoClinet 생성 exception. check environment ", self.host, ":", self.port)
            print(".......cmd 창에서 $mongod --dbpath=data/db 실행")
            return
        print(".......Ok to connect to mongodb")
        print("...............................")

    # ----------------------------------------------------------------------
    def loadDictionaryExcel(self, file=None):
        """
        Load the dictionary file as a DataFrame object.

        Args:
            file (str): File name of the dictionary file.

        Returns:
            None

        """
        # 사전 파일을 pandas을 이용하여 load히여 DataFrame으로 만듦
        # self.df     : panda의 DataFrame object임
        # self.cNames : heading 들의 list(dims document의 key로 사용됨
        # self.colLen : self.cNames의 key들 갯수
        if file is None:
            return
        try:
            self.df = pd.read_excel(file, engine='openpyxl')
            self.df.fillna('', inplace=True)
            self.cNames = list(self.df)  # column 이름 리스트
            if self.cNames[0] == "Unnamed: 0":
                del self.cNames[0]
            self.colLen = len(self.cNames)
        except:
            self.df = None
            self.cNames = []
            self.colLen = 0
        return

    # ----------------------------------------------------------------------
    def connect2Collection(self, dbName=None, collectionName=None):
        """
        Connect to the specified database and collection.

        Args:
            dbName (str): Name of the database.
            collectionName (str): Name of the collection.

        Returns:
            pymongo.collection.Collection: Collection object of the specified database and collection.

        """
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

    # -----------------------------------------------------------------------
    def insertDictionary(self,dbName=None,collectionName=None):
        """
        Insert the contents of self.df (words) into MongoDb.

        Args:
        - dbName: str, name of the database to insert to.
        - collectionName: str, name of the collection to insert to.

        Returns:
        - int, number of documents inserted.
        """
        # self.df 의 내용(단어들)을 MongoDb에 저장
        # db: <dbName>, collection:<collection>에 insert 함
        # DataFrame을 dictionary list로 변환한 후, insert 됨
        # return : insert된 doc 갯수
        if dbName is None or collectionName is None:
            return
        try:
            docList = self.__convertDataDrame2List()
            db = self.mgc[dbName]
            col = db[collectionName]
            docList[:] = [correct_encoding(i) for i in docList]
            res = col.insert_many(docList)
            # print("Insert_many:",len(res.inserted_ids))
        except Exception as ex:
            print("\n++++exception in insertDictionary")
            raise ex
        return

    def __convertDataDrame2List(self):
        """
        Convert the dataframe to a list of dictionaries.

        Returns:
        - list, a list of dictionaries containing the data from the dataframe.
        """
        docList = []
        count = len(self.df)
        for k in range(count):
            doc = {}
            for m in range(self.colLen):
                doc[self.cNames[m]] = self.df.iloc[k, m+1]
            docList.append(doc)
        return docList

    def print_DataFrame(self):
        """
        Print the contents of self.df in a list format.

        Returns:
        - None
        """
        try:
            docList = self.__convertDataDrame2List()
            print("---- list from data frame ")
            for k, item in enumerate(docList):
                pass
                # print(k, ":", item)
        except:
            pass

    # ----------------------------------------------------------------------
    def addTermsListDictionary(self, itemList):
        """
        Insert a list of dictionaries into a collection in MongoDb.

        Args:
        - itemList: list, a list of dictionaries to be inserted.

        Returns:
        - tuple, containing the number of documents inserted and the result of the insertion.
        """
        count = 0
        res = None
        try:
            res = self.collection.insert_many(itemList)
            count = len(res.inserted_ids)
        except Exception as ex:
            raise ex
            pass
        return count, res

    # ----------------------------------------------------------------------
    def makedoc2Dict(self, doc):
        """
        Convert a MongoDb document to a Python dictionary.

        Args:
        - doc: dict, a MongoDb document to be converted.

        Returns:
        - dict, the MongoDb document converted to a Python dictionary.
        """
        item = {}
        keys = doc.keys()
        for key in keys:
            if key == '_id': continue
            # _id 까지 sjgsms ruddn, fastAPi main에서 client로 return할 때 문제 발생
            item[key] = doc[key]
        return item

    def executeQuery(self, queryString=None):
        """
        Query a collection in MongoDb.

        Args:
        - queryString: str, a query in the form of a string.

        Returns:
        - tuple, containing the result of the query (a list of dictionaries) and the number of documents in the result.
        """
        # query:
        #     relational operator("$or", "$and" 등),
        #     logical operator("$gt", "$ㅣs" 등) 과 {}. []로 표현된 query 문장임
        # query 예
        #     {"$or":[{"text":"str1"},{"recas_type":"NNGA"}]}
        #     {"text":"string"}           "string" 단어
        #     {"text":{"$regex":"가"}}    "가로 시작하는 단어
        # return
        #     reply : document list
        #     count : 갯수
        reply = []
        query = {}
        if queryString is not None:
            query = json.loads(queryString)
        # print("Query:",query)
        try:
            col = self.collection
            # print("----- before find(query):",query)
            if query == {}:
                docs = col.find()
            else:
                docs = col.find(query)
            docs = col.find(query)
            for doc in docs:
                item = self.makedoc2Dict(doc)
                reply.append(copy.deepcopy(item))
                # print("----- end of find(query):", item)
        except:
            pass
        return reply, len(reply)

    # ----------------------------------------------------------------------
    def updateDocumenmts(self, queryString, setString):
        """
        Update documents in a MongoDb collection.

        Args:
        - queryString: str, a query in the form of a string.
        - setString: str, a document containing the updates in the form of a string.

        Returns:
        - tuple, containing the number of documents matched and the number of documents modified.
        """
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
        """
        Delete documents from a MongoDb collection.

        Args:
        - queryString: str, a query in the form of a string.

        Returns:
        - int, the number of documents deleted.
        """
        # query :  query 때와 같은 형식의 조건이며, 이 조건에 해당하는 document가 삭제됨
        col = self.collection
        query = json.loads(queryString)
        print("----- before delete(query):", query)
        result = col.delete_many(query)
        return result.deleted_count

    # ----------------------------------------------------------------------
    def print_queryNdocs(self, query):
        """
        Print the results of a query in a list format.

        Args:
        - query: str, a query in the form of a string.

        Returns:
        - None
        """
        # find(query)결과를 출력
        if self.dimsStatus == 0:
            return
        list = self.executeQuery(query)
        for k, item in enumerate(list):
            # print("[query]", query, " ", k, ":", item["text"], "\t", item["recas_type"])
            pass
