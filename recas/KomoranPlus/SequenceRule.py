# -*- coding: utf8 -*-

from openpyxl import load_workbook
import jamo


class RuleClass:
    """
    Sequence Rule을 적용하는 클래스
    """
    word_dict_default = {
        "NNG": "NNGA",
        "NNP": "NNPA",
        "VA": "VVA",
        "VV": "VVA",
        'NNB': "NNPA",
        "SW": "QNT",
        "VCN": "VVA",
    }

    def __init__(self, rule_id, word_dict=None):
        """
        룰 클래스의 초기화
        Args:
            rule_id: 룰이 저장된 경로
            word_dict: 변환에 사용하는 단어사전
        """
        # 룰트리 구성 전 룰의 raw_data 테이블 입니다.
        self.rule_table = None
        # 빠른 검색을 위해 구성된 룰 트리입니다.
        self.rule_tree = None
        self.SelectKey = "mod_seq"
        self.NoneCareKey = None
        self.rule_table = []
        self.rule_tree = []
        self.tags = []
        self.word_dict = word_dict

        self.rule_table += self.__load_rule_from_xlsx(rule_id)

    def append_rule_tree(self, rile_tree):
        """
        룰 트리에 룰을 후순위로 추가
        Args:
            rile_tree: 추가되는 룰

        Returns:
            None
        """
        self.rule_tree += rile_tree

    def __load_rule_from_xlsx(self, rule_id):
        """
        특정 포멧의 엑셀로 작성된 룰을 불러와 룰트리로 파싱
        Args:
            rule_id:
                룰이 저장된 경로
        Returns:
            생성된 룰 트리
        """

        def xlsx_str2tuple(line_str):
            """
            룰이 작성된 엑셀을 파싱하는 규칙
            Args:
                line_str: 셀의 문자열

            Returns:
                튜플로 파싱된 문자열
            """
            output = []
            token_str_list = line_str[1:-1].split("], [")
            for token_str in token_str_list:
                tokens = token_str[1:-1].split("\", \"")
                output.append((tokens[0], tokens[1]))
            return output

        sub_rule = []
        rule = [sub_rule]

        if rule_id.split(".")[-1] != "xlsx":
            raise Exception("RecasRule.py - load_rule: invalid rule_id")
        load_wb = load_workbook(rule_id, data_only=True)
        load_ws = load_wb['Sheet1']
        all_rows = load_ws

        # row 길이에 대한 예외처리 필요
        for row in all_rows:
            key = row[1].value
            if key is None or key[0] == '#':
                pass

            elif key[0] == '<':
                sub_rule = []
                rule.append(sub_rule)

            elif key[0] == '[':
                input_seq = row[1].value
                output_seq = row[3].value
                input_seq = xlsx_str2tuple(input_seq)
                output_seq = xlsx_str2tuple(output_seq)
                sub_rule.append((input_seq, output_seq))

        return rule

    @staticmethod
    def __check_nonecare(key: str) -> bool:
        """
        None Care 문자인지 확인하는 함수
        Args:
            key: None care 확인 대상 함수

        Returns:
            인 결과

        """
        try:
            if key[0] == "#":
                return True
            else:
                return False
        except:
            return False

    def __ruletree_add(self, rule_tree, ori_seq, mod_seq):
        """
        룰 트리에 Child를 추가하는 함수
        Args:
            rule_tree: 구성 대상 트리
            ori_seq: 룰 규칙 중 오리지널 시퀀스
            mod_seq: 룰 규칙 중 수정 시퀀스

        Returns:
            None

        """
        ori_pos = 0
        while len(ori_seq) > ori_pos:
            new_key = ori_seq[ori_pos]
            if self.__check_nonecare(new_key[0]):
                new_key = (self.NoneCareKey, new_key[1])
            else:
                new_key = (new_key[0], new_key[1])
            if new_key not in rule_tree.keys():
                rule_tree[new_key] = {}
            rule_tree = rule_tree[new_key]
            ori_pos += 1
        else:
            rule_tree[self.SelectKey] = (ori_seq, mod_seq)

    def __make_rule_tree(self):
        """
        불러온 룰 파일 데이터로부터 룰 트리 구성을 시작하는 함수
        Returns:
            None

        """
        self.rule_tree = []
        try:
            for sub_rule in self.rule_table:
                rule_tree_sub = {}

                for ori_seq, mod_seq in sub_rule:
                    self.__ruletree_add(rule_tree_sub, ori_seq, mod_seq)
                    # 임시코드
                    for item in mod_seq:
                        if item[1] not in self.tags:
                            self.tags.append(item[1])
                self.rule_tree.append(rule_tree_sub)
        except Exception as e:
            print("룰트리 구성 중 에러 발생")
            raise (e)

    # ---------------------------------------------------------------------------------------------------
    # 코모란 출력인 input_seq의 형태소들에 품사변환 규칙을 적용하며 품사를 변환함
    # conver() : 외부에서 호출하는 함수
    # __  함수들은 모두 내부 함수들임

    def convert(self, input_seq, err_chk_list=None):
        """
        시퀀스에 룰을 적용하여 변환 결과를 출력하는 함수
        Args:
            input_seq: 룰을 적용할 시퀀스
            err_chk_list: 해당 리스트에 변환 결과의 tag가 없을 시 에러로 취급

        Returns:
            변환 결과
        """
        # 사전(mongoDB)에 등록된 단어들에 대한 tag 변환
        if self.word_dict is not None:
            input_seq_dict_applied = []
            for token in input_seq:
                input_seq_dict_applied.append(token)
                if token[0] in self.word_dict:
                    word_data = self.word_dict[token[0]]
                    if word_data["tokenizer_type"] == token[1]:
                        input_seq_dict_applied[-1] = (token[0], word_data["recas_type"])

        # 사전을 사용하지 않을 시, 명사, 동사에 대한 기본 변환
        else:
            input_seq_dict_applied = []
            for token in input_seq:
                input_seq_dict_applied.append(token)
                if token[1] in self.word_dict_default:
                    input_seq_dict_applied[-1] = (token[0], self.word_dict_default[token[1]])

        token_list = self.__ruletree_search(input_seq)

        if err_chk_list is not None:
            for token in token_list:
                if token[1] not in err_chk_list:
                    tmp_str = ""
                    for token_ in input_seq:
                        token_tag = token_[0]
                        tmp_str += token_tag
                    return [(tmp_str, "ERR")]

        return token_list

    # self.rule_tree에 등록된 rule tree들을 차례대로 적용함
    # 각 rule tree 들은 차례대로 적용, 즉 단계별로 적용되는 규칙들임
    def __ruletree_search(self, input_seq):
        """
        룰 트리를 순회하여 적용되는 룰을 찾아 변환하는 함수
        Args:
            input_seq:
                룰을 적용할 시퀀스
        Returns:
            변환 결과

        """
        output = []
        output.append(input_seq)
        try:
            tmp = input_seq
            for rule_tree_sub in self.rule_tree:
                tmp = self.__ruletree_apply(rule_tree_sub, tmp)
                output.append(tmp)
            return output[-1]
        except Exception as e:
            print("rule.__ruletree_search: 에러 발생")
            raise (e)

    # 규칙 tree에 등록된 규칙에 적용되는 token의 품사를 변경함
    def __ruletree_apply(self, rule_tree_sub, input_seq):
        """
        선택된 룰트리에 대하여 해당되는 룰을 찾아 적용하는 함수
        Args:
            rule_tree_sub: 적용할 룰 트리
            input_seq: 룰을 적용할 시퀀스

        Returns:
            룰이 적용된 결과

        """
        in_pos = 0
        output_seq = []
        input_len = len(input_seq)
        while in_pos < input_len:
            found_rule = self.__ruletree_find_rule(rule_tree_sub, input_seq, in_pos)  # 해당되는 가장 긴 룰 탐색
            if len(found_rule[0]) != 0:  # 매치되는 rule 을 찾았음
                output_seq += self.__group_nonecare_key(input_seq, in_pos, found_rule)
                in_pos += len(found_rule[0])
            else:  # 룰을 찾지 못함
                output_seq.append(input_seq[in_pos])
                in_pos += 1
        return output_seq

    # in_seq의 in_pos부터 매치되는 규칙 중 가장 긴 규칮을 찾음
    def __ruletree_find_rule(self, rule_tree_sub, input_seq, in_pos):
        """
        룰 트리에서 룰 검색 시 겹치는 룰 중 적합한 룰을 찾는 합수
        Args:
            rule_tree_sub: 적용할 룰 트리
            input_seq: 룰을 적용할 시퀀스
            in_pos: 현재 순회중인 위치

        Returns:
            탐색된 룰

        """
        found_rule = ([], [])
        work_queue = []
        tp_pos = 0
        searching_tree = rule_tree_sub
        length = len(input_seq)
        while (True):
            if in_pos + tp_pos < length:
                # 토큰이 룰과 일치할 경우
                if (input_seq[in_pos + tp_pos][0], input_seq[in_pos + tp_pos][1]) in searching_tree:
                    work_queue.append(
                        (tp_pos + 1, searching_tree[(input_seq[in_pos + tp_pos][0], input_seq[in_pos + tp_pos][1])]))
                # 토큰이 룰과 일치할 경우
                if (self.NoneCareKey, input_seq[in_pos + tp_pos][1]) in searching_tree:
                    work_queue.append((tp_pos + 1, searching_tree[(self.NoneCareKey, input_seq[in_pos + tp_pos][1])]))
            # 길이가 긴 룰을 우선시
            if self.SelectKey in searching_tree:
                if len(found_rule[0]) < tp_pos:
                    found_rule = searching_tree[self.SelectKey]
            # 작업을 끝낸 경우 종료
            if len(work_queue) == 0:
                break
            # 다음 작업 할당
            tp_pos, searching_tree = work_queue.pop()
        return found_rule

    def __group_nonecare_key(self, input_seq, in_pos, found_rule):
        """
        None Care 문자열들을 룰 문자열에 적용하여 None Care Key를 문자열로 변환
        Args:
            input_seq: 룰을 적용할 시퀀스
            in_pos: 현재 순회중인 위치
            found_rule: 탐색된 룰

        Returns:
            None Care Key가 변환된 문자열

        """
        ori_seq = found_rule[0]
        mod_seq = found_rule[1]
        out_seq = []
        dic = {}
        for i, item in enumerate(ori_seq):
            if self.__check_nonecare(item[0]):
                if item[0] not in dic:
                    dic[item[0]] = input_seq[in_pos + i][0]
                else:
                    dic[item[0]] += input_seq[in_pos + i][0]
        for item in mod_seq:
            tmp_str = ""
            if len(item[0]) > 1:
                for item_str in item[0].split("+"):
                    if item_str in dic:
                        tmp_str += dic[item_str]
                    else:
                        tmp_str += item_str
            else:
                tmp_str += item[0]

            if len(item) == 3:
                out_seq.append((tmp_str[:], item[1], item[2]))
            else:
                out_seq.append((tmp_str[:], item[1]))
        return out_seq

    def ruletree_search_check(self, token_input, rule_tree_sub):
        """
        미사용 함수
        """
        for token_rule in rule_tree_sub.keys():
            if token_input is token_rule:
                return True  # 토큰과 품사 모두 일치할 경우
            elif token_rule[0] is self.NoneCareKey and token_input[1] is token_rule[1]:
                return True  # rule의 토큰은 NoneCare이고 품사는 일치할 경우

        return False
