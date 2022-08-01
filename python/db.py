import pandas as pd
import sqlite3

import cfg
import fio



################################################################################
#                            CONNECTION MAINTENANCE                            #
################################################################################

class DatabaseConnection(object):
    def __init__(self, db_fname):
        self._conn = sqlite3.connect(db_fname)
        self._c = self._conn.cursor()

    def __del__(self):
        self._conn.close()

    def execute(self, sql_stmt, params=tuple()):
        return self._c.execute(sql_stmt, params)

    def executemany(self, sql_stmt, params=tuple()):
        return self._c.executemany(sql_stmt, params)

    def executescript(self, sql_script):
        return self._c.executescript(sql_script)

    def getrowcount(self):
        return self._c.rowcount

    def commit(self):
        self._conn.commit()

    def get_conn(self):
        return self._conn

# global connection object; status maintained through functions below
# all functions interacting with database (setters etc.) assume open connection
dbc = None


def connect(corpus_id):
    ''' instantiates global connection object for given corpus '''
    global dbc
    dbc = DatabaseConnection(cfg.get_db_fname(corpus_id))


def close():
    ''' closes connection by deleting global connection object '''
    global dbc
    del dbc
    dbc = None


def commit():
    ''' issues commit to database via global connection object '''
    dbc.commit()


def get_conn():
    ''' returns internal sqlite3 connection of global connection object 

    this should rarely be necessary, only if conn needs to be passed on '''
    return dbc.get_conn()



################################################################################
#                                  INSERTIONS                                  #
################################################################################

def ins_spk(spk_id, gender, age, years_edu, native_lang, where_raised):
    ''' inserts individual speaker in fisher corpus speakers table '''
    sql_stmt = \
        'INSERT INTO speakers ' \
            '(spk_id, gender, age, years_edu, native_lang, where_raised)\n' \
        'VALUES (?,?,?,?,?,?);'
    dbc.execute(sql_stmt, 
                (spk_id, gender, age, years_edu, native_lang, where_raised))

def ins_spk_dc(
        spk_id, gender, native_lang, age, orig_cntry, home_lang, other_lang,
        neo_o, neo_c, neo_e, neo_a, neo_n):
    ''' inserts individual speaker in deception corpus speakers table '''
    sql_stmt = \
        'INSERT INTO speakers ' \
            '(spk_id, gender, native_lang, age, orig_cntry, home_lang,' \
            ' other_lang, neo_o, neo_c, neo_e, neo_a, neo_n)\n' \
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
    params = (spk_id, gender, native_lang, age, orig_cntry, home_lang, 
              other_lang, neo_o, neo_c, neo_e, neo_a, neo_n)
    dbc.execute(sql_stmt, params)


def ins_top_fc(top_id, title, details):
    ''' inserts individual topic in fisher corpus topics table '''
    sql_stmt = \
        'INSERT INTO topics(top_id, title, details)\n' \
        'VALUES (?,?,?)'
    dbc.execute(sql_stmt, (top_id, title, details))


def ins_ses_fc(ses_id, spk_id_a, spk_id_b, top_id):
    ''' inserts individual session in fisher corpus sessions table '''
    sql_stmt = \
        'INSERT INTO sessions (ses_id, spk_id_a, spk_id_b, top_id)\n' \
        'VALUES(?,?,?,?);'
    dbc.execute(sql_stmt, (ses_id, spk_id_a, spk_id_b, top_id))


def ins_ses_dc(ses_id, spk_id_a, spk_id_b):
    ''' inserts individual session in deception corpus sessions table '''
    sql_stmt = \
        'INSERT INTO sessions (ses_id, spk_id_a, spk_id_b)\n' \
        'VALUES(?,?,?);'
    dbc.execute(sql_stmt, (ses_id, spk_id_a, spk_id_b))


