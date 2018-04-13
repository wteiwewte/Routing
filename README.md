# Routing
Network routing algorithms

## Information

This project was made during Computer Networks course. 
Its goal was to implement two routing algorithms: one based on shortest paths, second based on keeping whole graph in each vertex.

## Description

ShortPathRouter - algorithm using distance vector implemented by dictionary (router_id : (distance, time, intercessory_router_id)) which
is actualized each time we received distance vector from neighbor. Information from other vectors are processed only when it is up-to-date. In case of deleted edge, we're changing our distance vector when that edge participated in shortest path.

Whole_graph_router - algorithm grounded on keeping whole graph in every vertex via list of lists.
When deletion of edge occures, only single bool is changed in proper lists.
Sending a packet takes place with BFS algorithm, using set - used_links and dictionary - predecessors which
inform in which direction send each packet.

### Tests

Project was tested by two tests - test1 and test2. Both operates on graph consisting of 2 cycles: p and q. In test2 we perform periodic
edge deletions. 
To run tests just type 'python test1.py' or 'python test2.py'.

# Note

The basis of source (classes: Packet, MetaPacket, Link, Router, RoutingAlgorithm, Simulator, RandomRouter) code was provided by my tutor.
