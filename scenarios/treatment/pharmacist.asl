// Pharmacist agent


+!filled_rx(Id,"Azithromycin",Done) <-
    .print("Rejecting prescription for Azithromycin").

+!filled_rx(Id,Rx,Done) <-
    .print("Filling prescription ",Rx);
    Done = "ok".
