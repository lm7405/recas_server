import multiprocessing
import time


# -----------------------------------------------------------------
#  각 core에서 병렬로 실행되는 worker process
#  (참고)
#    worker - master 간 주고 받는 자료의 규모에 따라 전략적 접근이 필요함
#    예를 들면 묶어서 하나의 mission 으로 전달
#    즉 한 mission에 여러 개의 동일 작업을 저장하여 전달함
# -----------------------------------------------------------------
class RecasWorker(multiprocessing.Process):
    def __init__(self, missionQ, resultQ, recas_class):
        multiprocessing.Process.__init__(self)
        self.missionQ = missionQ
        self.resultQ = resultQ
        self.recas_class = recas_class
        self.recas_class.init_thread()

    # process main 함수
    def run(self):
        proc_name = self.name
        print("\t..[worker] ", proc_name, " 실행 시작함, mission 대기함")
        while True:
            next_mission = self.missionQ.get(block=True)
            if next_mission is None:
                self.missionQ.task_done()
                break
            answer = next_mission(self.recas_class)    # Mission object 호출(__call__() 실행)
            self.missionQ.task_done()  # single mission이 끝남을 알림
            self.resultQ.put(answer)   # mission 수행 결과를 보냄
        print("\t..[worker] ", proc_name, ": 모든 mission 처리하고 종료함")
        return


# ---------------------------------------------------------
def Create_WorkerProcesses(recas_class):
    # Worker와 main 간 communication channel 구축
    #   main   =>  worker : multiprocessing.Joinablequeues
    #   worker =>  main   : multiprocessing.queue
    missionQ = multiprocessing.JoinableQueue()
    resultQ = multiprocessing.Queue()

    num_cores = multiprocessing.cpu_count()         # num_cores: core의 수
    if num_cores <= 2:
        num_consumers = 1
    else:
        num_consumers = num_cores - 1                # 작업 환경에 따라 가변
    workers = [RecasWorker(missionQ, resultQ, recas_class)
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

