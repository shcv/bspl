+!result(TA, Prof, SID, QID, Answer, Solution, Grade) <-
  if (Answer = Solution) {
    .print(SID,QID,Answer,"matches",Solution);
    Grade = 1;
  } else {
    .print(SID,QID,Answer,"does not match",Solution);
    Grade = 0;
  }
  .print("Grade: ",Grade).
