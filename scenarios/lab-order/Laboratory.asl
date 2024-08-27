+collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)
  <- // insert code to compute NotifyUnsuitable out parameters ['unsuitable'] here
     .emit(notify_unsuitable(MasID, Laboratory, Collector, ID, Order, Specimen, Unsuitable)).

+ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen)
  <- // insert code to compute NotifyUnsuitable out parameters ['unsuitable'] here
     .emit(notify_unsuitable(MasID, Laboratory, Collector, ID, Order, Specimen, Unsuitable)).

+collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)
  <- // insert code to compute NotifyReceived out parameters ['received'] here
     .emit(notify_received(MasID, Laboratory, Collector, ID, Order, Specimen, Received)).

+ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen)
  <- // insert code to compute NotifyReceived out parameters ['received'] here
     .emit(notify_received(MasID, Laboratory, Collector, ID, Order, Specimen, Received)).

+collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)
  <- // insert code to compute Results out parameters ['results'] here
     .emit(results(MasID, Laboratory, Provider, ID, Order, Specimen, Results)).

+ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen)
  <- // insert code to compute Results out parameters ['results'] here
     .emit(results(MasID, Laboratory, Provider, ID, Order, Specimen, Results)).

+collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)
  <- // insert code to compute ResultsAvailable out parameters ['results-id'] here
     .emit(results_available(MasID, Laboratory, Provider, ID, Order, Specimen, ResultsId)).

+ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen)
  <- // insert code to compute ResultsAvailable out parameters ['results-id'] here
     .emit(results_available(MasID, Laboratory, Provider, ID, Order, Specimen, ResultsId)).

+query(MasID, Provider, Laboratory, ID, ResultsId, Query)
  <- // insert code to compute SendResults out parameters ['results'] here
     .emit(send_results(MasID, Laboratory, Provider, ID, ResultsId, Query, Results)).

