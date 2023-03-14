from recas.Chunk import making_data
import numpy as np
import tensorflow as tf


def one_sentence_to_word_index(sentence_komop, komop_pos_dic):
    """
    Converts a single Korean sentence into a list of word indices based on their POS tags.

    Args:
    sentence_komop (list): A list of tuples, where each tuple contains a Korean word and its corresponding POS tag.
    komop_pos_dic (dict): A dictionary that maps each POS tag to a unique integer value.

    Returns:
    tuple: A tuple containing the final sentence as a list of word indices, and the original sentence as a list of words.
    """
    try:
        komoran_pos = list(zip(*sentence_komop))[0]                                  # train: 코모란 문장
    except Exception as e:
        print(sentence_komop)
        raise
    sen = [list(list(zip(*i))[0]) for i in komoran_pos]                   # list   #train: 코모란 문장의 단어
    test_datalist = [list(list(zip(*i))[1]) for i in komoran_pos]         # list   #train: 코모란 문장의 품사

    final_sentence = making_data.komoran_encoding(test_datalist, komop_pos_dic)

    return final_sentence, sen


def sentence_to_word_index(sentences_komop, komop_pos_dic):
    """
    Converts multiple Korean sentences into lists of word indices based on their POS tags.

    Args:
    sentences_komop (list): A list of lists, where each inner list contains tuples that represent a Korean sentence.
    komop_pos_dic (dict): A dictionary that maps each POS tag to a unique integer value.

    Returns:
    tuple: A tuple containing the list of final sentences, each represented as a list of word indices, and the original sentences as lists of words.
    """
    test_sentences = []
    sen = []
    for sentence_komop in sentences_komop:
        test_sentence, one_sen = one_sentence_to_word_index(sentence_komop, komop_pos_dic)
        test_sentences.append(test_sentence)
        sen.append(one_sen)

    return test_sentences, sen


def merge(test_sentences, start, end):
    """
    Merges a list of lists into a single list and pads the result to a fixed length.

    Args:
    test_sentences (list): A list of lists, where each inner list represents a sentence as a list of word indices.
    start (int): The starting index for the slice of the test_sentences list to be merged.
    end (int): The ending index for the slice of the test_sentences list to be merged.

    Returns:
    numpy.ndarray: A 2D array where each row represents a sentence as a list of word indices padded to a fixed length.
    """
    merged = [item for sublist in test_sentences[start:end] for item in sublist]
    merged = np.array([merged])
    merged_sentences = tf.keras.preprocessing.sequence.pad_sequences(merged, maxlen=30, padding='post')
    return merged_sentences


def index(predict, num_to_word_dic):
    """
    Converts a predicted index into a corresponding word.

    Args:
    predict (numpy.ndarray): A 1D array that contains the predicted word index.
    num_to_word_dic (dict): A dictionary that maps each word index to a corresponding Korean word.

    Returns:
    str: The predicted Korean word.
    """
    index_ = np.argmax(predict)
    predict_index = num_to_word_dic[index_]
    return predict_index


def change(predict_sen, sen, num_to_word_dic, model):
    """
    Converts a list of predicted word indices into their corresponding Korean words.

    Args:
    predict_sen (numpy.ndarray): A 2D array where each row represents a sentence as a list of word indices.
    sen (list): A list of lists, where each inner list represents a sentence as a list of words.
    num_to_word_dic (dict): A dictionary that maps each word index to a corresponding Korean word.
    model: A TensorFlow machine learning model used for prediction.

    Returns:
    list: A list of tuples, where each tuple contains the original Korean sentence as a string and the predicted Korean word as a string.
    """
    start = 0
    end = start + 1
    output = []
    res_pos = ''
    while True:
        if end > len(predict_sen):
            if res_pos == 'ERR':
                output.append(["", sen[start:end], "예측값:", res_pos])
            break
        res = model.predict(merge(predict_sen, start, end))
        res_pos = index(res, num_to_word_dic)
        if res_pos != 'ERR':  # success
            output.append(["", sen[start:end], "예측값:", res_pos])
            start = end
            end = start + 1
        else:                 # fail
            tmp = start + 1
            while True:
                if (tmp == end) or (end > len(predict_sen)):
                    end = end + 1
                    break
                res = model.predict(merge(predict_sen, tmp, end))  # tmp2
                res_pos = index(res, num_to_word_dic)
                if res_pos != 'ERR':  # success
                    output.append(["Error", sen[start:tmp]])
                    output.append(["Found", sen[tmp:end], "예측값:", res_pos])
                    start = end
                    end = start + 1
                    break
                else:                 # fail
                    tmp = tmp+1
    return output


