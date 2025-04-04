question(q1, "What is your name?").
solution("lancelot", q1, "Sir Lancelot of Camelot").
solution("galahad", q1, "Sir Galahad of Camelot").
question(q2, "What is your quest?").
solution("lancelot", q2, "To seek the Holy Grail").
solution("galahad", q2, "To seek the Grail").
question(q3, "What is your favorite color?").
solution("lancelot", q3, "Blue").
solution("galahad", q3, "Yellow").

student("lancelot", "Lancelot").
student("galahad", "Galahad").

!start.

+!start <-
  TID = "midterm";
  .print("Starting test ", TID);
  .emitAll(begin_test(MasID, Prof, Student, TID));

  for (question(QID, Question)) {
    .print("Challenge ", QID, ": ", Question);
    .emitAll(challenge(MasID, Prof, Student, TID, QID, Question));
    for (student(MasID, Student)) {
      solution(MasID, QID, Solution);
      .emit(rubric(MasID, Prof, TA, TID, QID, Solution));
      .print("Solution for", MasID, QID, "is", Solution);
    };
  };
  .count(question(_, _), NumChallenges);
  .emitAll(end_test(MasID, Prof, Student, TID, NumChallenges, "done"));
  .print("Sent end marker with ", NumChallenges, " questions").

+result(MasID, TA, Prof, TID, QID, Ans, Sol, Grade) <-
  .print("Received result for", MasID, QID, "with grade", Grade);
  .count(result(MasID,_,_,TID,_,_,_,_), C);
  .count(challenge(MasID,_,_,TID,_,_), Challenges);
  if (C >= Challenges | (resign(MasID,Student,Prof,TID,NumResponses,Finished) & C >= NumResponses)) {
    !report(MasID, TID);
  }.


+resign(MasID, Student, Prof, TID, NumResponses, Finished) <-
  .print("Student ", Student, " has resigned after ", NumResponses, " responses");
  .count(result(MasID,_,_,TID,_,_,_,_), C);
  if (C >= NumResponses) {
    !report(MasID, TID);
  }.

+!report(MasID, TID) : not reported(MasID, TID) <-
  .findall(Grade, result(MasID,_,_,TID,_,_,_,Grade), L);
  !sum(L, Total);
  .count(challenge(MasID,_,_,TID,_,_), C);
  .print("Total grade for student", MasID, "is", Total, "/", C);
  +reported(MasID, TID).
+!report(MasID, TID) <- true.

+!sum([],0).
+!sum([T|R],M) <-
  !sum(R,S);
  M = T+S.
