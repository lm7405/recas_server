from itertools import filterfalse
from recas.FastAPI_Server.structure import *


class UpdatedMethod(str, Enum):
    ADD = 'add'
    MODIFY = 'modify'
    DELETE = 'delete'


class TermDataUpdatedLog(BaseModel):
    method: UpdatedMethod
    term_data: TermData


class RecasCommitBuffer(BaseModel):
    updated_logs: List[TermDataUpdatedLog] = []

    def add(self, term_data: TermData):
        self.updated_logs.append(
            TermDataUpdatedLog(
                method=UpdatedMethod.ADD,
                term_data=term_data
            )
        )

    def modify(self, term_data: TermData):
        self.updated_logs.append(
            TermDataUpdatedLog(
                method=UpdatedMethod.MODIFY,
                term_data=term_data
            )
        )

    def delete(self, term_data: TermData):
        self.updated_logs.append(
            TermDataUpdatedLog(
                method=UpdatedMethod.DELETE,
                term_data=term_data
            )
        )

    def clear(self):
        self.updated_logs[:] = []

    def compress_buffer(self):
        compressed_logs: Dict[str, TermDataUpdatedLog] = {}
        for updated_log in self.updated_logs:
            current_term_data = updated_log.term_data
            if current_term_data.text not in compressed_logs:
                compressed_logs[current_term_data.text] = updated_log
            else:
                current_method = updated_log.method
                old_update_log = compressed_logs[current_term_data.text]
                if current_method in [UpdatedMethod.ADD, UpdatedMethod.MODIFY]:
                    compressed_logs[current_term_data.text] = TermDataUpdatedLog(
                        method=old_update_log.method,
                        term_data=current_term_data
                    )
                elif current_method in [UpdatedMethod.DELETE]:
                    compressed_logs[current_term_data.text] = updated_log
                    # 삭제에 대한 정의 확인 필요
        self.updated_logs[:] = list(compressed_logs.values())

    def get_commit_data(self) -> UpdateTermParam:
        self.compress_buffer()
        commit_data: UpdateTermParam = UpdateTermParam()
        for updated_log in self.updated_logs:
            if updated_log.method != UpdatedMethod.DELETE:
                commit_data.term_data.append(updated_log.term_data)
        return commit_data

    def apply_commit(self, commit_datas: UpdateTermParam):
        def determine(updated_log_: TermDataUpdatedLog):
            if updated_log_.method != UpdatedMethod.DELETE:
                searched = [x for x in commit_datas.term_data if x.text == updated_log_.term_data.text]
                if len(searched) > 0:
                    commit_data = searched[0]
                    if updated_log_.term_data.date < commit_data.date:
                        return True
            return False

        self.compress_buffer()
        self.updated_logs[:] = filterfalse(determine, self.updated_logs[:])
