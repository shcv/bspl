+ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen)
  <- Received = "received";
     .emit(notify_received(MasID, Laboratory, Collector, ID, Order, Specimen, Received));
     .randint(1,10, Suitable);
     .print(Suitable);
     if (Suitable < 3) {
        // 30% chance shipped sample is unsuitable
        Unsuitable = "unsuitable";
       .emit(notify_unsuitable(MasID, Laboratory, Collector, ID, Order, Specimen, Unsuitable));
     } else {
       !handle_results(MasID, Laboratory, Collector, ID, Order, Specimen);
     }.

+collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)
  <- !handle_results(MasID, Laboratory, Collector, ID, Order, Specimen).

+!handle_results(MasID, Laboratory, Collector, ID, Order, Specimen)
  <- Results = "negative";
     +available_results(ID, Results);
     .randint(1,10, Decision);
     if (Decision <= 5) {
       .emit(results(MasID, Laboratory, Provider, ID, Order, Specimen, Results));
     } else {
       ResultsId = ID;
       .emit(results_available(MasID, Laboratory, Provider, ID, Order, Specimen, ResultsId));
     }.

+query(MasID, Provider, Laboratory, ID, ResultsId, Query)
  : available_results(ResultsId, Results)
  <- .emit(send_results(MasID, Laboratory, Provider, ID, ResultsId, Query, Results)).