def ins_tsk_fc(ses_id, date_time, signal_quality, 
        conv_quality, gender_a, gender_b, dialect_a, dialect_b, 
        phnum_a, phnum_b, phset_a, phset_b, phtype_a, phtype_b):
    ''' inserts individual task in fisher corpus tasks table '''
    sql_stmt = \
        'INSERT INTO tasks (tsk_id, ses_id, date_time,' \
            ' signal_quality, conv_quality, gender_a, gender_b,' \
            ' dialect_a, dialect_b, phnum_a, phnum_b, phset_a, phset_b,' \
            ' phtype_a, phtype_b)\n' \
        'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
    params = (ses_id, ses_id, date_time, signal_quality, conv_quality, 
              gender_a, gender_b, dialect_a, dialect_b, 
              phnum_a, phnum_b, phset_a, phset_b, phtype_a, phtype_b)
    # tasks are only dummies, same id as ses (see init_fc.sql)
    dbc.execute(sql_stmt, params)


def ins_tsk_dc(tsk_id, ses_id, task_index, a_or_b):
    ''' inserts individual task in deception corpus tasks table '''
    sql_stmt = \
        'INSERT INTO tasks (tsk_id, ses_id, task_index, a_or_b)\n' \
        'VALUES(?,?,?,?);'
    dbc.execute(sql_stmt, (tsk_id, ses_id, task_index, a_or_b))


def ins_tur(tur_id, ses_id, turn_index, speaker_role):
    ''' inserts individual turn in fisher corpus turns table '''
    # sessions = tasks here, so tsk_id = ses_id and turn_index = turn_index_ses
    sql_stmt = \
        'INSERT INTO turns ' \
            '(tur_id, tsk_id, turn_index, turn_index_ses, speaker_role)\n' \
        'VALUES (?,?,?,?,?);'
    dbc.execute(
        sql_stmt, (tur_id, ses_id, turn_index, turn_index, speaker_role))


def ins_tur_dc(tur_id, ses_id, turn_index, speaker_role):
    ''' inserts individual turn in deception corpus turns table '''
    sql_stmt = \
        'INSERT INTO turns (tur_id, tsk_id, turn_index, speaker_role)\n' \
        'VALUES (?,?,?,?);'
    dbc.execute(sql_stmt, (tur_id, ses_id, turn_index, speaker_role))


def ins_chu(chu_id, tur_id, chunk_index, start, end, transcript, words, 
            time_suffix=''):
    ''' inserts individual chunk in chunks table (either corpus) '''
    sql_stmt = \
        'INSERT INTO chunks (chu_id, tur_id, chunk_index, ' \
            'start_time' + time_suffix + ', end_time' + time_suffix + ', ' \
            'transcript, words)\n' \
        'VALUES (?,?,?,?,?,?,?);'
    dbc.execute(
        sql_stmt, (chu_id, tur_id, chunk_index, start, end, transcript, words))



################################################################################
#                           SETTERS (SIMPLE UPDATES)                           #
################################################################################

def set_trans_by(ses_id, trans_by):
    ''' updates given session with info how it was transcribed (fisher only) '''
    sql_stmt = \
        'UPDATE tasks\n' \
        'SET    transcribed_by = ?\n' \
        'WHERE  ses_id = ?;'
    dbc.execute(sql_stmt, (trans_by, ses_id))


def set_turn_index_ses():
    ''' sets the session-wide turn index for all sessions (deception corpus) '''
    sql_stmt = \
        'UPDATE turns\n' \
        'SET turn_index_ses = (\n' \
        '    SELECT COUNT(tur2.tur_id) + 1\n' \
        '    FROM   turns tur2\n' \
        '    JOIN   tasks tsk2\n' \
        '    ON     tur2.tsk_id == tsk2.tsk_id\n' \
        '    WHERE  tsk2.ses_id = (\n' \
        '        SELECT ses_id FROM tasks WHERE tsk_id = turns.tsk_id\n' \
        '    )\n' \
	    '    -- assumes that tsk_id is sorted by task_index within ses_id\n' \
	    '    AND   (   tur2.tsk_id < turns.tsk_id\n' \
	    '           OR (    tur2.tsk_id = turns.tsk_id\n' \
        '               AND tur2.turn_index < turns.turn_index\n' \
        '           )\n' \
	    '    )\n' \
        ');'
    dbc.execute(sql_stmt)


