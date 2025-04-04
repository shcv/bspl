+begin_test(MasID, Prof, Student, TID) <-
  .print("Starting test with TID", TID);
  +active_test(TID).

+challenge(MasID, Prof, Student, TID, QID, Question) : active_test(TID) & answer(Question, Answer) <-
  .print("Answering", QID, "with", Answer);
  +answered(TID, QID);
  .emit(response(MasID, Student, Ta, TID, QID, Question, Answer)).

+end_test(MasID, Prof, Student, TID, NumChallenges, Done) : active_test(TID) <-
  .print("Received end marker with", NumChallenges, "challenges");
  .count(answered(TID,_), NumAnswered);
  if (NumAnswered < NumChallenges) {
    .print("Resigning after answering", NumAnswered, "questions out of", NumChallenges);
    .emit(resign(MasID, Student, Prof, TID, NumAnswered, "finished"));
  };
  -active_test(TID).

+!answer("What is your name?", "Sir Lancelot of Camelot").
+!answer("What is your quest?", "To seek the Holy Grail").
// +!answer("What is your favorite color?", "Blue").
// +!answer(_, "I don't know that").
