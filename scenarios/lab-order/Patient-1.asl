!send_complain.
+!send_complain
  <- MAS = "main";
     ID = 1;
     Complaint = "My toe hurts.";
     .print("Complaining: ", Complaint);
     .emit(complain(MAS, Patient, Provider, ID, Complaint)).

+need_appointment(MasID, Provider, Patient, ID, Order, Collection, Contact)
  <- CoLocation = "lab 4";
     .emit(schedule(MasID, Patient, Collector, ID, Contact, CoLocation, Specimen)).

+all_received(MasID, Provider, Patient, ID, Results, Report)
  <- .print(Report).
