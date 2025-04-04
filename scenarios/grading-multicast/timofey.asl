+rubric(MasID, Prof, TA, TID, QID, Solution)
  : response(MasID, Student, TA, TID, QID, Question, Answer)
  <- !send_result(MasID, TA, Prof, TID, QID, Answer, Solution).

+response(MasID, Student, TA, TID, QID, Question, Answer)
  : rubric(MasID, Prof, TA, TID, QID, Solution)
  <- !send_result(MasID, TA, Prof, TID, QID, Answer, Solution).

+!send_result(MasID, TA, Prof, TID, QID, Answer, Solution)
  <- if (Answer = Solution) {
       .print(MasID, QID, Answer, "matches", Solution);
       Grade = 1;
     } else {
       .print(MasID, QID, Answer, "does not match", Solution);
       Grade = 0;
     }
     .print("Grade: ", Grade);
     .emit(result(MasID, TA, Prof, TID, QID, Answer, Solution, Grade)).
