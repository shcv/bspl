// Pharmacist agent

+!filled_rx(Id,Rx,Done) <-
    .print("Filling prescription ",Rx);
    Done = "ok".
