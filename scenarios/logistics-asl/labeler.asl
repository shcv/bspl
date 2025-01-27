// Handle request for label
+request_label(System, Merchant, Labeler, OrderID, Address)
  <- // Generate label based on address
     if (Address == "Lancaster University") {
       Label = "UK-LANCS-001"
     } else {
       Label = "US-NCSU-001"
     };
     .print("Labeler: Generated label ", Label, " for order ", OrderID);
     .emit(labeled(System, Labeler, "Packer", OrderID, Address, Label)).

