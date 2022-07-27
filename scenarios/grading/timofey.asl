+response(Student, TA, SID, QID, Question, Answer)
  : rubric(Prof, TA, SID, QID, Solution) <-
  !grade(SID, QID, Answer, Solution).

+rubric(Prof, TA, SID, QID, Solution)
  : response(Student, TA, SID, QID, Question, Answer) <-
  !grade(SID, QID, Answer, Solution).

+!grade(SID, QID, Answer, Solution) <-
  if (Answer = Solution) {
    .print(SID,QID,Answer,"matches",Solution);
    Grade = 1;
  } else {
    .print(SID,QID,Answer,"does not match",Solution);
    Grade = 0;
  }
  .print("Grade: ",Grade);
  .emit(result(TA, _, SID, QID, Answer, Solution, Grade)).
