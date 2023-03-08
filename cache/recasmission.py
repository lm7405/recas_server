'''
  1. Parallel Processing을 위한 Algorithm

    1) fastAPI는  RESTful API로 request를 받음(1차년도에서와 동일함)
    2) fastAPI는  request recasReq 를 바탕으로 Recas_Mission instance를 생성
       (방법) mission = Recas_Mission(recas, recasReq)
       (설명)
            recas는 request를 처리할 당시의 recas 객체임.
            모든 변수는 recas 객체가 저장하여야 함.
            ( 1차년도에서 fastAPI는 class RecasUtill의 instance이며
            rc = recas.RecasUtil.RecasUtill() 으로 recas instance를 만든 후에
            rc.run_sentence(req["req_str"], path=result_path)로 적합성을 검사하고
            rc.draw_sentence(...) 로 parse tree를 그렸음.
            각 문장마다 mission을 만든 후에 missionQ에 put함
            => parallel worker들에 의하여 processing됨
        (참고)
            parse tree 그리는 작업은 fastAPI가 직접 수행함
    3) queue(MissionQ)에 mission instance를 전달함
       (방법) missionQ.put(mission)
       (설명)
             missionQ는 worker processs가 mission 도착을 기다리는 queue임
    4) worker process는 Recas_Mission instance의 __call__() 함수를 호출
       (방법)
             next_mission = missionQ.get()
             answer = next_mission()  # mission의 __call__()을 호출하게 됨
    5) fastAPI는 resultQ에서 응답을 대기함(여러 worker process로부터 응답 받음)
       (방법)
            result = results.get()
    6) 받은 result를 모아서 사용자에게 응답

  2. Recas_Mission.__call__()
     이전 version1.0 에서 적합성 검사를 한 것과 동일하게 recas 호출화여 적합성 검사를 수행
     req_id를 넣어서 어떤 request인지 구별에 사용토록 함
     (1차년도와 차이점)
        1차년도:  run_data, output, file_name = self.rc.run_sentence
        2차년도:  run_data, output, file_name = self.rc.run_sentence
                 return [req_id, run_data, output, file_name]
                 즉 list 로 return됨
  3. worker process의 활용
     일반적인 체계이며 recas 에만 적용되는 것은 아니다.
     즉, Recas_Mission 과 다른 object 를 missionQ에 put하면
     put된 object의 __call__()이 호출된다.
     그리고 return값은 __call__()이 return한 값이다.
'''

import json
import copy


class Recas_Mission(object):

    def __init__(self, recas, recasReq):
        self.rc = recas            # recas 수행에 필요한 데이터거 모인 object
        self.request = recasReq
        # 사용자 request type : {"req_id":... , "req_str":... ,"path":... }

    def __call__(self):
        # self.request를 처리한 후, 결과를 return함
        # return 값은 worker process 에 의하여 returnQ에 put됨
        req_id = self.request["req_id"]
        run_data, output, file_name = self.rc.run_sentence(self.request["req_str"],
                                                           self.request["path"])
        return [req_id, run_data, output, file_name]

    # __call__을 test에 사용된 함수임
    def call(self): # __call__() 함수를 테스트 용
        return self.__call__()

