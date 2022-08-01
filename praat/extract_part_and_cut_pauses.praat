form Test
    word in_filename
    word out_filename_wav
    word out_filename_txt
    real start_point
    real end_point
endform

long_sound = Open long sound file... 'in_filename$'
sound1 = Extract part... 'start_point' 'end_point' no
total_duration = Get total duration

text_grid = To TextGrid (silences)... 75 0 -25 0.1 0.1 silent sounding
interval_count = Get number of intervals... 1

# determine actual start of utterance
start_label$ = Get label of interval... 1 1
if start_label$ == "silent"
    start_offset = Get end point... 1 1
else
    start_offset = 0.0
endif

# determine actual end of utterance
end_label$ = Get label of interval... 1 interval_count
if end_label$ == "silent"
    end_offset = Get start point... 1 interval_count
    end_offset = total_duration - end_offset
else
    end_offset = 0.0
endif

start_point = start_point + start_offset
end_point = end_point - end_offset

# write offsets to text file
text$ = "" 
text$ > 'out_filename_txt$'

text$ = "start_point,'start_point''newline$'"
text$ >> 'out_filename_txt$'
text$ = "end_point,'end_point''newline$'"
text$ >> 'out_filename_txt$'

# cut pauses from utterance, write result to wav file
select long_sound
sound2 = Extract part... 'start_point' 'end_point' no
execute plugin_VocalToolkit/cutpauses.praat
Save as WAV file... 'out_filename_wav$'

select sound1
plus sound2
plus long_sound
plus text_grid
Remove
