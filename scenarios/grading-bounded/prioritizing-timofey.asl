student("s1", 3). // ID, year
student("s2", 4).

reverse([],Z,Z) :- true.
reverse([H|T],Z,Acc) :- reverse(T,Z,[H|Acc]).

+response(MasID, Student, TA, SID, QID, Question, Answer)
  : rubric(MasID, Prof, TA, SID, QID, Solution) <-
  +task(MasID, SID, QID, Answer, Solution).

+rubric(MasID, Prof, TA, SID, QID, Solution)
  : response(MasID, Student, TA, SID, QID, Question, Answer) <-
  +task(MasID, SID, QID, Answer, Solution).

+task(MasID, SID, QID, Answer, Solution)
  : .count(task(_,_,_,_,_), C) & C = 6
  <- !prioritize(P);
  !work(P).

+!work(P) <-
  for(.member([Year, SID, QID], P)) {
    task(MasID, SID, QID, Ans, Sol);
    !grade(MasID, SID, QID, Ans, Sol);
  }.

+!map_year([[SID, QID] | []], P) : student(SID, Year) <-
  P = [[Year, SID, QID]].
+!map_year([[SID, QID]|T], P) : student(SID, Year) <-
  !map_year(T, P2);
  P = [[Year, SID, QID] | P2].

+!prioritize(P) <-
  .findall([SID, QID], task(MasID,SID,QID,Ans,Sol), L);
  !map_year(L, L2);
  .sort(L2, L3);
  reverse(L3, P, []).

+!grade(MasID, SID, QID, Answer, Solution) <-
  if (Answer == Solution) {
    .print(SID,QID,Answer,"matches",Solution);
    Grade = 1;
  } else {
    .print(SID,QID,Answer,"does not match",Solution);
    Grade = 0;
  }
  .print("Grade: ",Grade);
  .emit(result(MasID, TA, Prof, SID, QID, Answer, Solution, Grade)).
