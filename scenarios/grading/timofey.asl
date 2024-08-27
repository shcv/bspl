+rubric(MasID, Prof, TA, SID, QID, Solution)
  : response(MasID, Student, TA, SID, QID, Question, Answer)
  <- !send_result(MasID, TA, Prof, SID, QID, Answer, Solution).

+response(MasID, Student, TA, SID, QID, Question, Answer)
  : rubric(MasID, Prof, TA, SID, QID, Solution)
  <- !send_result(MasID, TA, Prof, SID, QID, Answer, Solution).

+!send_result(MasID, TA, Prof, SID, QID, Answer, Solution)
  <- if (Answer = Solution) {
       .print(SID,QID,Answer,"matches",Solution);
       Grade = 1;
     } else {
       .print(SID,QID,Answer,"does not match",Solution);
       Grade = 0;
     }
     .print("Grade: ",Grade);
     .emit(result(MasID, TA, Prof, SID, QID, Answer, Solution, Grade)).
