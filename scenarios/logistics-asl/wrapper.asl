// Handle request for wrapping
+request_wrapping(System, Merchant, Wrapper, OrderID, ItemID, Item)
  <- // Generate wrapping based on item
     if (Item == "ball") {
       Wrapping = "box"
     } else {
       if (Item == "bat") {
         Wrapping = "tube"
       } else {
         if (Item == "plate") {
           Wrapping = "bubble wrap"
         } else {
           Wrapping = "foam"
         }
       }
     };
     .print("Wrapper: Using ", Wrapping, " for item ", Item, " (Order ", OrderID, ")");
     .emit(wrapped(System, Wrapper, "Packer", OrderID, ItemID, Item, Wrapping)).

