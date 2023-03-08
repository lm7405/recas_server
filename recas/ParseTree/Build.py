# -*- coding: utf8 -*-

# ---------------------------------------- ... ---
# 1. 버전
#  1) 버전 코드		: 1.0.0
#  2) 최종 수정 날짜	: 220603
#  3) 최종 수정자	    : 아주대학교
#
# 2. 코드 목적
#  - recas 라이브러리의 사용자 기능을 함수로 제공함
#
#
# 4. 공개 함수 설명
#  - initialize(data_path, rule_file_path=None, dict_file_path=None):
#    수정된 rule 또는 dict를 적용할 필요가 있을 때 사용하는 함수
#    RecasUtill 클래스 내부적으로 초기화되며 반환값은 없음
#
#  - run_sentence(ori_sentence, path="result")
#    문장을 입력받아 run_data, output, file_name를 출력하는 함수
#    run_data: recas 분석 수행 중에 생성된 단계별 데이터. dictionary
#
#
# 5. 외부 라이브러리 의존성
#  - json
#
# ---------------------------------------- ... ---


from .Structure import *


def build_parse_tree(recas_sentence: List[Tuple[Tuple[str, str], List[Tuple[str, str]]]]) \
        -> Tuple[List[RPTItemSub], List[RPTItemSentence]]:
    """
    정해진 규칙에 따라 Parse Tree를 구성
    Args:
        recas_sentence: 토크나이저가 작용된 문장

    Returns:
        Parse Tree로 구성된 문장
    """

    CHUNKTAG_SENTENCE_END: List = ["VVCG", "VVCL", "VVCE", "VVCC", "VVTG", "VVTL", "VVTE", "VVTC", "VVEL", "VVEC", "VVEG"]
    CHUNKTAG_LIST_END: List = ["SUB", "OBJ", "ADV", "NNPG", "MOD", "TIMB"]
    CHUNKTAG_LIST: List = ["NNPL", "VVCL", "VVTL", "VVEL"]
    CHUNKTAG_NOUN = ["SUB", "OBJ", "ADV", "NNPG", "NNPL", "QNT", "TIMB", "TIMG", "TIMS", "TIMO", "TOPRN"]

    CHUNKTAG_MOD_NOUN = ("VVCG", "VVTG", "VVEG", "NNPG", "QNT", "TOPRN")
    CHUNKTAG_MOD = ["MOD"]

    # chunk_tag_contain_check(CHUNKTAG_ALL, [CHUNKTAG_SENTENCE_END, CHUNKTAG_LIST_END, CHUNKTAG_LIST])

    RootHold = List[List[RPTItemSub]]
    root_hold: RootHold = [[], [], [], [], [], [], []]
    root_hold_adv = 0
    root_hold_obj = 1
    root_hold_sub = 2
    root_hold_mod_noun = 3
    root_hold_mod = 4
    root_hold_n_list = 5
    root_hold_v_list = 6
    root_err: List[RPTItemSub] = []
    root_crt: List[RPTItemSentence] = []

    def root_hold_func_last_item_index(root_hold: RootHold, max_limit=-1):
        max_key_index = -1
        max_index = -1
        if max_limit == -1:
            max_limit = 923
        for i, root_hold_item in enumerate(root_hold):
            if len(root_hold_item) > 0:
                target_rpt_item = root_hold_item[-1]
                if type(target_rpt_item) is RPTItem:
                    index = target_rpt_item.index
                    if max_limit > index > max_index:
                        max_index = index
                        max_key_index = i
                elif type(target_rpt_item) is RPTItemSentence:
                    index = target_rpt_item.vrb.index
                    if max_limit > index > max_index:
                        max_index = index
                        max_key_index = i
        return max_key_index

    def rpt_proc_list(root_hold: RootHold, rpt_item_root: RPTItemSub):
        root_hold_adv = 0
        root_hold_obj = 1
        root_hold_sub = 2
        root_hold_mod_noun = 3
        root_hold_n_list = 5
        root_hold_v_list = 6

        index_limit = -1
        if len(root_hold[root_hold_obj]) > 0:
            if root_hold[root_hold_obj][-1].index < rpt_item_root.index:
                index_limit = max(index_limit, root_hold[root_hold_obj][-1].index)
        if len(root_hold[root_hold_sub]) > 0:
            if root_hold[root_hold_sub][-1].index < rpt_item_root.index:
                index_limit = max(index_limit, root_hold[root_hold_sub][-1].index)
        for rpt_item_sub in reversed(root_hold[root_hold_mod_noun]):
            if type(rpt_item_sub) == RPTItem:
                if rpt_item_sub.index < rpt_item_root.index:
                    index_limit = max(index_limit, rpt_item_sub.index)
                    break

        if type(rpt_item_root) == RPTItem:
            limit_over = []
            limit_less = []
            for rpt_item in root_hold[root_hold_n_list]:
                if rpt_item.index < index_limit:
                    limit_less.append(rpt_item)
                elif rpt_item_root.index < rpt_item.index:
                    limit_less.append(rpt_item)
                else:
                    limit_over.append(rpt_item)
            root_hold[root_hold_n_list] = limit_less
            output = limit_over

        elif type(rpt_item_root) == RPTItemSentence:
            output = root_hold[root_hold_v_list]
            root_hold[root_hold_v_list] = []
        else:
            raise
        output.append(rpt_item_root)
        return output

    def rpt_proc_mod(root_hold: RootHold, rpt_item_root: RPTItem):
        root_hold_mod_noun = 3
        max_index = rpt_item_root.index
        len_mod = len(root_hold[root_hold_mod_noun])
        if len_mod > 0:
            for i in range(len_mod):
                i = len_mod - i - 1
                rpt_item_mod = root_hold[root_hold_mod_noun][i]
                if rpt_item_mod.index < max_index:
                    list_checked_item_list = rpt_proc_list(root_hold, rpt_item_mod)
                    rpt_item_root.mod_list = list_checked_item_list + rpt_item_root.mod_list
                    del root_hold[root_hold_mod_noun][i]
        return 0

    def rpt_make_unit_sentence(root_hold: RootHold, new_rpt_item: RPTItem) -> Tuple[RootHold, RPTItemSentence]:
        root_hold_adv = 0
        root_hold_obj = 1
        root_hold_sub = 2
        root_hold_mod_noun = 3
        root_hold_mod = 4
        root_hold_n_list = 5
        root_hold_v_list = 6

        new_rtm_sentence = RPTItemSentence(new_rpt_item)
        if len(root_hold[root_hold_sub]) > 0:
            new_item = root_hold[root_hold_sub].pop()
            list_checked_item_list = rpt_proc_list(root_hold, new_item)
            new_rtm_sentence.sub_list = list_checked_item_list

        if len(root_hold[root_hold_obj]) > 0:
            new_item = root_hold[root_hold_obj].pop()
            list_checked_item_list = rpt_proc_list(root_hold, new_item)
            new_rtm_sentence.obj_list = list_checked_item_list

        if len(root_hold[root_hold_adv]) > 0:
            new_list = root_hold[root_hold_adv]
            root_hold[root_hold_adv] = []
            new_rtm_sentence.adv_list = new_list

        return root_hold, new_rtm_sentence

    # Parse Tree 만들기
    for i, recas_item in enumerate(recas_sentence):
        recas_item = RecasItem(raw=recas_item)  # ([('제어반', 'NNPA')], [('제어반', 'NNPA')])
        chunk_tag = recas_item.chunk_item.tag
        # new_rpt_item: RPTItem = (rpt_deep_copy([recas_item]), i, [])
        new_rpt_item = RPTItem(recas_item, i)

        ##  Chunk 예외를 위한 코드
        # COND_KEY 를 위한 코드: COND_KEY가 있을 때 앞의 동사파생접미사와 합쳐 COND 구성
        if chunk_tag in ["COND_KEY"]:
            if len(root_hold[root_hold_mod_noun]) > 0:
                mod_noun_rpt_item = root_hold[root_hold_mod_noun].pop()
                if isinstance(mod_noun_rpt_item, RPTItemSentence):
                    if mod_noun_rpt_item.vrb.item.chunk_item.tag in ["VVEG"]:
                        mod_noun_rpt_item.merge_chunk(new_rpt_item, "VVEC")
                    elif mod_noun_rpt_item.vrb.item.chunk_item.tag in ["VVCG"]:
                        mod_noun_rpt_item.merge_chunk(new_rpt_item, "VVCC")
                    elif mod_noun_rpt_item.vrb.item.chunk_item.tag in ["VVTG"]:
                        mod_noun_rpt_item.merge_chunk(new_rpt_item, "VVTC")
                    else:
                        raise
                else:
                    # TODO: TOPRN + JKGA => NNPG와 COND_KEY가 연속 할 때의 처리 필요
                    raise
                new_rpt_item = mod_noun_rpt_item
                for rpt_item_v_list in root_hold[root_hold_v_list]:
                    root_crt.append(rpt_item_v_list)
                    root_hold[root_hold_v_list] = []
                root_crt.append(new_rpt_item)

        # TBF 를 위한 코드: TBF가 있을 때 앞의 동사파생접미사와 합쳐 COND 구성
        elif chunk_tag in ["TIMB", "TIMG", "TIMS", "TIMO", "TIML"] \
                and len(new_rpt_item.mod_list) > 0 and isinstance(new_rpt_item.mod_list[-1], RPTItemSentence):
                mod_noun_rpt_item = new_rpt_item.mod_list.pop()
                if mod_noun_rpt_item.vrb.item.chunk_item.tag in ["VVEG"]:
                    mod_noun_rpt_item.merge_chunk(new_rpt_item, "VVEC")
                elif mod_noun_rpt_item.vrb.item.chunk_item.tag in ["VVCG"]:
                    mod_noun_rpt_item.merge_chunk(new_rpt_item, "VVCC")
                elif mod_noun_rpt_item.vrb.item.chunk_item.tag in ["VVTG"]:
                    mod_noun_rpt_item.merge_chunk(new_rpt_item, "VVTC")
                else:
                    raise
                new_rpt_item = mod_noun_rpt_item
                for rpt_item_v_list in root_hold[root_hold_v_list]:
                    root_crt.append(rpt_item_v_list)
                    root_hold[root_hold_v_list] = []
                root_crt.append(new_rpt_item)

        ##  수식절이 Depth 를 넘지 않도록 하는 코드
        # if len(root_hold[root_hold_mod]) > 0 and depth(root_hold[root_hold_mod][-1]) >= 2:
        #     new_rpt_item_sentence = root_hold[root_hold_mod].pop()
        # if len(root_hold[root_hold_mod_noun]) > 0 and depth(root_hold[root_hold_mod_noun][-1]) >= 2:
        #     new_rpt_item_sentence = root_hold[root_hold_mod_noun].pop()


        ##  수식어에 대한 수식 처리 코드
        if len(root_hold[root_hold_mod]) > 0:
            mod_rpt_item = root_hold[root_hold_mod].pop()
            new_rpt_item.mod_list.append(mod_rpt_item)

        if chunk_tag in CHUNKTAG_NOUN:
            rpt_proc_mod(root_hold, new_rpt_item)

        ##  문장 구성 코드
        if chunk_tag in CHUNKTAG_SENTENCE_END:
            if recas_item.komop_sentence[0].tag in ["TBF3"]:
                while len(root_hold[root_hold_n_list]) > 0:
                    mod_rpt_item = root_hold[root_hold_n_list].pop()
                    new_rpt_item.mod_list.append(mod_rpt_item)
                if len(new_rpt_item.mod_list) == 0:
                    root_err.append(new_rpt_item)
                    continue
            elif recas_item.komop_sentence[0].tag in ["TBF2"]:
                if len(root_err) > 0 and root_err[-1].item.chunk_item.tag == "ERR":
                    mod_rpt_item = root_err.pop()
                    new_rpt_item.mod_list.append(mod_rpt_item)
                else:
                    root_err.append(new_rpt_item)
                    continue

            new_rpt_unit_sentence: RPTItemSentence
            (root_hold, new_rpt_unit_sentence) = rpt_make_unit_sentence(root_hold, new_rpt_item)
            if chunk_tag in CHUNKTAG_MOD_NOUN:
                root_hold[root_hold_mod_noun].append(new_rpt_unit_sentence)
            elif chunk_tag in CHUNKTAG_LIST:
                root_hold[root_hold_v_list].append(new_rpt_unit_sentence)
            else:
                for rpt_item_v_list in root_hold[root_hold_v_list]:
                    root_crt.append(rpt_item_v_list)
                    root_hold[root_hold_v_list] = []
                root_crt.append(new_rpt_unit_sentence)

        elif chunk_tag in CHUNKTAG_LIST_END:

            if chunk_tag == "SUB":
                root_hold[root_hold_sub].append(new_rpt_item)
            elif chunk_tag == "OBJ":
                root_hold[root_hold_obj].append(new_rpt_item)
            elif chunk_tag == "ADV" or chunk_tag == "TIMB":
                root_hold[root_hold_adv].append(new_rpt_item)
            elif chunk_tag in CHUNKTAG_MOD_NOUN:
                root_hold[root_hold_mod_noun].append(new_rpt_item)
            elif chunk_tag in CHUNKTAG_MOD:
                root_hold[root_hold_mod].append(new_rpt_item)
            else:
                raise Exception()

        elif chunk_tag in CHUNKTAG_LIST:
            root_hold[root_hold_n_list].append(new_rpt_item)
        elif chunk_tag == "ERR":
            root_err.append(new_rpt_item)
        # 임시 처리, 수정 필요
        elif chunk_tag in ["QNT"]:
            root_hold[root_hold_mod].append(new_rpt_item)
        else:
            root_err.append(new_rpt_item)
            # raise

    for root_hold_item in root_hold:
        for rpt_sub_item in root_hold_item:
            root_err.append(rpt_sub_item)

    # 주 문장의 주어가 없고 해당 문장 하위 문장에 주어가 있을 경우, 해당 주어를 가져온다. -> 상위 문장에 주어가 없을 때로 작용해도 괜찮을까요?
    def traverse_rpt_item_no_sub(rpt_item: RPTItem) -> List[List[RPTItem]]:
        searched_sub_ = []
        if len(rpt_item.mod_list) > 0:
            searched_sub_ += traverse_rpt_item_sub_no_sub(rpt_item.mod_list)
        return searched_sub_

    def traverse_rpt_item_sentence_no_sub(rpt_item_sentence: RPTItemSentence) -> List[List[RPTItem]]:
        searched_sub_ = []
        if len(rpt_item_sentence.sub_list) > 0:
            searched_sub_.append(rpt_item_sentence.sub_list)
        searched_sub_ += traverse_rpt_item_sub_no_sub(rpt_item_sentence.sub_list)
        searched_sub_ += traverse_rpt_item_sub_no_sub(rpt_item_sentence.obj_list)
        searched_sub_ += traverse_rpt_item_sub_no_sub(rpt_item_sentence.adv_list)
        return searched_sub_

    def traverse_rpt_item_sub_no_sub(rpt_item_sub_list: List[RPTItemSub]) -> List[List[RPTItem]]:
        searched_sub_ = []
        for rpt_item_sub in rpt_item_sub_list:
            if type(rpt_item_sub) == RPTItemSentence:
                searched_sub_ += traverse_rpt_item_sentence_no_sub(rpt_item_sub)
            elif type(rpt_item_sub) == RPTItem:
                searched_sub_ += traverse_rpt_item_no_sub(rpt_item_sub)
            else:
                raise
        return searched_sub_

    for root_sentence in root_crt:
        if len(root_sentence.sub_list) == 0:
            searched_sub_list: List[List[RPTItem]] = traverse_rpt_item_sentence_no_sub(root_sentence)
            min_index = None
            min_searched_sub = None
            for searched_sub in searched_sub_list:
                if len(searched_sub) > 0:
                    new_index = searched_sub[-1].index
                    if min_index is None or min_index > new_index:
                        min_index = new_index
                        min_searched_sub = searched_sub
                else:
                    raise
            if min_searched_sub is not None:
                while len(min_searched_sub) > 0:
                    root_sentence.sub_list.append(min_searched_sub[0])
                    del min_searched_sub[0]

    return root_err, root_crt


