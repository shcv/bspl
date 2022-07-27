question(1, "What is your name?").
solution(1, 1, "Sir Lancelot of Camelot").
solution(2, 1, "Sir Galahad of Camelot").
question(2, "What is your quest?").
solution(1, 2, "To seek the Holy Grail").
solution(2, 2, "To seek the Grail").
question(3, "What is your favorite color?").
solution(1, 3, "Blue").
solution(2, 3, "Yellow").

student(1, "0.0.0.0:8010"). // Lancelot
student(2, "0.0.0.0:8011"). // Galahad

!start.

+!start <-
  for (student(SID, Student)) {
    .emit(begin_test("Pnin", Student, SID));
    for (question(QID, Q)) {
      .emit(challenge("Pnin", Student, SID, QID, Q));
      .print("Asking", Student, SID, QID, Q);

      solution(SID, QID, Solution);
      .emit(rubric(Prof, TA, SID, QID, Solution));
      .print("Solution for",SID,QID,"is",Solution);
    };
  }.

+result(TA, Prof, SID, QID, Ans, Sol, _) <-
  .count(result(_,_,SID,_,_,_,Grade), C);
  if (C = 3) {
    !report(SID);
  }.

+!report(SID) : not reported(SID) <-
  .findall(Grade, result(_,_,SID,_,_,_,Grade), L);
  !sum(L, Total);
  .length(L, C);
  .print("Total grade for student",SID,"is",Total,"/",C);
  +reported(SID).
+!report(SID) <- true.

+!sum([],0).
+!sum([T|R],M) <-
  !sum(R,S);
  M = T+S.
