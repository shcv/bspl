+!send_complain
  <- // insert code to compute Complain out parameters ['ID', 'complaint'] here
     .emit(complain(MasID, Patient, Provider, ID, Complaint)).

+need_appointment(MasID, Provider, Patient, ID, Order, Collection, Contact)
  <- // insert code to compute Schedule out parameters ['co-location'] here
     .emit(schedule(MasID, Patient, Collector, ID, Contact, CoLocation)).

