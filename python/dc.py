import sqlite3

import aux
import cfg
import db
import fio

# functions for the population of deception corpus tables
# note: chunks are listed in csv files per role and their audio contained in 
#       individual files per chunk, with start/end timestamps in name



def _load_chunks(ses_dict, role):
    ''' reads chunk meta-data, returns dict per task with dict of chunks '''
    tsk_chu_dict = {}
    fname = 'chunks_%s.csv' % role.lower()
    for row in fio.read_csv(cfg.META_PATH_DC, fname, skip_header=True):
        ses = '%s_%s' % (row[0][1:4], row[0][5:8])
        if ses in ses_dict:
            # sessions are indexed by spk_id pair in csv file, convert to ses_id
            ses_id = ses_dict[ses][0]
            # each session contains two parts, interviews in either direction
            part = row[0][13]
            tsk_id = 2 * ses_id - (1 if part == '1' else 0)
            if tsk_id not in tsk_chu_dict:
                tsk_chu_dict[tsk_id] = {}
            start = float(row[1])
            end = float(row[2])
            transcript = row[3]
            words = aux.preprocess_transcript(row[3])
            tsk_chu_dict[tsk_id]['%f:%f' % (start, end)] = \
                (start, end, transcript, words)
    return tsk_chu_dict


def _merge_chunks(tsk_chu_dict_ee, tsk_chu_dict_er):
    ''' merges chunks from both speakers in each task by start timestamps '''
    tsk_chu_dict = {}
    for key, val in tsk_chu_dict_ee.items():
        inf = float('inf')
        tsk_chus_ee = [v for k, v in val.items()] + [(inf,)]
        tsk_chus_ee.sort()
        tsk_chus_er = [v for k, v in tsk_chu_dict_er[key].items()] + [(inf,)]
        tsk_chus_er.sort()
        tsk_chu_dict[key] = []
        i = 0
        j = 0
        for k in range(len(tsk_chus_ee) + len(tsk_chus_er) - 2):
            if tsk_chus_ee[i][0] <= tsk_chus_er[j][0]:
                tsk_chu_dict[key].append(('EE',) + tsk_chus_ee[i])
                i += 1
            else:
                tsk_chu_dict[key].append(('ER',) + tsk_chus_er[j])
                j += 1
    return tsk_chu_dict


def get_ses_dict():
    ''' reads list of relevant sessions, returns dict '''
    ses_dict = {}
    for line in fio.readlines(cfg.META_PATH_DC, 'sessions'):
        # sessions are indexed by spk_id pair in file, count pairs for ses_id
        ses_id = len(ses_dict) + 1
        spk_id_b = line[1:4]
        spk_id_a = line[5:8]
        # store conversion from spk_id pair to ses_id in dict
        ses_dict['%s_%s' % (spk_id_b, spk_id_a)] = [ses_id, spk_id_b, spk_id_a]
    return ses_dict


def populate_speakers(ses_dict):
    ''' populates speakers table from dict of relevant sessions '''
    # dict to track speakers stored in database
    spk_dict = {}
    # only read interviewee file, all speakers take either role
    fname = 'chunks_ee.csv'
    for row in fio.read_csv(cfg.META_PATH_DC, fname, skip_header=True):
        ses = '%s_%s' % (row[0][1:4], row[0][5:8])
        if ses in ses_dict and row[13] not in spk_dict:
            # session is relevant and speaker not in database yet
            gender = 'f' if row[15] == 'Female' else 'm'
            db.ins_spk_dc(
                row[13], gender, row[16], row[19], row[21], row[22], row[23],
                row[33], row[35], row[32], row[34], row[31])
            spk_dict[row[13]] = 1


def populate_sessions_and_tasks(ses_dict):
    ''' populates sessions/tasks tables from dict of relevant sessions '''
    for ses_id, spk_id_b, spk_id_a in ses_dict.values():
        db.ins_ses_dc(ses_id, spk_id_a, spk_id_b)
        # B is always interviewer first
        db.ins_tsk_dc(2*ses_id-1, ses_id, 1, 'B')
        db.ins_tsk_dc(2*ses_id, ses_id, 2, 'A')


def populate_turns_and_chunks(ses_dict):
    ''' populates turns/chunks tables from meta-data for relevant sessions '''
    # load chunks to dicts from meta-data csv files 
    tsk_chu_dict_ee = _load_chunks(ses_dict, 'EE')
    tsk_chu_dict_er = _load_chunks(ses_dict, 'ER')
    # merge chunk dicts by starting timestamps
    tsk_chu_dict = _merge_chunks(tsk_chu_dict_ee, tsk_chu_dict_er)
    
    chu_id = 0
    tur_id = 0
    # iterate over merged dict to insert chunks; insert turns as needed
    for tsk_id, chunks in tsk_chu_dict.items():
        turn_index = 0
        chunk_index = 0
        role_prev = None
        for chunk in chunks:
            role = 'd' if chunk[0] == 'ER' else 'f'
            if role_prev != role:
                # change in role marks new turn; insert turn first
                tur_id += 1
                turn_index += 1
                chunk_index = 0
                db.ins_tur_dc(tur_id, tsk_id, turn_index, role)
            chu_id += 1
            chunk_index += 1
            db.ins_chu(chu_id, tur_id, chunk_index, *chunk[1:])
            role_prev = role


def extract_features(ses_id):
    ''' runs feature extraction for all chunks in given session, updates db '''
    db.connect(cfg.CORPUS_ID_DC)
    path = cfg.get_corpus_path(cfg.CORPUS_ID_DC)
    path += 'wav_segments/ses' + str(ses_id) + '/'
    for a_or_b, ch in [('A', 1), ('B', 2)]:
        all_features = {}
        for chu_id, words, start, end, task_index, spk_id_a, spk_id_b \
        in db.find_chunks(ses_id, a_or_b):
            if end - start >= 0.04: # min duration for 75Hz min pitch
                fname = 'p%dp%d-part%d_ch%d:%f:%f.wav' % \
                    (spk_id_b, spk_id_a, task_index, ch, start, end)
                all_features[chu_id] = fio.extract_features(
                    path, fname, ses_id, chu_id, words, start, end, False)
        # function is invoked in parallel, database might be locked;
        # keep trying to update until it works
        done = False
        while not done:
            try:
                for chu_id, features in all_features.items():
                    db.set_features(chu_id, features)
                db.commit()
                done = True
            except sqlite3.OperationalError:
                pass
    db.close()









