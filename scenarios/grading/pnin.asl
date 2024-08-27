question(q1, "What is your name?").
solution(s1, q1, "Sir Lancelot of Camelot").
solution(s2, q1, "Sir Galahad of Camelot").
question(q2, "What is your quest?").
solution(s1, q2, "To seek the Holy Grail").
solution(s2, q2, "To seek the Grail").
question(q3, "What is your favorite color?").
solution(s1, q3, "Blue").
solution(s2, q3, "Yellow").

student(s1, "lancelot", "Lancelot").
student(s2, "galahad", "Galahad").

!start.

+!start <-
  for (student(SID, MasID, Student)) {
    .emit(begin_test(MasID, Prof, Student, SID));
    for (question(QID, Question)) {
      .emit(challenge(MasID, Prof, Student, SID, QID, Question));
      .print("Challenging", Student, SID, QID, Question);

      solution(SID, QID, Solution);
      .emit(rubric(MasID, Prof, Ta, SID, QID, Solution));
      .print("Solution for",SID,QID,"is",Solution);
    };
  }.

+result(MasID, TA, Prof, SID, QID, Ans, Sol, _) <-
  .count(result(_,_,_,SID,_,_,_,Grade), C);
  if (C = 3) {
    !report(SID);
  }.

+!report(SID) : not reported(SID) <-
  .findall(Grade, result(_,_,_,SID,_,_,_,Grade), L);
  !sum(L, Total);
  .length(L, C);
  .print("Total grade for student",SID,"is",Total,"/",C);
  +reported(SID).
+!report(SID) <- true.

+!sum([],0).
+!sum([T|R],M) <-
  !sum(R,S);
  M = T+S.
