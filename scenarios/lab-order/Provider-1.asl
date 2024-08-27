+complain(MasID, Patient, Provider, ID, Complaint)
  <- Order = "Order 0001";
     .emit(enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)).

+enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  <- .randint(1,3,Method);
     if (Method == 1) {
       Collection = "provider";
       Specimen = "Specimen 0000";
       .emit(ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen));
     };
     if (Method == 2) {
       Collection = "non-provider";
       CoLocation = "on-site";
       .emit(non_provider_collect(MasID, Provider, Collector, ID, Order, Collection, CoLocation));
     };
     if (Method == 3) {
       Collection = "appointment";
       Contact = "Laboratory";
       .emit(need_appointment(MasID, Provider, Patient, ID, Order, Collection, Contact));
     }.

+order_query(MasID, Collector, Provider, ID, CoLocation, OrderQuery)
  : enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  <- OrderResponse = "responded";
     .emit(order_response(MasID, Provider, Collector, ID, OrderQuery, Order, OrderResponse)).

+results_available(MasID, Laboratory, Provider, ID, Order, Specimen, ResultsId)
  <- Query = "get results";
     .emit(query(MasID, Provider, Laboratory, ID, ResultsId, Query)).

+results(MasID, Laboratory, Provider, ID, Order, Specimen, Results)
  <- !report(MasID, Provider, Patient, ID, Results).

+send_results(MasID, Laboratory, Provider, ID, ResultsId, Query, Results)
  <- !report(MasID, Provider, Patient, ID, Results).

+!report(MasID, Provider, Patient, ID, Results)
  <- Report = "Negative";
     .emit(all_received(MasID, Provider, Patient, ID, Results, Report)).
