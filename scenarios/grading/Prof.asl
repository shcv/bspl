+!send_begin_test
  <- // insert code to compute begin_test out parameters ['sID'] here
     .emit(begin_test(MasID, Prof, Student, SID)).

+begin_test(MasID, Prof, Student, SID)
  <- // insert code to compute challenge out parameters ['qID', 'question'] here
     .emit(challenge(MasID, Prof, Student, SID, QID, Question)).

+challenge(MasID, Prof, Student, SID, QID, Question)
  <- // insert code to compute rubric out parameters ['solution'] here
     .emit(rubric(MasID, Prof, Ta, SID, QID, Solution)).

