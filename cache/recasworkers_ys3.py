import multiprocessing
import time
from recas.Utill import get_recas_process_class


# -----------------------------------------------------------------
#  각 core에서 병렬로 실행되는 worker process
#  (참고)
#    worker - master 간 주고 받는 자료의 규모에 따라 전략적 접근이 필요함
#    예를 들면 묶어서 하나의 mission 으로 전달
#    즉 한 mission에 여러 개의 동일 작업을 저장하여 전달함
# -----------------------------------------------------------------
class RecasWorker(multiprocessing.Process):
    process_class: any

    def __init__(self, missionQ, resultQ, init_data):
        multiprocessing.Process.__init__(self)
        self.missionQ = missionQ
        self.resultQ = resultQ
        self.process_class = None
        self.init_data = init_data
        # self.process_class = get_recas_process_class(init_data)

    # process main 함수
    def run(self):
        if self.process_class is None:
            self.process_class = get_recas_process_class(self.init_data)

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


# ---------------------------------------------------------
def Create_WorkerProcesses(get_process_class_func, process_class_init_data: dict):
    # Worker와 main 간 communication channel 구축
    #   main   =>  worker : multiprocessing.Joinablequeues
    #   worker =>  main   : multiprocessing.queue
    missionQ = multiprocessing.JoinableQueue()
    resultQ = multiprocessing.Queue()

    num_cores = multiprocessing.cpu_count()         # num_cores: core의 수
    num_cores = 3
    if num_cores <= 2:
        num_consumers = 1
    else:
        num_consumers = num_cores - 1                # 작업 환경에 따라 가변
    workers = [RecasWorker(missionQ, resultQ, process_class_init_data.copy())
               for i in range(num_consumers)]
    print("[worker process]", len(workers), " 개 병렬 worker가 생성됨")
    for w in workers:
        w.start()
    return missionQ, resultQ, workers


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

