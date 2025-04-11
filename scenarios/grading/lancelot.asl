answer("What is your name?", "Sir Lancelot of Camelot").
answer("What is your quest?", "To seek the Holy Grail").
answer("What is your favorite color?", "Blue").

+begin_test(MasID, Prof, Student, TID) <-
  .print("Starting test with TID", TID).

+challenge(MasID, Prof, Student, TID, QID, Question) : answer(Question,Answer) <-
  .print("Answering", QID, "with", Answer);
  .emit(response(MasID, Student, Ta, TID, QID, Question, Answer)).
