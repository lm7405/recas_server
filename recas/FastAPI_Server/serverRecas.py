import os
import shutil
from pydantic import BaseModel
from recas.Utill import Recas
from typing import List, Any
import multiprocessing

from . import serverDIMS
from . import structure
from recas.Utill import RecasMission
from recas.Utill import get_recas_process_class


class ServerRecasWorkerConfig(BaseModel):
    use_worker: bool
    num_workers: int
    num_sentences: int

    server_dims_config: serverDIMS.ServerDIMSConfig


class ServerRecasConfig(BaseModel):
    mfile_path: str
    komop_tag_path: str
    chunk_tag_path: str
    chunk_rule_path: str
    komop_rule_path: str
    user_dict_path: str
    result_path: str
    worker_config: ServerRecasWorkerConfig


class ServerRecas:
    recas: Recas
    recas_worker: "Worker"

    def __init__(self, config: ServerRecasConfig, dims, debug):
        try:
            # recas 를 위한 환경 변수 설정
            os.environ["JAVA_HOME"] = "external/jdk-17"
            os.environ["path"] = "external/Graphviz/bin"

            self.config = config
            self.debug = debug
            self.dims = dims

            self.use_worker = self.config.worker_config.use_worker

            self.is_recas_initialized = False
            self.make_class()
            self.init()

        except Exception as ex:
            if debug:
                raise ex
            else:
                raise Exception("++++ recas 초기화를 실패하였습니다")

    def make_class(self):
        if self.use_worker:
            self.recas_worker = Worker(self.config)
        else:
            self.recas = Recas(
                chunk_rule_path=self.config.chunk_rule_path,
                komop_rule_path=self.config.komop_rule_path,
                komop_tag_path=self.config.komop_tag_path,
                chunk_tag_path=self.config.chunk_tag_path,
                user_dict_path=self.config.user_dict_path,
                dims=self.dims,
                load_model_path=self.config.mfile_path
            )

    def init(self):
        try:
            if self.use_worker:
                pass
            else:
                self.clear_result()
                self.recas.init_thread()
            self.is_recas_initialized = True
            return True

        except Exception as ex:
            recas = None
            self.is_recas_initialized = False
            raise ex

    def clear_result(self):
        result_path = self.config.result_path
        if os.path.isdir(result_path):
            shutil.rmtree(result_path)
            os.mkdir(result_path)

    def run_sentence(self, sentence):
        if self.use_worker:
            requirements = structure.RecasRequirement2(pm_ID="common", req_ID=None, req_str=sentence)
            output = self.recas_worker.run_sentence_list([requirements])
        else:
            output = self.recas.make_recas_sentence(sentence, result_path=self.config.result_path)
        return output

    def run_sentences(self, requirements: List[structure.RecasRequirement2]) -> List[dict]:
        if self.use_worker:
            output = self.recas_worker.run_sentence_list(requirements)
        else:
            output = []
            for requirement in requirements:
                output.append(self.recas.make_recas_sentence(
                    sentence=requirement.req_str,
                    result_path=self.config.result_path,
                    pm_id=requirement.pm_ID
                ))
        return output

    def add_dict(self, term_dict):
        if self.use_worker:
            raise
        else:
            self.recas.komop_tokenizer.add_dict(term_dict)

    def remove_dict(self, term_dict):
        if self.use_worker:
            raise
        else:
            self.recas.komop_tokenizer.remove_dict(term_dict)

    def modify_dict(self, term_dict):
        if self.use_worker:
            raise
        else:
            raise


