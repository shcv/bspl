// Initial beliefs
order_id(0).
item_id(0).
next_address("Lancaster University").
next_item("ball").

// Generate orders periodically
+!generate_orders
  : order_id(OrderID) & OrderID < 10
  <- !send_request_label;
     !send_request_wrapping;
     .wait(1000);  // Wait 1 second
     -+order_id(OrderID + 1);
     !generate_orders.
+!generate_orders
  <- .print("Merchant: Finished generating all orders.").

// Send a request for a label
+!send_request_label
  : order_id(OrderID) & next_address(Address)
  <- .print("Merchant: Requesting label for order ", OrderID, " to ", Address);
     .emit(request_label("logistics", "Merchant", "Labeler", OrderID, Address));
     // Toggle between addresses
     if (Address == "Lancaster University") {
       -+next_address("NCSU")
     } else {
       -+next_address("Lancaster University")
     }.

// Send a request for wrapping
+!send_request_wrapping
  : order_id(OrderID) & item_id(ItemID) & ItemID < 2 & next_item(Item)
  <- .print("Merchant: Requesting wrapping for order ", OrderID, " item ", ItemID, " (", Item, ")");
     .emit(request_wrapping("logistics", "Merchant", "Wrapper", OrderID, ItemID, Item));
     -+item_id(ItemID + 1);
     // Cycle through items
     if (Item == "ball") {
       -+next_item("bat")
     } else {
       if (Item == "bat") {
         -+next_item("plate")
       } else {
         if (Item == "plate") {
           -+next_item("glass")
         } else {
           -+next_item("ball")
         }
       }
     }.

// Reset item counter for new order
+order_id(OrderID)
  <- -+item_id(0).

// Handle packed items
+packed(System, Packer, "Merchant", OrderID, ItemID, Item, Wrapping, Label, Status)
  <- .print("Merchant: Received order ", OrderID, " item ", ItemID, " (", Item, ") - ", Status).

// Start generating orders when the agent starts
!generate_orders.

