# -*- coding: utf-8 -*-

import multiprocessing
from recas.Utill import get_recas_process_class
from cache import DIMS


def get_dims():
    # mongodb를 사용하기 위한 모의 환경 시작
    dicFile = "data\\DimsWordsDict-210919_0.xlsx"
    dims = DIMS.DIMS(mongoHost="localhost", port=27017)

    dims.loadDictionaryExcel(file=dicFile)
    dims.print_DataFrame()
    dbName = "dimsTermDic"
    colName = "dictionary"
    dims.mgc[dbName][colName].drop()
    dims.insertDictionary(dbName=dbName, collectionName=colName)
    collection = dims.connect2Collection(dbName=dbName, collectionName=colName)
    return dims


def get_dims_lite():
    dims = DIMS.DIMS(mongoHost="localhost", port=27017)
    return dims


recas_init_data = {
        "mfile_path": 'data\\sample\\model23.h5',
        "komop_tag_path": "data\\sample\\komop_tags.txt",
        "chunk_tag_path": "data\\sample\\chunk_tags.txt",
        "chunk_rule_path": 'data\\sample\\chunk_rule.xlsx',
        "no_dict_rule_path": "data\\sample\\no_dict_rule.xlsx",
        "komop_rule_path": "data\\sample\\komop_rule.xlsx",
        "user_dict_path": "data\\sample\\user_dict.txt",
        "DIMS": get_dims()
    }


# -----------------------------------------------------------------
#  각 core에서 병렬로 실행되는 worker process
#  (참고)
#    worker - master 간 주고 받는 자료의 규모에 따라 전략적 접근이 필요함
#    예를 들면 묶어서 하나의 mission 으로 전달
#    즉 한 mission에 여러 개의 동일 작업을 저장하여 전달함
# -----------------------------------------------------------------
class RecasWorker(multiprocessing.Process):
    process_class: any

    def __init__(self, missionQ, resultQ, wordMission):
        multiprocessing.Process.__init__(self)
        self.missionQ = missionQ
        self.resultQ = resultQ
        self.process_class = None
        self.wordMission = wordMission

    # process main 함수
    def run(self):
        if self.process_class is None:
            self.process_class = get_recas_process_class(recas_init_data)

        proc_name = self.name
        print("\t..[worker] ", proc_name, " worker start")
        while True:
            if "dict_mission" in self.wordMission and proc_name not in self.wordMission:
                print("\t..[worker] ", proc_name, " dict mission start")
                next_mission = self.wordMission["dict_mission"]
                self.wordMission[proc_name] = True
                next_mission(self.process_class)
                print("\t..[worker] ", proc_name, " dict mission end")

            print("\t..[worker] ", proc_name, " mission wait")
            try:
                next_mission = self.missionQ.get(block=True, timeout=1)
                print("\t..[worker] ", proc_name, " get mission")

                if next_mission is None:
                    self.missionQ.task_done()
                    break

                answer = next_mission(self.process_class)    # Mission object 호출(__call__() 실행)
                self.missionQ.task_done()  # single mission이 끝남을 알림
                self.resultQ.put(answer)   # mission 수행 결과를 보냄
                print("\t..[worker] ", proc_name, " mission complete")
            except multiprocessing.queues.Empty as ex:
                pass
        print("\t..[worker] ", proc_name, ": 모든 mission 처리하고 종료함")
        return


# ---------------------------------------------------------
def Create_WorkerProcesses():
    # Worker와 main 간 communication channel 구축
    #   main   =>  worker : multiprocessing.Joinablequeues
    #   worker =>  main   : multiprocessing.queue
    missionQ = multiprocessing.JoinableQueue()
    resultQ = multiprocessing.Queue()
    wordMission = multiprocessing.Manager().dict()

    num_cores = multiprocessing.cpu_count()         # num_cores: core의 수
    # num_cores = 3
    if num_cores <= 2:
        num_consumers = 1
    else:
        num_consumers = num_cores - 1                # 작업 환경에 따라 가변
    workers = [RecasWorker(missionQ, resultQ, wordMission)
               for i in range(num_consumers)]
    print("[worker process]", len(workers), " 개 병렬 worker가 생성됨")
    for w in workers:
        w.start()
    return missionQ, resultQ, wordMission, workers


# ---------------------------------------------------------
# 각 consumer task 종료
# (참고)
#     worker는 None을 받으면 종료함
#     (RecasWorker.run() 참조)
# ---------------------------------------------------------
def Terminate_Workers_Wait(missionQ, num_consumers):
    for i in range(num_consumers):
        missionQ.put(None)
    missionQ.join()

