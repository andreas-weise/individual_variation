-- tables for deception corpus analysis
-- interviewers are marked as "d"escribers throughout to allow for reuse of code
-- (interviewees as "f"ollowers)

DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS turns;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS speakers;



CREATE TABLE speakers (
    spk_id         INTEGER NOT NULL,
    gender         TEXT NOT NULL,
    native_lang    TEXT NOT NULL,
    age            NUMERIC,
    orig_cntry     TEXT,
    home_lang      TEXT,
    other_lang     TEXT, 
    neo_o          NUMERIC,
    neo_c          NUMERIC,
    neo_e          NUMERIC,
    neo_a          NUMERIC,
    neo_n          NUMERIC,
    PRIMARY KEY (spk_id)
);



CREATE TABLE sessions (
    ses_id      INTEGER NOT NULL,
    spk_id_a    INTEGER NOT NULL,
    spk_id_b    INTEGER NOT NULL,
    -- topic (never populated, only for consistency with fisher corpus)
    top_id      INTEGER DEFAULT 0,
    PRIMARY KEY (ses_id),
    FOREIGN KEY (spk_id_a) REFERENCES speakers (spk_id),
    FOREIGN KEY (spk_id_b) REFERENCES speakers (spk_id)
);



CREATE TABLE tasks (
    -- each task is one of two interviews between a pair of speakers
    -- speaker A (channel 1) is interviewee in task 1, B in task 2
    tsk_id        INTEGER NOT NULL,
    ses_id        INTEGER NOT NULL,
    task_index    INTEGER NOT NULL,
    -- who is interviewer (i.e., "d"escriber), A or B
    a_or_b        TEXT NOT NULL,
    PRIMARY KEY (tsk_id),
    FOREIGN KEY (ses_id) REFERENCES sessions (ses_id)
);



CREATE TABLE turns (
    tur_id            INTEGER NOT NULL,
    tsk_id            INTEGER NOT NULL,
    -- index of the turn within its task
    turn_index        INTEGER NOT NULL,
    -- index of the turn within its session
    turn_index_ses    INTEGER,
    turn_type         TEXT,
    -- interviewer ("d"escriber) or interviewee ("f"ollower)
    speaker_role      TEXT NOT NULL,
    PRIMARY KEY (tur_id),
    FOREIGN KEY (tsk_id) REFERENCES tasks (tsk_id)
);



CREATE TABLE chunks (
    -- inter-pausal units with acoustic-prosodic and lexical data
    -- "pause-free units of speech from a single speaker separated from one 
    --  another by at least 50ms" (Levitan and Hirschberg, 2011)
    chu_id            INTEGER NOT NULL,
    tur_id            INTEGER NOT NULL,
    chunk_index       INTEGER NOT NULL,
    start_time        NUMERIC,
    end_time          NUMERIC,
    -- duration redundant for consistency with games corpus structure
    duration          INTEGER,
    -- original transcription with all markup
    transcript        TEXT,
    -- parsed transcription without markup
    words             TEXT,
    pitch_min         NUMERIC,
    pitch_max         NUMERIC,
    pitch_mean        NUMERIC,
    pitch_std         NUMERIC,
    rate_syl          NUMERIC,
    rate_vcd          NUMERIC,
    intensity_min     NUMERIC,
    intensity_max     NUMERIC,
    intensity_mean    NUMERIC,
    intensity_std     NUMERIC,
    jitter            NUMERIC,
    shimmer           NUMERIC,
    nhr               NUMERIC,
    PRIMARY KEY (chu_id),
    FOREIGN KEY (tur_id) REFERENCES turns (tur_id)
);



CREATE UNIQUE INDEX chu_pk ON chunks (chu_id);
CREATE INDEX chu_tur_fk ON chunks (tur_id);
CREATE UNIQUE INDEX tur_pk ON turns (tur_id);
CREATE INDEX tur_tsk_fk ON turns (tsk_id);
CREATE UNIQUE INDEX tsk_pk ON tasks (tsk_id);
CREATE INDEX tsk_ses_fk ON tasks (ses_id);
CREATE UNIQUE INDEX ses_pk ON sessions (ses_id);
CREATE INDEX ses_spk_a_fk ON sessions (spk_id_a);
CREATE INDEX ses_spk_b_fk ON sessions (spk_id_b);
CREATE UNIQUE INDEX spk_pk ON speakers (spk_id);

