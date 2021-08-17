// Doctor agent

treatment("ICD10:R05", "Cheratussin AC").
treatment("ICD10:J02.9","Azithromycin").

+!prescription(ID, Symptom, Rx) <-
    !diagnose(ID, Symptom, ICD);
    treatment(ICD, Rx);
    .print("Treatment for",Symptom,"is",Rx).

+!diagnose(ID, "cough", ICD) <-
    ICD = "ICD10:R05".

+!diagnose(ID, "sore throat", ICD) <- // acute pharyngitis
    ICD = "ICD10:J02.9".

+!reassurance(CID, "sneeze", Comment) <-
    Comment = "Hang in there.".

+complaint(ID, Symptom) <-
  .print("Observed complaint:",ID,Symptom).
