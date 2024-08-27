+schedule(MasID, Patient, Collector, ID, Contact, CoLocation)
  <- OrderQuery = "GET order";
     .emit(order_query(MasID, Collector, Provider, ID, CoLocation, OrderQuery)).

+non_provider_collect(MasID, Provider, Collector, ID, Order, Collection, CoLocation)
  <- Specimen = "Specimen 0001";
     .emit(collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)).

+order_response(MasID, Provider, Collector, ID, OrderQuery, Order, OrderResponse)
  : schedule(MasID, Patient, Collector, ID, Contact, CoLocation)
  <- !send_collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation).

+!send_collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation)
  <- Specimen = "Specimen 0002";
     .emit(collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)).
