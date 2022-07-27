+challenge(Prof, Student, SID, QID, Question) <-
  !answer(Question, Answer);
  .emit(response(Student, TA, SID, QID, Question, Answer)).

+!answer("What is your name?", "Sir Lancelot of Camelot").
+!answer("What is your quest?", "To seek the Holy Grail").
+!answer("What is your favorite color?", "Blue").
+!answer(_, "I don't know that").
