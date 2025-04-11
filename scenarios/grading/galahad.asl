+begin_test(MasID, Prof, Student, TID) <-
  .print("Starting test with TID", TID).

+challenge(MasID, Prof, Student, TID, QID, Question) <-
  !answer(Question, Answer);
  .print("Answering", QID, "with", Answer);
  .emit(response(MasID, Student, Ta, TID, QID, Question, Answer)).

+!answer("What is your name?", "Sir Galahad of Camelot").
+!answer("What is your quest?", "To seek the Grail").
+!answer("What is your favorite color?", "Blue").
+!answer(_, "I don't know that").
