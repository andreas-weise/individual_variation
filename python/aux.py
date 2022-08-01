import hyphenate
import math
import nltk
import numpy as np
import pandas as pd
import scipy

import cfg

cmu_dict = nltk.corpus.cmudict.dict()



def preprocess_transcript(transcript):
    ''' prepocessing of transcripts of individual utterances '''
    words = transcript.lower()
    # remove markup for uncertain transcriptions
    words = words.replace('((', '')
    words = words.replace('))', '')
    # remove markup for noise, laughter etc.
    while words.find('[') != -1:
        if words.find(']') != -1:
            words = words[0:words.find('[')] + words[words.find(']')+1:]
        else:
            words = words[0:words.find('[')]
    # remove markup for spelled out abbreviations
    words = words.replace('._', ' ')
    words = words.replace('.', ' ')
    # remove additional markups
    words = words.replace("$", '')
    words = words.replace("#", '')
    # separate around hyphens and remove superfluous spaces
    words = ' '.join(' '.join(words.split('-')).split())
    return words


def count_syllables(in_str):
    ''' counts the number of syllables in a given string '''
    syll_count = 0
    for word in in_str.split(' '):
        ### PREPROCESSING
        # remove whitespace and convert to lowercase for dictionary lookup
        word = word.strip().lower()
        # '-' marks incomplete words; remove it
        if len(word) > 0 and word[-1] == '-':
            word = word[:-1]
        # remove trailing "'s" if word with it is not in dictionary
        # (does not change syllable count) 
        if len(word) > 1 and word[-2:] == "'s" and word not in cmu_dict:
            word = word[:-2]

        ### SPECIAL CASES
        # there are no syllables in an empty string
        if len(word) == 0:
            syll_count += 0
        ### STANDARD METHOD (dictionary lookup; fallback: automatic hyphenation)
        elif word in cmu_dict:
            # word is in the dictionary, extract number of vowels in primary
            # pronunciation as syllable count; vowels are recognizable by their 
            # stress markers (final digit), for example:
            #     cmu_dict["natural"][0] = ['N', 'AE1', 'CH', 'ER0', 'AH0', 'L']
            syll_count += sum([1 for p in cmu_dict[word][0] if p[-1].isdigit()])
        else:
            # fall back to the hyphenate library for a best guess (imperfect)
            syll_count += len(hyphenate.hyphenate_word(word))
    return syll_count


def get_df(data, index_names):
    ''' creates pandas dataframe from given data with given index names '''
    df = pd.DataFrame(data)
    df.index.set_names(index_names, inplace=True)
    return df


def ttest_ind(a, b):
    ''' scipy.stats.ttest_ind(a, b) with degrees of freedom also returned '''
    return scipy.stats.ttest_ind(a, b) + (len(a) + len(b) - 2,)


def ttest_rel(a, b):
    ''' scipy.stats.ttest_rel(a, b) with degrees of freedom also returned '''
    return scipy.stats.ttest_rel(a, b) + (len(a) - 1,)


def pearsonr(x, y):
    ''' scipy.stats.pearsonr(x, y) with degrees of freedom also returned '''
    return scipy.stats.pearsonr(x, y) + (len(x) - 2,)


def r2z(r):
    ''' fisher z-transformation of a pearson correlation coefficient '''
    return 0.5 * (math.log(1 + r) - math.log(1 - r))


def cohen_d(x, y):
    ''' cohen's d, only for len(x) == len(y) '''
    assert len(x) == len(y), 'x and y need to have the same length'
    std_x = np.std(x, ddof=1)
    std_y = np.std(y, ddof=1)
    return (np.mean(x) - np.mean(y)) / np.sqrt((std_x ** 2 + std_y ** 2) / 2.0)



           


































