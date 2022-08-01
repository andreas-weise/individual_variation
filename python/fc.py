import sqlite3
import xml.dom.minidom 

import aux
import cfg
import db
import fio



def populate_speakers():
    ''' reads meta-data to populate speakers table '''
    fname = 'fe_03_pindata.tbl'
    for row in fio.read_csv(cfg.META_PATH_FC, fname, skip_header=True):
        spk_id = int(row[0])
        gender = None if row[1] == 'NA' else row[1].lower()
        age = None if row[2] == 'NA' else int(row[2])
        years_edu = None if row[3] == 'NA' else int(row[3])
        native_lang = None if row[4] == 'NA' else row[4]
        where_raised = None if row[5] == 'NA' else row[5]
        db.ins_spk_fc(spk_id, gender, age, years_edu, native_lang, where_raised)


def populate_topics():
    ''' reads meta-data to populate topics table '''
    xml_str = ''.join(list(fio.readlines(cfg.META_PATH_FC, 'fe_03_topics.sgm')))
    dom_tree = xml.dom.minidom.parseString(xml_str)
    for token in dom_tree.documentElement.getElementsByTagName('topic'):
        top_id = int(token.getAttribute('id')[3:])
        title = token.getAttribute('title')
        details = token.firstChild.nodeValue
        db.ins_top_fc(top_id, title, details)


def populate_sessions_and_tasks():
    ''' reads meta-data to populate tasks/sessions table '''
    # call data is split up in two files, process both
    for p in [1,2]:
        call_fname = 'fe_03_p%d_calldata.tbl' % p
        for row in fio.read_csv(cfg.META_PATH_FC, call_fname, skip_header=True):    
            # parse row (see doc_calldata_tbl.txt for fields)
            ses_id = int(row[0])
            date_time = row[1]
            top_id = None if row[2] == '' else int(row[2][3:])
            signal_quality = float(row[3])
            conv_quality = float(row[4])
            spk_id_a = int(row[5])
            gender_a = row[6].split('.')[0]
            dialect_a = row[6].split('.')[1]
            phnum_a = None if row[7] == 'no_APHNUM' else row[7]
            phset_a = 'speaker-phone' if row[8] == '1' \
                else 'headset' if row[8] == '2' \
                else 'ear-bud' if row[8] == '3' \
                else 'handheld' if row[8] == '4' \
                else None
            phtype_a = 'cell' if row[9] == '1' \
                else 'cordless' if row[9] == '2' \
                else 'regular (land-line)' if row[9] == '3' \
                else None
            spk_id_b = int(row[10])
            gender_b = row[11].split('.')[0]
            dialect_b = row[11].split('.')[1]
            phnum_b = None if row[12] == 'no_BPHNUM' else row[12]
            phset_b = 'speaker-phone' if row[13] == '1' \
                else 'headset' if row[13] == '2' \
                else 'ear-bud' if row[13] == '3' \
                else 'handheld' if row[13] == '4' \
                else None
            phtype_b = 'cell' if row[14] == '1' \
                else 'cordless' if row[14] == '2' \
                else 'regular (land-line)' if row[14] == '3' \
                else None
            db.ins_ses_fc(ses_id, spk_id_a, spk_id_b, top_id)
            db.ins_tsk_fc(ses_id, date_time, signal_quality, conv_quality, 
                 gender_a, gender_b, dialect_a, dialect_b, phnum_a, phnum_b, 
                 phset_a, phset_b, phtype_a, phtype_b)


def populate_turns_and_chunks():
    ''' populates turns/chunks tables from session transcripts '''
    # global ids for turns and chunks
    tur_id = 0
    chu_id = 0

    # session list is split up in two files, process both
    for p in [1,2]:
        list_fname = 'fe_03_p%d_filelist.tbl' % p
        for list_line in fio.readlines(cfg.META_PATH_FC, list_fname):
            audio_dir, ses_id_str, _, trans_by = list_line.split()
            ses_id = int(ses_id_str)
            db.set_trans_by(ses_id, trans_by)
            a_or_b_prev = ''
            turn_index = 0
            trans_fname = \
                'fe_03_p%d_tran/data/trans/%s/fe_03_%s.txt' % \
                (p, ses_id_str[:3], ses_id_str)
            for trans_line in fio.readlines(cfg.CORPUS_PATH_FC, trans_fname):
                items = trans_line.split()
                # skip empty lines and preamble
                if len(items) == 0 or items[0] == '#':
                    continue
                start = float(items[0])
                end = float(items[1])
                a_or_b = items[2][0]
                transcript = ' '.join(items[3:])
                words = aux.preprocess_transcript(transcript)

                if a_or_b != a_or_b_prev:
                    # utterance by new speaker; insert new turn
                    # A is always decriber, B always follower (roles not 
                    # needed, only for compatibility with other code)
                    speaker_role = 'd' if a_or_b == 'A' else 'f'
                    tur_id += 1
                    turn_index += 1
                    db.ins_tur(tur_id, ses_id, turn_index, speaker_role)
                    chunk_index = 0
                chu_id += 1
                chunk_index += 1
                db.ins_chu(chu_id, tur_id, chunk_index, start, end, transcript, 
                           words, '_og')
                a_or_b_prev = a_or_b
            if ses_id % 1000 == 0:
                print('%d done' % ses_id)
    print('%d done, finished!' % ses_id)


def extract_features(ses_id):
    ''' runs feature extraction for all chunks in given session, updates db '''
    db.connect(cfg.CORPUS_ID_FC)
    path = cfg.get_corpus_path(cfg.CORPUS_ID_FC)
    for a_or_b in ['A', 'B']:
        fname = '%d.%s.wav' % (ses_id, a_or_b)
        all_features = {}
        for chu_id, words, start, end, _, _, _ \
        in db.find_chunks(ses_id, a_or_b, '_og'):
            if end - start >= 0.04: # min duration for 75Hz min pitch
                all_features[chu_id] = fio.extract_features(
                    path, fname, ses_id, chu_id, words, start, end)
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
            


























