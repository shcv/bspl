name("Sir Lancelot of Camelot").
quest("To seek the Holy Grail").
color("Blue").

+!response(Student, TA, SID, QID, Question, Answer) <-
  !answer(Question, Answer).

+!answer("What is your name?", Answer) <-
  name(Answer).

+!answer("What is your quest?", Answer) <-
  quest(Answer).

+!answer("What is your favorite color?", Answer) <-
  color(Answer).

+!answer(_, Answer) <-
  Answer = "I don't know that".