def change_modified(predict_sen, sen, num_to_word_dic, model):
    """
    Converts a list of predicted word indices into their corresponding Korean words.

    Args:
    predict_sen (numpy.ndarray): A 2D array where each row represents a sentence as a list of word indices.
    sen (list): A list of lists, where each inner list represents a sentence as a list of words.
    num_to_word_dic (dict): A dictionary that maps each word index to a corresponding Korean word.
    model: A TensorFlow machine learning model used for prediction.

    Returns:
    list: A list of tuples, where each tuple contains the original Korean sentence as a string and the predicted Korean word as a string.
    """
    start = 0
    end = start + 1
    log = []
    res_pos = ''
    while True:
        if end > len(predict_sen):
            if res_pos == 'ERR':
                log.append(["", sen[start:end], "예측값:", res_pos])
            break
        res = model.predict(merge(predict_sen, start, end))
        res_pos = index(res, num_to_word_dic)
        if res_pos != 'ERR':    # success
            # print(predict_sen[start:end],sen[start:end],res_pos)
            log.append(["", sen[start:end], "예측값:", res_pos])
            start = end
            end = start + 1
        else:                 # fail
            tmp = start + 1
            while True:
                if (tmp == end) or (end > len(predict_sen)):
                    end = end + 1
                    break
                res = model.predict(merge(predict_sen, tmp, end))         # tmp2
                res_pos = index(res, num_to_word_dic)
                if res_pos != 'ERR':                                    # success
                    # print("Error:", predict_sen[start:tmp],sen[start:tmp])
                    log.append(["", sen[start:tmp], "예측값:", "ERR"])
                    # print("Found:", predict_sen[tmp:end],sen[tmp:end],res_pos)
                    log.append(["", sen[tmp:end], "예측값:", res_pos])
                    start = end
                    end = start + 1
                    break
                else:                 # fail
                    tmp = tmp+1

    output = []
    for item in log:
        if len(item) != 4:
            raise
        if item[2] != "예측값:":
            raise
        merge_str = ""
        for item_ in item[1]:
            merge_str += " "
            merge_str += "".join(item_)
        merge_str = merge_str[1:]
        output.append((merge_str, item[3]))

    return output


def change_modified2(predict_sen, sen, num_to_word_dic, model):
    """Predicts the parts of speech of words in a sentence using a trained model and dictionary.

    Args:
    predict_sen (list): A list of integers representing the words in the sentence as numbers.
    sen (list): A list of lists, each containing a character of a word in the sentence.
    num_to_word_dic (dict): A dictionary mapping numbers to words.
    model (object): A trained model for predicting parts of speech.

    Returns:
    list: A list of tuples, each containing a string representing a word in the sentence and its predicted part of speech.
    """
    start = 0
    end = start + 3
    log = []
    res_pos = ''
    while True:
        if start == end:
            if res_pos == 'ERR':
                log.append(["", sen[start:end], "예측값:", res_pos])
            break
        res = model.predict(merge(predict_sen, start, end))
        res_pos = index(res, num_to_word_dic)
        if res_pos != 'ERR':    # success
            # print(predict_sen[start:end],sen[start:end],res_pos)
            log.append(["", sen[start:end], "예측값:", res_pos])
            start = end
            end = min(start + 3, len(predict_sen))
        else:                 # fail
            while True:
                if end == start:
                    break
                res = model.predict(merge(predict_sen, start, end))         # tmp2
                res_pos = index(res, num_to_word_dic)
                if res_pos != 'ERR':                                    # success
                    # print("Error:", predict_sen[start:tmp],sen[start:tmp])
                    log.append(["", sen[start:end], "예측값:", "ERR"])
                    start = end
                    end = min(start + 3, len(predict_sen))
                    break
                else:                 # fail
                    end -= 1

    output = []
    for item in log:
        if len(item) != 4:
            raise
        if item[2] != "예측값:":
            raise
        merge_str = ""
        for item_ in item[1]:
            merge_str += " "
            merge_str += "".join(item_)
        merge_str = merge_str[1:]
        output.append((merge_str, item[3]))

    return output
