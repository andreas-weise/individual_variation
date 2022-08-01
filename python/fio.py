import csv
import os
import shutil
import subprocess

import aux
import cfg
import db



################################################################################
#                                  READ FILES                                  #
################################################################################

def readlines(path, fname):
    ''' yields all lines in given file '''
    with open(path + fname) as file:
        for line in file.readlines():
            yield(line)


def read_csv(path, fname, delimiter=",", quotechar='"', skip_header=False):
    ''' yields all rows in given file, interpreted as csv '''
    with open(path + fname, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=delimiter, quotechar=quotechar)
        if skip_header:
            next(reader)
        for row in reader:
            yield(row)



################################################################################
#                                     OTHER                                    #
################################################################################

def extract_features(
        in_path, in_fname, ses_id, chu_id, words, start, end, do_cut=True):
    ''' runs feature extraction for given chunk section, returns features '''
    # determine tmp filenames
    cut_fname = '%d_%d.wav' % (ses_id, chu_id)
    out_fname = '%d_%d.txt' % (ses_id, chu_id)
    if do_cut:
        # extract relevant audio with praat, removing pauses (fisher corpus 
        # contains pauses longer than 50ms within transcription segments)
        subprocess.check_call(['praat', '--run',
                                cfg.PRAAT_PATH + cfg.PRAAT_CUT_FNAME,
                                in_path + in_fname, 
                                cfg.TMP_PATH + cut_fname,
                                cfg.TMP_PATH + out_fname, 
                                str(start), str(end)])
    else:
        # chunks are already in separate wav files, simply use the whole file
        shutil.copy(in_path + in_fname, cfg.TMP_PATH + cut_fname)
    # extract features
    subprocess.check_call(['praat', '--run', 
                           cfg.PRAAT_PATH + cfg.PRAAT_EXTRACT_FNAME,
                           cfg.TMP_PATH + cut_fname, 
                           cfg.TMP_PATH + out_fname])
    # read output
    features = {}
    for line in readlines(cfg.TMP_PATH, out_fname):
        key, val = line.replace('\n', '').split(',')
        try:
            val = float(val)
        except:
            val = None
        features[key] = val
    if not do_cut:
        # cutting script writes start and end to output; if it's not run, these
        # keys need to be set manually
        features['start_point'] = start
        features['end_point'] = end
    features['rate_syl'] = aux.count_syllables(words) / features['dur']
    # clean up
    os.remove(cfg.TMP_PATH + cut_fname)
    os.remove(cfg.TMP_PATH + out_fname)
    
    return features




