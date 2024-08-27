+complain(MasID, Patient, Provider, ID, Complaint)
  <- // insert code to compute EnterRequest out parameters ['order'] here
     .emit(enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)).

+enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  <- // insert code to compute Ship out parameters ['collection', 'specimen'] here
     .emit(ship(MasID, Provider, Laboratory, ID, Order, Collection, Specimen)).

+enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  <- // insert code to compute NonProviderCollect out parameters ['co-location', 'collection'] here
     .emit(non_provider_collect(MasID, Provider, Collector, ID, Order, Collection, CoLocation)).

+enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  <- // insert code to compute NeedAppointment out parameters ['collection', 'contact'] here
     .emit(need_appointment(MasID, Provider, Patient, ID, Order, Collection, Contact)).

+enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  : order_query(MasID, Collector, Provider, ID, CoLocation, OrderQuery)
  <- !send_order_response(MasID, Provider, Collector, ID, OrderQuery, Order).

+order_query(MasID, Collector, Provider, ID, CoLocation, OrderQuery)
  : enter_request(MasID, Provider, Laboratory, ID, Complaint, Order)
  <- !send_order_response(MasID, Provider, Collector, ID, OrderQuery, Order).

+!send_order_response(MasID, Provider, Collector, ID, OrderQuery, Order)
  <- // insert code to compute OrderResponse out parameters ['order-response'] here
     .emit(order_response(MasID, Provider, Collector, ID, OrderQuery, Order, OrderResponse)).

+results_available(MasID, Laboratory, Provider, ID, Order, Specimen, ResultsId)
  <- // insert code to compute Query out parameters ['query'] here
     .emit(query(MasID, Provider, Laboratory, ID, ResultsId, Query)).

+results(MasID, Laboratory, Provider, ID, Order, Specimen, Results)
  <- // insert code to compute AllReceived out parameters ['report'] here
     .emit(all_received(MasID, Provider, Patient, ID, Results, Report)).

+send_results(MasID, Laboratory, Provider, ID, ResultsId, Query, Results)
  <- // insert code to compute AllReceived out parameters ['report'] here
     .emit(all_received(MasID, Provider, Patient, ID, Results, Report)).