def set_features(chu_id, features):
    ''' sets features of given chunk '''
    sql_stmt = \
        'UPDATE chunks\n' \
        'SET    start_time = ?,\n' \
        '       end_time = ?,\n' \
        '       duration = ?,\n' \
        '       pitch_min = ?,\n' \
        '       pitch_max = ?,\n' \
        '       pitch_mean = ?,\n' \
        '       pitch_std = ?,\n' \
        '       rate_syl = ?,\n' \
        '       rate_vcd = ?,\n' \
        '       intensity_min = ?,\n' \
        '       intensity_max = ?,\n' \
        '       intensity_mean = ?,\n' \
        '       intensity_std = ?,\n' \
        '       jitter = ?,\n' \
        '       shimmer = ?,\n' \
        '       nhr = ?\n' \
        'WHERE  chu_id == ?;'
    dbc.execute(sql_stmt, 
                (round(features['start_point'], 3),
                 round(features['end_point'], 3),
                 round(features['dur'], 3),
                 features['f0_min'],
                 features['f0_max'],
                 features['f0_mean'],
                 features['f0_std'],
                 features['rate_syl'],
                 features['vcd2tot_frames'],
                 features['int_min'],
                 features['int_max'],
                 features['int_mean'],
                 features['int_std'],
                 features['jitter'],
                 features['shimmer'],
                 features['nhr'],
                 chu_id))


def set_duration():
    ''' sets chunk duration (after timestamps rounded in set_features) '''
    sql_stmt = \
        'UPDATE chunks\n' \
        'SET duration = end_time - start_time;'
    dbc.execute(sql_stmt)



################################################################################
#                           GETTERS (SIMPLE SELECTS)                           #
################################################################################

def get_ses_ids():
    ''' returns ses_id for all sessions in order '''
    sql_stmt = \
        'SELECT ses_id\n' \
        'FROM   sessions\n' \
        'ORDER BY ses_id;'
    return [int(v[0]) for v in dbc.execute(sql_stmt).fetchall()]



################################################################################
#                                    OTHER                                     #
################################################################################

def executescript(path, fname):
    ''' executes given file as script '''
    # users should obviously not have the ability to execute arbitrary scripts,  
    # but this project is not for end users, just privately run data analysis
    dbc.executescript(''.join(fio.readlines(path, fname)))


def pd_read_sql_query(sql_stmt='', sql_fname=''):
    ''' runs given sql query and returns pandas dataframe of result 

    establishes and closes db connection for each call

    args:
        sql_stmt: sql statement to execute (only run if no filename given)
        sql_fname: filename (in cfg.SQL_PATH) from where to load sql statement
    returns:
        pandas dataframe with query result set 
    '''
    assert len(sql_stmt) > 0 or len(sql_fname) > 0, 'need sql query or filename'
    if len(sql_fname) > 0:
        sql_stmt = '\n'.join(fio.readlines(cfg.SQL_PATH, sql_fname))
    df = pd.read_sql_query(sql_stmt, get_conn())
    return df


def find_chunks(ses_id, a_or_b, time_suffix=''):
    ''' yields all chunks for given speaker (A or B) in given session '''
    sql_stmt = \
        'SELECT chu.chu_id,\n' \
        '       chu.words,\n' \
        '       chu.start_time' + time_suffix + ',\n' \
        '       chu.end_time' + time_suffix + ',\n' \
        '       tsk.task_index,\n' \
        '       ses.spk_id_a,\n' \
        '       ses.spk_id_b\n' \
        'FROM   chunks chu\n' \
        'JOIN   turns tur\n' \
        'ON     chu.tur_id == tur.tur_id\n' \
        'JOIN   tasks tsk\n' \
        'ON     tur.tsk_id == tsk.tsk_id\n' \
        'JOIN   sessions ses\n' \
        'ON     tsk.ses_id == ses.ses_id\n' \
        'WHERE  ses.ses_id == ?\n' \
        'AND    CASE\n' \
        '           WHEN tur.speaker_role == "d" AND tsk.a_or_b == "A"\n' \
        '           THEN "A"\n' \
        '           WHEN tur.speaker_role == "f" AND tsk.a_or_b == "B"\n' \
        '           THEN "A"\n' \
        '           ELSE "B"\n' \
        '       END == ?\n'
    res = dbc.execute(sql_stmt, (ses_id, a_or_b)).fetchall()
    for chu_id, words, start, end, task_index, spk_id_a, spk_id_b in res:
        yield(chu_id, words, start, end, task_index, spk_id_a, spk_id_b)







