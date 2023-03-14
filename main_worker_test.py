# -*- coding: utf-8 -*-

import os
import sys
from cache import DIMS

import cache.recasworkers as recasworkers
import cache.recasworkers_ys4 as recasworkers_ys4
from recas.Utill import RecasMission

cwdir = os.getcwd()
sys.path.append(cwdir)


def get_dims():
    """
    This function loads DIMS dictionary from an Excel file and inserts it into a MongoDB collection.

    Returns:
        instance of dims class
    """
    # mongodb를 사용하기 위한 모의 환경 시작
    dic_file = "data\\DimsWordsDict-210919_0.xlsx"
    dims = DIMS.DIMS(mongoHost="localhost", port=27017)

    dims.loadDictionaryExcel(file=dic_file)
    dims.print_DataFrame()
    db_name = "dimsTermDic"
    col_name = "dictionary"
    dims.mgc[db_name][col_name].drop()
    dims.insertDictionary(dbName=db_name, collectionName=col_name)
    collection = dims.connect2Collection(dbName=db_name, collectionName=col_name)
    return dims


if __name__ == "__main__":
    os.environ["JAVA_HOME"] = "external/jdk-17"
    os.environ["path"] = "external/Graphviz/bin"

    # 에러
    missionQ, resultQ, workers = recasworkers_ys4.Create_WorkerProcesses()

    m1 = RecasMission.RunSentences(["고양이는 강아지를"])
    m2 = RecasMission.RunSentences(["강아지는 고양이를"])
    m3 = RecasMission.RunSentences(["문장"])
    print("[in main] after mission.put()")
    missionQ.put(m1)
    missionQ.put(m2)
    r = resultQ.get(block=True)
    print("in main, after q.get:", r)
    recasworkers.Terminate_Workers_Wait(missionQ, len(workers))