# no_dict_rule_path: "data\\sample\\no_dict_rule.xlsx"
class Worker:
    missionQ: multiprocessing.JoinableQueue
    resultQ: multiprocessing.Queue
    workers: List["RecasWorker"]
    config: ServerRecasConfig

    def __init__(self, config: ServerRecasConfig):  # config: ServerRecasConfig, dims, no_dict_rule_path, debug):
        self.config = config
        self.Create_WorkerProcesses()

    def run_sentence_list(self, requirements: List[structure.RecasRequirement2]):
        for requirement in requirements:
            checking_input = RecasMission.CheckingInput(sentence=requirement.req_str, pm_id=requirement.pm_ID)
            mission = RecasMission.RunSentence(checking_input)
            self.missionQ.put(mission)
        r = []
        for requirement in requirements:
            r.append(self.resultQ.get(block=True))
        return r

    def add_term(self, term_dict):
        mission = RecasMission.AddDict(term_dict)
        self.missionQ.put(mission)
        r = self.resultQ.get(block=True)
        return r

    def remove_term(self, term_dict):
        mission = RecasMission.RemoveDict(term_dict)
        self.missionQ.put(mission)
        r = self.resultQ.get(block=True)
        return r

    # ---------------------------------------------------------
    # 각 consumer task 종료
    # (참고)
    #     worker는 None을 받으면 종료함
    #     (RecasWorker.run() 참조)
    # ---------------------------------------------------------
    def terminate_workers_wait(self):
        for i in range(len(self.workers)):
            self.missionQ.put(None)
        self.missionQ.join()

    # ---------------------------------------------------------
    def Create_WorkerProcesses(self):
        # Worker와 main 간 communication channel 구축
        #   main   =>  worker : multiprocessing.Joinablequeues
        #   worker =>  main   : multiprocessing.queue
        self.missionQ = multiprocessing.JoinableQueue()
        self.resultQ = multiprocessing.Queue()

        max_num_cores = multiprocessing.cpu_count()  # num_cores: core의 수
        num_cores = self.config.worker_config.num_workers
        if num_cores == 0:
            num_cores = max_num_cores
        num_cores = min(num_cores, max_num_cores)
        if num_cores <= 2:
            num_consumers = 1
        else:
            num_consumers = num_cores - 1  # 작업 환경에 따라 가변

        self.workers = [RecasWorker(self.missionQ, self.resultQ, self.config)
                        for i in range(num_consumers)]
        print("[worker process]", len(self.workers), " 개 병렬 worker가 생성됨")
        for w in self.workers:
            w.start()


# -----------------------------------------------------------------
#  각 core에서 병렬로 실행되는 worker process
#  (참고)
#    worker - master 간 주고 받는 자료의 규모에 따라 전략적 접근이 필요함
#    예를 들면 묶어서 하나의 mission 으로 전달
#    즉 한 mission에 여러 개의 동일 작업을 저장하여 전달함
# -----------------------------------------------------------------
class RecasWorker(multiprocessing.Process):
    process_class: any

    def __init__(self, missionQ, resultQ, config: ServerRecasConfig):
        multiprocessing.Process.__init__(self)
        self.missionQ = missionQ
        self.resultQ = resultQ
        self.config = config
        self.process_class = None

    # process main 함수
    def run(self):
        if self.process_class is None:
            dims_config = self.config.worker_config.server_dims_config
            dims = serverDIMS.ServerDims(dims_config, debug=False)
            recas_init_data = {
                    "mfile_path": self.config.mfile_path,
                    "komop_tag_path": self.config.komop_tag_path,
                    "chunk_tag_path": self.config.chunk_tag_path,
                    "chunk_rule_path": self.config.chunk_rule_path,
                    "komop_rule_path": self.config.komop_rule_path,
                    "user_dict_path": self.config.user_dict_path,
                    "DIMS": dims
                }
            self.process_class = get_recas_process_class(recas_init_data)
            # self.process_class = self.get_dummy_process_class(recas_init_data)

        proc_name = self.name
        print("\t..[worker] ", proc_name, " 실행 시작함, mission 대기함")
        while True:
            next_mission = self.missionQ.get(block=True)
            if next_mission is None:
                self.missionQ.task_done()
                break
            answer = next_mission(self.process_class)    # Mission object 호출(__call__() 실행)
            self.missionQ.task_done()  # single mission이 끝남을 알림
            self.resultQ.put(answer)   # mission 수행 결과를 보냄
        print("\t..[worker] ", proc_name, ": 모든 mission 처리하고 종료함")
        return

    def get_dummy_process_class(self, recas_init_data):
        print(recas_init_data)
