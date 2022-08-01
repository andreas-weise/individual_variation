# Influence of gender and native language on entrainment

This is an updated version of the code for the following paper (with slightly different results):
Weise, A., Levitan, S. I., Hirschberg, J., & Levitan, R. (2019). Individual differences in acoustic-prosodic entrainment in spoken dialogue. Speech Communication, 115(April), 78–87. https://doi.org/10.1016/j.specom.2019.10.007

Two local, acoustic-prosodic measures are computed and analyzed for a subset of sessions from the Fisher Corpus and the Columbia X-Cultural Deception Corpus. Data for the corpora is not contained.

One of the Praat scripts included in this project uses the Praat Vocal Toolkit, which is not included but can be downloaded from https://www.praatvocaltoolkit.com/.

## Directory Overview

<ul>
    <li>jupyter: a sequence of Jupyter notebooks that invoke all SQL/python code to process and analyze the corpora</li>
    <li>praat: Praat scripts for audio preprocessing (pause removal) and feature extraction</li>
    <li>python: modules for data processing and analysis invoked from the Jupyter notebooks; file overview:
        <ul>
            <li>ana.py: functions for the analysis of the entrainment measures</li>
            <li>ap.py: implementation of two acoustic-prosodic entrainment measures</li>
            <li>aux.py: auxiliary functions</li>
            <li>cfg.py: configuration constants; if you received the corpus data (separately), configure the correct paths here</li>
            <li>db.py: interaction with the corpus databases</li>
            <li>dc.py: functions specific to the deception corpus</li>
            <li>fc.py: functions specific to the fisher corpus</li>
            <li>fio.py: file i/o</li>
        </ul>
    </li>
    <li>R: single R script to execute ANOVAs</li>
    <li>sql: core sql scripts that initialize the database files and are used during processing/analysis; file overview:
        <ul>
            <li>aux_tables.sql: creates chunk_pairs table with turn exchanges for local entrainment measures (only adjacent pairs)</li>
            <li>big_table.sql: SELECT to flatten normalized, hierarchical schema into one wide, unnormalized table for analysis</li>
            <li>cleanup.sql: auxiliary script for cleanup after feature extraction</li>
            <li>fc_del_irrelevant_ses.sql: deletes all data relating to unused fisher corpus sessions</li>
            <li>fix_timestamps.sql: ensures continuous timestamps for all chunks in a session (no reset per task)</li>
            <li>init_fc.sql: creates and documents the hierarchical database schema for the fisher corpus</li>
            <li>init_xcdc.sql: creates and documents the hierarchical database schema for the x-cultural deception corpus</li>
            <li>speaker_pairs.sql: SELECT to determine partner and non-partner pairs of speakers for analysis</li>
        </ul>
    </li>
</ul>
