+rubric(MasID, Prof, Ta, SID, QID, Solution)
  : response(MasID, Student, Ta, SID, QID, Question, Answer)
  <- !send_result(MasID, Ta, Prof, SID, QID, Answer, Solution).

+response(MasID, Student, Ta, SID, QID, Question, Answer)
  : rubric(MasID, Prof, Ta, SID, QID, Solution)
  <- !send_result(MasID, Ta, Prof, SID, QID, Answer, Solution).

+!send_result(MasID, Ta, Prof, SID, QID, Answer, Solution)
  <- // insert code to compute result out parameters ['grade'] here
     .emit(result(MasID, Ta, Prof, SID, QID, Answer, Solution, Grade)).
