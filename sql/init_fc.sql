-- tables for fisher corpus analysis
-- same format as for games corpus analysis (including superfluous tasks table)
--     allows for reuse of code


DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS turns;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS speakers;
DROP TABLE IF EXISTS topics;



-- fe_03_pindata.tbl
CREATE TABLE speakers (
    spk_id          INTEGER NOT NULL,
    gender          TEXT,
    age             INTEGER,
    years_edu       INTEGER,
    native_lang     TEXT,
    where_raised    TEXT,
    -- stays NULL for Fisher Corpus, only included for consistent interface
    -- with Deception Corpus
    other_lang      TEXT, 
    PRIMARY KEY (spk_id)
);



-- fe_03_topics.sgm
CREATE TABLE topics (
    -- conversation topics given to subjects
    top_id     INTEGER NOT NULL,
    title      TEXT,
    details    TEXT,
    PRIMARY KEY (top_id)
);



-- fe_03_pX_calldata
CREATE TABLE sessions (
    -- session = complete phone conversation, up to 10 mins; 
    -- not broken up as in games corpus
    ses_id      INTEGER NOT NULL,
    spk_id_a    INTEGER NOT NULL,
    spk_id_b    INTEGER NOT NULL,
    top_id      INTEGER,
    PRIMARY KEY (ses_id),
    FOREIGN KEY (spk_id_a) REFERENCES speakers (spk_id),
    FOREIGN KEY (spk_id_b) REFERENCES speakers (spk_id),
    FOREIGN KEY (top_id) REFERENCES topics (top_id)
);



CREATE TABLE tasks (
    -- unnecessary table, only to match games corpus structure
    -- task_index always set to 1, a_or_b always set to "A"
    tsk_id            INTEGER NOT NULL,
    ses_id            INTEGER NOT NULL,    
    task_index        INTEGER DEFAULT 1,
    a_or_b            TEXT DEFAULT "A",
    transcribed_by    TEXT,
    date_time         STRING NOT NULL,
    signal_quality    NUMERIC NOT NULL,
    conv_quality      NUMERIC NOT NULL,
    -- this comes from an auditor; can differ from info in speaker table
    -- (sometimes wrong speaker takes the call) 
    gender_a          TEXT NOT NULL,
    gender_b          TEXT NOT NULL,
    dialect_a         TEXT NOT NULL,
    dialect_b         TEXT NOT NULL,
    phnum_a           TEXT,
    phnum_b           TEXT,
    phset_a           TEXT,
    phset_b           TEXT,
    phtype_a          TEXT,
    phtype_b          TEXT,
    PRIMARY KEY (tsk_id),
    FOREIGN KEY (ses_id) REFERENCES sessions (ses_id)
);



CREATE TABLE turns (
    -- turn = "maximal sequence of inter-pausal units from a single speaker"
    -- (Levitan and Hirschberg, 2011)
    tur_id            INTEGER NOT NULL,
    tsk_id            INTEGER NOT NULL,
    turn_type         TEXT,
    -- index of the turn within its task 
    turn_index        INTEGER NOT NULL,
    -- index of the turn within its session
    -- (same as for task, column only included for consistency)
    turn_index_ses    INTEGER NOT NULL,
    speaker_role      TEXT NOT NULL,
    PRIMARY KEY (tur_id),
    FOREIGN KEY (tsk_id) REFERENCES tasks (tsk_id)
);



CREATE TABLE chunks (
    -- inter-pausal units with acoustic-prosodic and lexical data
    -- "pause-free units of speech from a single speaker separated from one 
    --  another by at least 50ms" (Levitan and Hirschberg, 2011)
    -- note: alignment information is not that detailed for fisher corpus;
    --       chunks might contain pauses of more than 50ms
    --       those are removed by a praat script; some might still remain
    chu_id            INTEGER NOT NULL,
    tur_id            INTEGER NOT NULL,
    chunk_index       INTEGER NOT NULL,
    -- original start and end times from transcript
    start_time_og     NUMERIC,
    end_time_og       NUMERIC,
    -- true start and end times after trimming initial and final silences
    start_time        NUMERIC,
    end_time          NUMERIC,
    -- duration after cutting pauses, can differ from end_time - start_time
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
CREATE INDEX ses_top_fk ON sessions (top_id);
CREATE UNIQUE INDEX spk_pk ON speakers (spk_id);
CREATE UNIQUE INDEX top_pk ON topics (top_id);

