# paths within the project 
SQL_PATH = '../sql/'
PRAAT_PATH = '../praat/'

# corpus identifiers
CORPUS_ID_FC = 'FC'
CORPUS_ID_DC = 'XCDC'
CORPUS_IDS = [CORPUS_ID_FC, CORPUS_ID_DC]

# external paths (corpora directories and temporary file directory)
# comment back in and point to corpora 
# CORPUS_PATH_FC = ''
# CORPUS_PATH_DC = ''
META_PATH_FC = CORPUS_PATH_FC + 'meta/'
META_PATH_DC = CORPUS_PATH_DC + 'meta/'
# set as needed
TMP_PATH = ''

# database filenames
DB_FNAME_FC = '../../fc.db'
DB_FNAME_DC = '../../xcdc.db'

# praat and sql scripts
PRAAT_CUT_FNAME = 'extract_part_and_cut_pauses.praat'
PRAAT_EXTRACT_FNAME = 'extract_features.praat'
SQL_INIT_FNAME_FC = 'init_fc.sql'
SQL_INIT_FNAME_DC = 'init_xcdc.sql'
SQL_DI_FNAME = 'fc_del_irrelevant_ses.sql'
SQL_CU_FNAME = 'cleanup.sql'
SQL_FT_FNAME = 'fix_timestamps.sql'
SQL_AT_FNAME = 'aux_tables.sql'
SQL_BT_FNAME = 'big_table.sql'
SQL_SP_FNAME = 'speaker_pairs.sql'

# normalization types
NRM_SPK = 'SPEAKER'
NRM_GND = 'GENDER'
NRM_RAW = 'RAW'
NRM_TYPES = [NRM_SPK, NRM_GND, NRM_RAW]

# entrainment measure identifiers
MEA_LCON = 'lcon'
MEA_SYN  = 'syn'
MEASURES = [MEA_LCON, MEA_SYN]

# all features computed by praat and those actually analyzed
FEATURES_ALL = [
    'intensity_mean',
    'intensity_std',
    'intensity_min',
    'intensity_max',
    'pitch_mean',
    'pitch_std',
    'pitch_min',
    'pitch_max',
    'jitter',
    'shimmer',
    'nhr',
    'rate_syl',
    'rate_vcd'
]
FEATURES = [
    'intensity_mean',
    'intensity_max',
    'pitch_mean',
    'pitch_max',
    'jitter',
    'shimmer',
    'nhr',
    'rate_syl'
]

# (tsk_id, spk_id) combinations to exclude in the deception corpus
# (half of those between pairs that match in gender and native language;
#  manually selected to balance interviewees & interviewers as well as 
#  speakers who are interviewee first or interviewer first)
TSK_SPK_EXCL_DC = [
    # speaker A excluded in both tasks of the respective session
    # (speakers A are always interviewee first)
      (3, 203),   (4, 203),   (9, 209),  (10, 209),  (15, 221),  (16, 221), 
     (19, 227),  (20, 227),  (29, 237),  (30, 237),  (39, 247),  (40, 247), 
     (47, 255),  (48, 255),  (53, 261),  (54, 261),  (73, 281),  (74, 281), 
     (81, 289),  (82, 289),  (83, 295),  (84, 295),  (85, 303),  (86, 303), 
     (87, 305),  (88, 305), (113, 355), (114, 355), (117, 363), (118, 363),
    (119, 365), (120, 365), (123, 369), (124, 369), (125, 371), (126, 371), 
    (133, 379), (134, 379), (135, 381), (136, 381), (137, 383), (138, 383), 
    (139, 385), (140, 385), (141, 387), (142, 387), (147, 401), (148, 401), 
    (155, 411), (156, 411), (177, 435), (178, 435), (181, 439), (182, 439), 
    (187, 445), (188, 445), 
    # speaker B excluded in both tasks of the respective session
    # (speakers B are always interviewer first)
     (93, 318),  (94, 318),  (99, 326), (100, 326), (101, 328), (102, 328), 
    (103, 330), (104, 330), (105, 334), (106, 334), (109, 350), (110, 350), 
    (127, 372), (128, 372), (149, 402), (150, 402), (151, 406), (152, 406), 
    (153, 408), (154, 408), (157, 412), (158, 412), (159, 414), (160, 414), 
    (161, 416), (162, 416), (165, 420), (166, 420), (189, 448), (190, 448), 
    (191, 450), (192, 450), (203, 464), (204, 464), (213, 474), (214, 474), 
    (215, 476), (216, 476), (217, 478), (218, 478), (223, 484), (224, 484), 
    (231, 492), (232, 492), (233, 494), (234, 494), (237, 498), (238, 498), 
    (239, 500), (240, 500), (241, 502), (242, 502), (249, 510), (250, 510), 
    (253, 516), (254, 516), 
    # both speakers excluded in a task with task_index 2 (A interviewer)
    (130, 374), (130, 375), (222, 482), (222, 483), 
    # both speakers excluded in a task with task_index 1 (A interviewee)
    (257, 520), (257, 521), (269, 532), (269, 533)
]


def check_corpus_id(corpus_id):
    assert corpus_id in CORPUS_IDS, 'unknown corpus id'


def check_mea_id(mea_id):
    assert mea_id in MEASURES, 'unknown entrainment measure'


def get_db_fname(corpus_id):
    check_corpus_id(corpus_id)
    return DB_FNAME_FC if corpus_id == CORPUS_ID_FC else DB_FNAME_DC


def get_corpus_path(corpus_id):
    check_corpus_id(corpus_id)
    return CORPUS_PATH_FC if corpus_id == CORPUS_ID_FC else CORPUS_PATH_DC


