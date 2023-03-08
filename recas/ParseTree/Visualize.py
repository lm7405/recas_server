import graphviz
from .Structure import *
import os

os.environ["DOT_BINARY"] = os.path.abspath("recas\\ParseTree\\Graphviz\\bin_win\\dot.exe")

# -----------------------------------------------------------------------------------------------------------------------
# 1. parse tree 에 대하여 다음의 작업을 수행한다.
#    1) 각 노드에 unique ID(seq 번호)를 부여한다
#    2) for node in parse tree:
#        - parse tree node는 graph.edges에 출력(node type 에 따라 shape를 문장=>record,구성요소=>rectangle, 조사=>egg로 설정)
#        - parse tree link는 (수식하는 node ID, 수식받는 node ID) 형태로 ptrlist (list 구조)에 append
#    3) ptrlist를 graph.edges에 출력
# 2. parsetree node의 구조
#    "type" : 노드의 종류, 1000: 문장노드, 기타: 형태소 타입
#             문장인 경우, 3개, SUb, OBJ, ADV 에 children이 달림
#    "mod"  : 수식하는 문장 구성 요소
#    "comp"  : [터큰 값, 형태소 종류]
# 3. parsetree로부터 목사되는 tree
#    node["id"]    :  노드 Unique Id (seq no로 충분함)
#    node["type"]  :  sentence(문장), particle(명사, 관형어, 부사 등), ending(조사), fromto(pointer)
#    node["value"] :  token 값
#                     문장구성요소인 경우, token 의 값임
#                     "fromto"(link)인 경우 tuple (parent node id, child node id)
#    node["child"] : pointing child
# 4. 참고
#    gr.node('8', '운전자', shape='rectangle')
#    gr.edges([('2', '1'), ('3', '2'), ('4','3')])
# -----------------------------------------------------------------------------------------------------------------------






def __replace_reserved_letter(str):
    str = str.replace('|', r'\|')
    str = str.replace('<', r'\<')
    str = str.replace('>', r'\>')
    str = str.replace('[', r'\[')
    str = str.replace(']', r'\]')
    return str


def __make_tokenlist_node(tokenList, option):
    contents = ""
    for i, token in enumerate(tokenList):
        contents += "|{"
        node_string = __replace_reserved_letter(token[0])

        contents += node_string + "|" + token[1]
        if "show_pos_at_tokenList" in option:
            contents += "|" + str(i)
        contents += "}"
    contents = contents[1:]
    return contents


def __new_graphviz_node(args):
    DEFAULT_SETTING = {
        "tokenShape": 'rectangle',
        "statementShape": 'record',
        "endingShape": 'egg',
        "rankdir": 'BT',
        "fontname": "Gulim",
        "fontsize": '10',
        "height": '0.05',
        "arrowsize": '0.3',
        "tagStatementNode": 1000,
        "name": 'default_name',
        "filename": 'default_filename',
        "fileformat": 'jpg',
        "typeSentence": "sentence",
        "typeParticle": "particle",
        "typeEnding": "ending",
    }

    name = DEFAULT_SETTING["name"]
    if "file_name" in args:
        filename = args["file_name"]
    else:
        filename = DEFAULT_SETTING["filename"]
    fileformat = DEFAULT_SETTING["fileformat"]

    gr = graphviz.Digraph(name, filename=filename, format=fileformat)

    gr.graph_attr['rankdir'] = DEFAULT_SETTING["rankdir"]
    gr.node_attr['fontname'] = DEFAULT_SETTING["fontname"]
    gr.node_attr['fontsize'] = DEFAULT_SETTING["fontsize"]
    gr.node_attr['height'] = DEFAULT_SETTING["height"]
    gr.edge_attr['arrowsize'] = DEFAULT_SETTING["arrowsize"]

    return gr, DEFAULT_SETTING["statementShape"]


def __visualize_traverse_RPTItem(gr, error_pos_list, rpt_item: RPTItem, func_id: str, parent, cluster):
    node_shape = 'rectangle'
    # node_string = __replace_reserved_letter(rpt_item.item_list[0])
    node_string = __replace_reserved_letter(rpt_item.item.chunk_item.text)
    node_style = None
    color = "black"
    if rpt_item.index == -1:
        node_style = "dotted"
    elif rpt_item.index in error_pos_list:
        node_style = "bold"

    if cluster is None:
        gr.node(func_id, node_string, shape=node_shape, style=node_style, color=color)
        gr.edge(func_id, parent)
    else:
        cluster.node(func_id, node_string, shape=node_shape, style=node_style, color=color)

    if len(rpt_item.mod_list) > 0:
        new_func_id = func_id + '0'
        __visualize_traverse_RPTItemSubs(gr, error_pos_list, rpt_item.mod_list, new_func_id, func_id, None)


