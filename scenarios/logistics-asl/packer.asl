// Handle wrapped item
+wrapped(System, Wrapper, Packer, OrderID, ItemID, Item, Wrapping)
  : labeled(System, Labeler, Packer, OrderID, Address, Label)
  <- !send_packed(System, Packer, "Merchant", OrderID, ItemID, Item, Wrapping, Label).

// Handle labeled item
+labeled(System, Labeler, Packer, OrderID, Address, Label)
  : wrapped(System, Wrapper, Packer, OrderID, ItemID, Item, Wrapping)
  <- !send_packed(System, Packer, "Merchant", OrderID, ItemID, Item, Wrapping, Label).

// Send packed item
+!send_packed(System, Packer, Merchant, OrderID, ItemID, Item, Wrapping, Label)
  <- // Generate status based on wrapping and label
     if (Wrapping == "box" & Label == "UK-LANCS-001") {
       Status = "ready for UK shipping"
     } else {
       if (Wrapping == "box" & Label == "US-NCSU-001") {
         Status = "ready for US shipping"
       } else {
         Status = "ready for shipping"
       }
     };
     .print("Packer: Item ", Item, " from order ", OrderID, " is ", Status);
     .emit(packed(System, Packer, Merchant, OrderID, ItemID, Item, Wrapping, Label, Status)).

