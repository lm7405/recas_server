import tensorflow as tf


def convert_model_input(data_list, komop_tokenizer):
    """
    Converts input data into a format suitable for a machine learning model.

    Args:
        data_list (list): A list of input data.
        komop_tokenizer (object): A tokenizer object for Komoran POS tagging.

    Returns:
        tuple: A tuple containing three items:
            - A list of lists of Komoran POS tags.
            - A list of target POS tags.
            - A list of lists of target POS tags.
    """
    output = komop_tokenizer.get_training_data(data_list)

    # data 만들기
    komoran_pos = list(zip(*output))[0]
    rule_pos = list(zip(*output))[1]

    komoran_list = [list(list(zip(*i))[1]) for i in komoran_pos]
    rule_list = list(list(zip(*rule_pos))[1])
    rule_list_list = []
    for i in rule_list:
        i = i.split()
        rule_list_list.append(i)

    return komoran_list, rule_list, rule_list_list


def dictionary(komop_dic, chunk_dic):
    """
    Encodes dictionaries of POS tags into numeric form for use in a machine learning model.

    Args:
        komop_dic (str): A file path for the Komoran POS tag dictionary.
        chunk_dic (str): A file path for the target POS tag dictionary.

    Returns:
        tuple: A tuple containing five items:
            - A dictionary mapping Komoran POS tags to numeric values.
            - A dictionary mapping numeric values to Komoran POS tags.
            - A dictionary mapping target POS tags to numeric values.
            - A dictionary mapping numeric values to target POS tags.
            - The length of the Komoran POS tag dictionary.
    """
    # data_dic 인코딩
    with open(komop_dic) as f:
        komop_lines = f.readlines()

    komop_lines = [line.rstrip('\n') for line in komop_lines]

    komop_pos_dic = {pos: idx + 1 for idx, pos in enumerate(komop_lines)}
    num_to_word_dic = {komop_pos_dic.get(key): key for key in komop_pos_dic}

    # target_dic 인코딩
    with open(chunk_dic) as f:
        chunk_lines = f.readlines()

    chunk_lines = [line.rstrip('\n') for line in chunk_lines]

    chunk_pos_dic = {pos: idx + 1 for idx, pos in enumerate(chunk_lines)}
    chunk_num_to_word_dic = {chunk_pos_dic.get(key): key for key in chunk_pos_dic}

    word_index_len = len(komop_pos_dic)

    return komop_pos_dic, num_to_word_dic, chunk_pos_dic, chunk_num_to_word_dic, word_index_len


def komoran_encoding(komoran_list, komop_pos_dic):
    """
    Encodes Komoran POS tags into numeric form for use in a machine learning model.

    Args:
        komoran_list (list): A list of lists of Komoran POS tags.
        komop_pos_dic (dict): A dictionary mapping Komoran POS tags to numeric values.

    Returns:
        list: A list of lists of numeric values representing the input Komoran POS tags.
    """
    komoran_sentences = []
    for sentence in komoran_list:
        komoran_sentence = []
        for value in sentence:
            try:
                # 단어 집합에 있는 단어라면 해당 단어의 정수를 리턴.
                komoran_sentence.append(komop_pos_dic[value])
            except KeyError:
                # 만약 단어 집합에 없는 단어라면 raise
                print(value)
                raise
        komoran_sentences.append(komoran_sentence)
    return komoran_sentences


def chunk_encoding(rule_list_list, chunk_pos_dic):
    """
    Encodes chunk POS tags into numeric form for use in a machine learning model.

    Args:
    rule_list_list (list): A list of lists of chunk rule POS tags.
    chunk_pos_dic (dict): A dictionary mapping Komoran POS tags to numeric values.

    Returns:
    list: A list of lists of numeric values representing the input Komoran POS tags.
    """
    chunk_sentences = []
    for sentence in rule_list_list:
        chunk_sentence = []
        for value in sentence:
            try:
                # 단어 집합에 있는 단어라면 해당 단어의 정수를 리턴.
                chunk_sentence.append(chunk_pos_dic[value])
            except KeyError:
                # 만약 단어 집합에 없는 단어라면 raise
                print(value)
                raise
        chunk_sentences.append(chunk_sentence)
    return chunk_sentences


def padding(komoran_sentences, chunk_sentences):
    """
    Pads Komoran and chunk sentences to a fixed length.

    Args:
    komoran_sentences (list): A list of lists of numeric values representing the input Komoran POS tags.
    chunk_sentences (list): A list of lists of numeric values representing the input chunk POS tags.

    Returns:
    tuple: A tuple containing two items:
    - A padded list of lists of numeric values representing the input Komoran POS tags.
    - A padded list of lists of one-hot-encoded numeric values representing the input chunk POS tags.
    """
    komoran_sentences = tf.keras.preprocessing.sequence.pad_sequences(komoran_sentences, maxlen=30, padding='post')
    rule_sentences = tf.keras.utils.to_categorical(chunk_sentences)

    print("komoran_sentences: ", komoran_sentences.shape)
    print("rule_sentences: ", rule_sentences.shape)

    return komoran_sentences, rule_sentences