def __visualize_traverse_RPTItemSentence(gr, error_pos_list, rpt_item_sentence: RPTItemSentence, func_id: str, parent, cluster):
    contents = ''
    for key in ["SUB", "OBJ", "ADV", "VER"]:
        contents += '|' + '<' + key + '>' + key
        sub_parent = func_id + ':' + key
        new_func_id = func_id + key[0]
        if key == "SUB" and len(rpt_item_sentence.sub_list) != 0:
            __visualize_traverse_RPTItemSubs(gr, error_pos_list, rpt_item_sentence.sub_list, new_func_id, sub_parent, None)
        elif key == "OBJ" and len(rpt_item_sentence.obj_list) != 0:
            __visualize_traverse_RPTItemSubs(gr, error_pos_list, rpt_item_sentence.obj_list, new_func_id, sub_parent, None)
        elif key == "ADV" and len(rpt_item_sentence.adv_list) != 0:
            __visualize_traverse_RPTItemSubs(gr, error_pos_list, rpt_item_sentence.adv_list, new_func_id, sub_parent, None)
        elif key == "VER":
            __visualize_traverse_RPTItem(gr, error_pos_list, rpt_item_sentence.vrb, new_func_id, sub_parent, None)
    contents = contents[1:]

    if cluster is None:
        gr.node(func_id, contents, shape='record',)
        gr.edge(func_id, parent)
    else:
        cluster.node(func_id, contents, shape='record',)


def __visualize_traverse_RPTItemSubs(gr, error_pos_list, rpt_item_subs: List[RPTItemSub], func_id: str, parent, cluster):
    i = 0

    if len(rpt_item_subs) <= 1:
            for i, rpt_item_sub in enumerate(rpt_item_subs):
                new_func_id = func_id + '_' + str(i)
                if type(rpt_item_sub) is RPTItem:
                    __visualize_traverse_RPTItem(gr, error_pos_list, rpt_item_sub, new_func_id, parent, None)
                elif type(rpt_item_sub) is RPTItemSentence:
                    __visualize_traverse_RPTItemSentence(gr, error_pos_list, rpt_item_sub, new_func_id, parent, None)
                else:
                    raise
    else:
        with gr.subgraph(name='cluster_' + func_id) as cluster:
            if type(rpt_item_subs[0]) == RPTItem:
                rpt_item_subs = reversed(rpt_item_subs)
            for i, rpt_item_sub in enumerate(rpt_item_subs):
                new_func_id = func_id + '_' + str(i)
                if type(rpt_item_sub) is RPTItem:
                    __visualize_traverse_RPTItem(gr, error_pos_list, rpt_item_sub, new_func_id, func_id, cluster)
                elif type(rpt_item_sub) is RPTItemSentence:
                    __visualize_traverse_RPTItemSentence(gr, error_pos_list, rpt_item_sub, new_func_id, func_id, cluster)
                else:
                    raise
        i = int(i / 2)
        gr.edge(func_id + '_' + str(i), parent)


def get_gr_nodes(item: Union[RPTItemSub, List[RPTItemSub]], args):
    (gr, statementShape) = __new_graphviz_node(args)

    start_node_name = "n"
    gr.node(start_node_name, "root", shape=statementShape)

    if "recas_sentence" in args:
        text = ""
        dummy = args["recas_sentence"]
        while len(dummy) > 50:
            text += dummy[:50]
            dummy = dummy[50:]
            text += "\n"
        text += dummy

        gr.node("recas_sentence", "recas_sentence: " + text, shape="rectangle")
        gr.edge("error_code", "recas_sentence", color="white")

    if "error_list" in args:
        gr.node("error_code", "error_code: " + str(args["error_list"]), shape="rectangle")
        gr.edge(start_node_name, "error_code", color="white")
        error_pos_list = []
        for error_item in args["error_list"]:
            error_pos_list += error_item[1]
    else:
        error_pos_list = []

    if "rpt_error" in args and args["rpt_error"] is not None:
        item_e = args["rpt_error"]
        func_id = "e"
        item_type = type(item_e)
        if item_type is RPTItem:
            __visualize_traverse_RPTItem(gr, error_pos_list, item_e, func_id, start_node_name, None)
        elif item_type is RPTItemSentence:
            __visualize_traverse_RPTItemSentence(gr, error_pos_list, item_e, func_id, start_node_name, None)
        elif type(item_e) is type([]):
            __visualize_traverse_RPTItemSubs(gr, error_pos_list, item_e, func_id, start_node_name, None)
        else:
            raise

    func_id = "n"
    item_type = type(item)
    if item_type is RPTItem:
        __visualize_traverse_RPTItem(gr, error_pos_list, item, func_id, start_node_name, None)
    elif item_type is RPTItemSentence:
        __visualize_traverse_RPTItemSentence(gr, error_pos_list, item, func_id, start_node_name, None)
    elif type(item) is type([]):
        __visualize_traverse_RPTItemSubs(gr, error_pos_list, item, func_id, start_node_name, None)
    else:
        raise

    # gr.view()
    gr.render(view=False)
    return


def visualize(item: Union[RPTItemSub, List[RPTItemSub]],
              rpt_error: Union[RPTItemSub, List[RPTItemSub], None],
              recas_sentence: str, error_list, file_name: str):
    args = {
        "file_name": file_name,
        "recas_sentence": recas_sentence,
        "rpt_error": rpt_error,
        "error_list": error_list
    }

    get_gr_nodes(item, args)

    return None
