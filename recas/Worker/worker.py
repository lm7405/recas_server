# -*- coding: utf-8 -*-

import os
import sys
from typing import List
from cache import DIMS

from . import recasworkers
from recas.Utill import Recas, RecasMission, get_recas_process_class

cwdir = os.getcwd()
sys.path.append(cwdir)


def get_dims():
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


class Worker:
    min_worker_sentence_count = 5
    sentence_per_worker = 7

    def __init__(self):
        os.environ["JAVA_HOME"] = "external/jdk-17"
        os.environ["path"] = "external/Graphviz/bin"

        self.missionQ, self.resultQ, self.wordMission, self.workers = recasworkers.Create_WorkerProcesses()

    def run_sentence_list(self, sentence_list: List[str], debug=False, force_not_worker=False):
        sentence_count = len(sentence_list)
        if sentence_count > self.min_worker_sentence_count and not force_not_worker:
            start_index = 0
            for i in range(sentence_count):
                if i - start_index >= self.sentence_per_worker:
                    self.missionQ.put(RecasMission.RunSentences(sentence_list[start_index:i], debug))
                    start_index = i
            self.missionQ.put(RecasMission.RunSentences(sentence_list[start_index:], debug))
        else:
            self.missionQ.put(RecasMission.RunSentences(sentence_list, debug))
        output = []

        self.missionQ.join()
        while len(output) < len(sentence_list):
            output += self.resultQ.get(block=True)
        # print("in main, after q.get:", r)
        return output

    def add_dict(self, word_data):
        self.wordMission["dict_mission"] = RecasMission.AddDict(word_data)

        while len(self.wordMission) != len(self.workers) + 1:
            pass
        del self.wordMission["dict_mission"]
        for key in self.wordMission.keys():
            del self.wordMission[key]

    def update_dict(self, word_data):
        self.wordMission["dict_mission"] = RecasMission.UpdateDict(word_data)

        while len(self.wordMission) != len(self.workers) + 1:
            pass
        del self.wordMission["dict_mission"]
        for key in self.wordMission.keys():
            del self.wordMission[key]

    def remove_dict(self, word_data):
        self.wordMission["dict_mission"] = RecasMission.RemoveDict(word_data)
        while len(self.wordMission) != len(self.workers) + 1:
            pass
        del self.wordMission["dict_mission"]
        for key in self.wordMission.keys():
            del self.wordMission[key]

    def delete(self):
        recasworkers.Terminate_Workers_Wait(self.missionQ, len(self.workers))

