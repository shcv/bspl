+!response(Student, TA, SID, QID, Question, Answer) <-
  !answer(Question, Answer).

+!answer("What is your name?", "Sir Galahad of Camelot").
+!answer("What is your quest?", "To seek the Grail").
+!answer("What is your favorite color?", "Blue").
+!answer(_, "I don't know that").
