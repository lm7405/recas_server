## ---------------------------------------- ... ---
# 1. 버전
#  1) 버전 코드		: 1.0.0
#  2) 최종 수정 날짜	: 210929
#  3) 최종 수정자	    : 아주대학교
#
# 2. 코드 목적
#  - recas 토큰과 원본 문장을 비고하여 recas 토큰의 위치를 복원
#
# 3. 공개 함수 설명
#  - get_pos_from_seq
#   원본 문장 문자열과 recas 토큰을 입력으로 받아, (token, start, end) 형태의 위치정보가 추가된 리스트를 반환한다.
#
# 4. 외부 라이브러리 의존성
#  - jamo == 0.4.1
#  -
# ---------------------------------------- ... ---

from jamo import h2j, j2hcj


def get_pos_from_seq(sentence, tokens):
    """
    원본 문장의 문자열과 토큰의 문자열을 비고하여 토큰의 위치를 반환하는 함수

    Args:
        sentence: 원본 문장
        tokens: 원본 문장에 토크나이저를 적용한 토큰 리스트

    Returns:
        (토큰, 시작위치, 끝위치)로 구성된 리스ㅡ
    """
    sentence_jamo = j2hcj(h2j(sentence))
    sentence_jamo_pos = []
    for pos, letter in enumerate(sentence):
        letter_jamo = j2hcj(h2j(letter))
        for jamo in letter_jamo:
            sentence_jamo_pos.append(pos)

    sentence_jamo_from_tokens = []
    for token in tokens:
        word_jamo = j2hcj(h2j(token[0]))
        for jamo in word_jamo:
            sentence_jamo_from_tokens.append(jamo)
    left_jamo_tkn = sentence_jamo_from_tokens[:]
    left_jamo_ori = []
    for jamo in sentence_jamo:
        if jamo != ' ':
            if jamo in left_jamo_tkn:
                left_jamo_tkn.remove(jamo)
            else:
                left_jamo_ori.append(jamo)

    i = 0
    result = []
    for token in tokens:
        if i > len(sentence_jamo):
            break

        start = -1
        end = -1
        word_jamo = j2hcj(h2j(token[0]))
        j = 0
        while j < len(word_jamo) and i < len(sentence_jamo):
            while sentence_jamo[i] in [" "]:
                i += 1
            while word_jamo[j] in [" "]:
                j += 1

            jamo_ori = sentence_jamo[i]
            jamo_tkn = word_jamo[j]

            if jamo_tkn == jamo_ori:
                if start == -1:
                    start = sentence_jamo_pos[i]
                end = sentence_jamo_pos[i]
                i += 1
                j += 1
            elif jamo_tkn in left_jamo_tkn:
                j += 1
                left_jamo_tkn.remove(jamo_tkn)
            elif jamo_ori in left_jamo_ori:
                i += 1
                left_jamo_ori.remove(jamo_ori)
            else:
                break
        if word_jamo == "":
            result.append((token, result[-1][1], result[-1][2]))
        else:
            result.append((token, start, end))

    return result
