+challenge(MasID, Prof, Student, SID, QID, Question)
  <- !answer(Question, Answer);
     .emit(response(MasID, Student, Ta, SID, QID, Question, Answer)).

+!answer("What is your name?", "Sir Galahad of Camelot").
+!answer("What is your quest?", "To seek the Grail").
+!answer("What is your favorite color?", "Blue").
+!answer(_, "I don't know that").
