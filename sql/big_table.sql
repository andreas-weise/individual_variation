-- collects the tables of the normalized, hierarchical schema into a single,
-- unnormalized table with redundant information
WITH halfway_points AS
-- select assumes continuous timestamps per session, no reset per task!
-- start/end are determined based on *all* chunks, even those missing features
(
 SELECT NULL tsk_id,
        tsk.ses_id, 
        MIN(chu.start_time) + (MAX(chu.end_time) - MIN(chu.start_time)) / 2 ts
 FROM   chunks chu
 JOIN   turns tur
 ON     chu.tur_id == tur.tur_id
 JOIN   tasks tsk
 ON     tur.tsk_id == tsk.tsk_id
 GROUP BY tsk.ses_id

 UNION

 SELECT tur.tsk_id,
        NULL ses_id, 
        MIN(chu.start_time) + (MAX(chu.end_time) - MIN(chu.start_time)) / 2 ts
 FROM   chunks chu
 JOIN   turns tur
 ON     chu.tur_id == tur.tur_id
 GROUP BY tur.tsk_id
), spk AS
(
 SELECT tur.tur_id,
        CASE
            WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
            THEN "A"
            WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
            THEN "A"
            ELSE "B"
        END speaker_a_or_b,
        CASE
            WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
            THEN spk_a.spk_id
            WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
            THEN spk_a.spk_id
            ELSE spk_b.spk_id
        END spk_id,
        CASE
            WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
            THEN spk_a.gender
            WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
            THEN spk_a.gender
            ELSE spk_b.gender
        END gender,
        CASE
            WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
            THEN spk_a.native_lang
            WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
            THEN spk_a.native_lang
            ELSE spk_b.native_lang
        END native_lang,
        CASE
            WHEN tsk.a_or_b == "A" AND tur.speaker_role == "d"
            THEN spk_a.age
            WHEN tsk.a_or_b == "B" AND tur.speaker_role == "f"
            THEN spk_a.age
            ELSE spk_b.age
        END age
 FROM   turns tur
 JOIN   tasks tsk
 ON     tur.tsk_id == tsk.tsk_id
 JOIN   sessions ses
 ON     tsk.ses_id == ses.ses_id
 JOIN   speakers spk_a
 ON     ses.spk_id_a == spk_a.spk_id
 JOIN   speakers spk_b
 ON     ses.spk_id_b == spk_b.spk_id
), eng_age AS
(
 -- per chinese native speaker, the age at which they started speaking english,
 -- if available (documentation format is inconsistent, with or without comma 
 -- after "English", then always " age ", then up to two digits; code removes
 -- commata in search strings for consistent format)
 SELECT spk_id,
        CASE 
            WHEN INSTR(other_lang, 'English') != 0
            THEN CAST(
                     SUBSTR(
                         REPLACE(other_lang,',',''),
                         INSTR(
                             REPLACE(other_lang,',',''), 
                             'English'
                         )+12, -- need to skip 'English age '
                         2 -- up to two digits (trailing space if only one)
                     ) 
                     AS INTEGER
                 )
            ELSE NULL
        END eng_age
 FROM   speakers
 WHERE  native_lang == 'Chinese'
)
SELECT ses.ses_id,
       tsk.tsk_id,
       tur.tur_id,
       chu.chu_id,
       tsk.task_index,
       tur.turn_index,
       tur.turn_index_ses,
       chu.chunk_index,
       CASE 
           WHEN chu.start_time > hlf_ses.ts
           THEN 2
           ELSE 1
       END ses_half,
       CASE 
           WHEN chu.start_time > hlf_tsk.ts
           THEN 2
           ELSE 1
       END tsk_half,
       chu.start_time,
       chu.end_time,
       chu.duration,
       chu.words,
       chu.pitch_min pitch_min_raw,
       chu.pitch_max pitch_max_raw,
       chu.pitch_mean pitch_mean_raw,
       chu.pitch_std pitch_std_raw,
       chu.rate_syl rate_syl_raw,
       chu.rate_vcd rate_vcd_raw,
       chu.intensity_min intensity_min_raw,
       chu.intensity_max intensity_max_raw,
       chu.intensity_mean intensity_mean_raw,
       chu.intensity_std intensity_std_raw,
       chu.jitter jitter_raw,
       chu.shimmer shimmer_raw,
       chu.nhr nhr_raw,
       tur.speaker_role,
       tsk.a_or_b,
       spk.speaker_a_or_b,
       spk.spk_id,
       spk.gender,
       CASE 
           WHEN spk.native_lang == "Mandarin"
           THEN "Chinese"
           ELSE spk.native_lang
       END native_lang,
       spk.age,
       spk.age - eng_age.eng_age eng_yrs
FROM   chunks chu
JOIN   turns tur
ON     chu.tur_id == tur.tur_id
JOIN   tasks tsk
ON     tur.tsk_id == tsk.tsk_id
JOIN   sessions ses
ON     tsk.ses_id == ses.ses_id
JOIN   speakers spk_a
ON     ses.spk_id_a == spk_a.spk_id
JOIN   speakers spk_b
ON     ses.spk_id_b == spk_b.spk_id
JOIN   halfway_points hlf_tsk
ON     tsk.tsk_id == hlf_tsk.tsk_id
JOIN   halfway_points hlf_ses
ON     ses.ses_id == hlf_ses.ses_id
JOIN   spk
ON     tur.tur_id == spk.tur_id
LEFT JOIN eng_age
ON     spk.spk_id == eng_age.spk_id
ORDER BY ses.ses_id, tsk.task_index, tur.turn_index, chu.chunk_index;


