// Patient agent

!get_treatment(1,cough).
!get_treatment(2,"sore throat").
//!get_treatment(sneeze).

+!get_treatment(Symptom) <-
  .uuid(Id);
  !get_treatment(Id, Symptom).

+!get_treatment(Id, Symptom) <-
     .print("Complaining about",Symptom);
     .emit("Complaint", [Id, Symptom]). // sends to doctor, declares +complaint(Id,Symptom)

+filled_rx(Id,Symptom,Medicine)
   <- .print("Received filled prescription (",Medicine,") for",Symptom).

+reassurance(Id,Symptom)
   <- .print("Received reassurance for",Symptom).

+complaint(Id, Symptom) <-
  .print("This event was triggered implicitly by emit",Id,Symptom).
