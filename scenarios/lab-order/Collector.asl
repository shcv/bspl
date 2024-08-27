+schedule(MasID, Patient, Collector, ID, Contact, CoLocation)
  <- // insert code to compute OrderQuery out parameters ['order-query'] here
     .emit(order_query(MasID, Collector, Provider, ID, CoLocation, OrderQuery)).

+schedule(MasID, Patient, Collector, ID, Contact, CoLocation)
  : order_response(MasID, Provider, Collector, ID, OrderQuery, Order, OrderResponse)
  <- !send_collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation).

+order_response(MasID, Provider, Collector, ID, OrderQuery, Order, OrderResponse)
  : schedule(MasID, Patient, Collector, ID, Contact, CoLocation)
  <- !send_collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation).

+!send_collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation)
  <- // insert code to compute CollectSpecimen out parameters ['specimen'] here
     .emit(collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)).

+non_provider_collect(MasID, Provider, Collector, ID, Order, Collection, CoLocation)
  <- // insert code to compute CollectSpecimen out parameters ['specimen'] here
     .emit(collect_specimen(MasID, Collector, Laboratory, ID, Order, CoLocation, Specimen)).

