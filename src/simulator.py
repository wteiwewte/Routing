#!/usr/bin/env python3
# vim:ts=4:sts=4:sw=4:expandtab

import json
import logging
import random
import uuid
from collections import deque

###
#
# Interfaces
#
###
class Packet:
    """Abstract packet class"""
    def __init__(self, src, dst):
        self._id  = uuid.uuid4()
        self._src = src
        self._dst = dst
    @property
    def id(self):
        """Returns globally unique id of the packet"""
        return self._id
    @property
    def src(self):
        """Returns address of the source router"""
        return self._src
    @property
    def dst(self):
        """Returns address of the destination router"""
        return self._dst

class MetaPacket(Packet):
    """Packet for routing algorithm communication"""
    def __init__(self, src, dst, payload):
        super().__init__(src, dst)
        self._payload = json.dumps(payload)
    @property
    def payload(self):
        return json.loads(self._payload)

class Link:
    """Abstract inter-router link class"""
    def __init__(self, dst):
        self._dst = dst
    @property
    def dst(self):
        """Returns address of the destination router"""
        return self._dst

class Router:
    """Abstract router class"""
    @property
    def id(self):
        """Returns address of the router"""
        pass
    @property
    def links(self):
        """Returns a list of links available at the router"""
        pass
    @property
    def stored_packets(self):
        """Returns a list of packets stored in the memory of the router"""
        pass
    def drop_packet(self, packet):
        """Drops a packet"""
        pass
    def store_packet(self, packet):
        """Stores a packet in the memory of the router"""
        pass
    def forward_packet(self, link, packet):
        """Forwards a packet over a link"""
        pass

class RoutingAlgorithm:
    """Abstract routing algorithm class"""
    def __init__(self, router):
        if not isinstance(router, Router):
            raise ValueError
        self.router = router
    def __call__(self, packets):
        if not isinstance(packets, list):
            raise ValueError
        for src, packet in packets:
            if not isinstance(packet, Packet):
                raise ValueError
            if src is not None and not isinstance(src, Link):
                raise ValueError
        self.route(packets)
    def add_link(self, link):
        """Called when new link is added to router"""
        pass
    def del_link(self, link):
        """Called when a link is removed from router"""
        pass
    def route(self, packets):
        """Called in every round of routing algorithm"""
        pass

###
#
# Simulation engine
#
###
class Simulator:
    """Simulator sandbox for routing algorithm experiments"""
    class SimPacket(Packet):
        def __init__(self, src, dst, start_time):
            super().__init__(src, dst)
            self.start_time = start_time
            self.stop_time = None

    class SimLink(Link):
        def __init__(self, dst):
            super().__init__(dst)
            self.packet = None

        def forward_packet(self, packet):
            if self.packet is not None:
                raise RuntimeError
            if not isinstance(packet, Packet):
                raise ValueError
            self.packet = packet

    class SimRouter(Router):
        def __init__(self, algorithm_class, id=None):
            if not issubclass(algorithm_class, RoutingAlgorithm):
                raise ValueError
            super().__init__()
            self._id = id or uuid.uuid4()
            self._links = dict()
            self.store = dict()
            self.packets = dict()
            self.algorithm = algorithm_class(self)

        @property
        def id(self):
            return self._id
        @property
        def links(self):
            return list(self._links.values())
        @property
        def stored_packets(self):
            return list(self.store.values())

        def drop_packet(self, packet):
            if not isinstance(packet, Packet):
                raise ValueError
            if packet.id in self.store:
                del self.store[packet.id]
            if packet.id in self.packets:
                del self.packets[packet.id]
            logging.info("Droped packet [{}] {} -> {}".format(packet.id, packet.src, packet.dst))

        def store_packet(self, packet):
            if not isinstance(packet, Packet):
                raise ValueError
            self.store[packet.id] = packet
            if packet.id in self.packets:
                del self.packets[packet.id]

        def forward_packet(self, link, packet):
            if not isinstance(link, Simulator.SimLink):
                raise ValueError
            if not isinstance(packet, Packet):
                raise ValueError
            if link not in self.links:
                raise ValueError
            if isinstance(packet, Simulator.SimPacket):
                if packet.id not in self.store and packet.id not in self.packets:
                    raise ValueError
            link.forward_packet(packet)
            if packet.id in self.store:
                del self.store[packet.id]
            if packet.id in self.packets:
                del self.packets[packet.id]

    def __init__(self):
        self.routers = dict()
        self.links = set()
        self.time = 0
        self.routable_packets = 0
        self.routed_packets = list()

    @property
    def stats(self):
        response = dict()
        response['packets'] = self.routable_packets
        if self.routable_packets > 0:
            response['delivery_rate'] = len(self.routed_packets) / self.routable_packets
        response['routed'] = len(self.routed_packets)
        if len(self.routed_packets) > 0:
            response['avg_time'] = sum( [p.stop_time - p.start_time for p in self.routed_packets] ) / len(self.routed_packets)
        return response

    def add_router(self, algorithm_class, id=None):
        if id in self.routers:
            raise ValueError
        r = Simulator.SimRouter(algorithm_class, id)
        self.routers[r.id] = r
        return r

    def add_link(self, r1, r2):
        if isinstance(r1, Router):
            r1 = r1.id
        if isinstance(r2, Router):
            r2 = r2.id
        if r1 not in self.routers or r2 not in self.routers:
            raise ValueError
        r1, r2 = (min(r1,r2), max(r1,r2))
        if r1 != r2 and (r1,r2) not in self.links:
            self.links.add( (r1,r2) )
            self.routers[r1]._links[r2] = Simulator.SimLink(r2)
            self.routers[r1].algorithm.add_link(self.routers[r1]._links[r2])
            self.routers[r2]._links[r1] = Simulator.SimLink(r1)
            self.routers[r2].algorithm.add_link(self.routers[r2]._links[r1])

    def del_link(self, r1, r2):
        if isinstance(r1, Router):
            r1 = r1.id
        if isinstance(r2, Router):
            r2 = r2.id
        if r1 not in self.routers or r2 not in self.routers:
            raise ValueError
        r1, r2 = (min(r1,r2), max(r1,r2))
        if (r1,r2) in self.links:
            self.links.remove( (r1,r2) )
            self.routers[r1].algorithm.del_link(self.routers[r1]._links[r2])
            del self.routers[r1]._links[r2]
            self.routers[r2].algorithm.del_link(self.routers[r2]._links[r1])
            del self.routers[r2]._links[r1]

    def add_packet(self, r1, r2):
        if isinstance(r1, Router):
            r1 = r1.id
        if isinstance(r2, Router):
            r2 = r2.id
        if r1 in self.routers:
            if r2 in self.routers:
                self.routable_packets += 1
            router = self.routers[r1]
            packet = Simulator.SimPacket(r1, r2, self.time)
            router.packets[packet.id] = (None, packet)
            return packet

    def route(self):
        self.time += 1
        for id, router in self.routers.items():
            router.algorithm(list(router.packets.values()))
            for src, packet in router.packets.values():
                if packet.dst != router.id:
                    logging.warning("Silently droped packet [{}] {} -> {} at {}".format(packet.id, packet.src, packet.dst, router.id))
            router.packets = dict()
        for id, router in self.routers.items():
            for link in router.links:
                if link.packet is not None:
                    packet = link.packet
                    link.packet = None
                    if link.dst in self.routers:
                        if isinstance(packet, Simulator.SimPacket) and packet.dst == link.dst:
                            packet.stop_time = self.time
                            self.routed_packets.append(packet)
                            logging.info("Routed packet [{}] {} -> {} in {} steps".format(packet.id, packet.src, packet.dst, packet.stop_time - packet.start_time))
                        else:
                            logging.debug("Forwarded packet [{}] {} -> {} to {}".format(packet.id, packet.src, packet.dst, link.dst))
                            self.routers[link.dst].packets[packet.id] = (self.routers[link.dst]._links[router.id], packet)

###
#
# Routing algorithms
#
###
class RandomRouter(RoutingAlgorithm):
    """Routing algorithm that forwards packets in random directions"""
    def route(self, packets):
        for src, packet in packets:
            self.router.store_packet(packet)
        packets = self.router.stored_packets
        random.shuffle(packets)
        links = self.router.links
        random.shuffle(links)
        for link in links:
            if len(packets) > 0:
                self.router.forward_packet(link, packets[-1])
                packets = packets[0:-1]

class ShortPathRouter(RoutingAlgorithm):
    """Distance vector type routing algorithm"""
    def __init__(self, router):
        super().__init__(router)
        self.tick = 0
        self._distance_vector = dict()

    @property
    def distance_vector(self):
        return self._distance_vector

    def route(self, packets):
        for src, packet in packets:
            if isinstance(packet, MetaPacket):
                logging.debug('Router {} received vector {} from {}'.format(self.router.id, packet.payload, src.dst))
                #HANDLE distance vector from neighbor
                for router_id, info in packet.payload.items():
                    if router_id == self.router.id:
                        continue
                    if router_id not in self.distance_vector.keys():
                        if info[0] > 0 :
                            self.distance_vector[router_id] = [info[0] + 1, self.tick, src.dst]
                    else:
                        """if information is up-to-date"""
                        if info[1] >= self.distance_vector[router_id][1]:
                            if self.distance_vector[router_id][0] < 0:
                                if info[0] > 0:
                                    self.distance_vector[router_id] = info
                            else:
                                if info[0] < 0:
                                    if self.distance_vector[router_id][2] == src.dst:
                                        self.distance_vector[router_id] = [info[0], self.tick, src.dst]
                                else:
                                    if info[0] + 1 < self.distance_vector[router_id][0]:
                                        self.distance_vector[router_id] = [info[0] + 1, self.tick, src.dst]

            else:
                self.router.store_packet(packet)
        if self.tick % 5 == 0:
            #SEND my distance vector to neighbors every 5-th round
            for link in self.router.links:
                if link.dst not in self.distance_vector.keys():
                    self.distance_vector[link.dst] = [1, self.tick, self.router.id]

            for router_id, info in self.distance_vector.items():
                info[1] = self.tick


            logging.debug('Router {} sending vector {} to neighbors'.format(self.router.id, self.distance_vector))
            for link in self.router.links:
                self.router.forward_packet(link, MetaPacket(self.router.id, link.dst, self.distance_vector))
        else:
            #print(self.router.id)
            for link in self.router.links:
                for packet in self.router.stored_packets:
                    if packet.dst in self.distance_vector.keys():
                        if self.distance_vector[packet.dst][0] < 0:
                            continue
                        if self.distance_vector[packet.dst][2] == self.router.id:
                            if link.dst == packet.dst:
                                self.router.forward_packet(link, packet)
                                break
                        elif link.dst == self.distance_vector[packet.dst][2]:
                                self.router.forward_packet(link, packet)
                                break

            # FORWARD stored packets using distance_vector
        self.tick += 1

    def add_link(self, link):
        for router_id, info in self.distance_vector.items():
            if info[2] == link.dst:
                if info[0] < 0:
                    info[0] = -info[0]
                info[1] = self.tick

    def del_link(self, link):
        """setting -1 in our distance vector on deleted link"""
        for router_id, info in self.distance_vector.items():
            if info[2] == link.dst:
                if info[0] > 0:
                    info[0] = -info[0]
                info[1] = self.tick

class whole_graph_router(RoutingAlgorithm):
    def __init__(self, router):
        super().__init__(router)
        self.tick = 0
        self._graph = dict()
        self._graph[self.router.id] = dict()
        self.used_links = set()
        self.predecessors = dict()

    @property
    def graph(self):
        return self._graph

    def forward_through_link(self, dst_, packet):
        """helper function to find link to forward packet through dst_"""
        for link in self.router.links:
            if link.dst == dst_:
                if link.dst not in self.used_links:
                    self.router.forward_packet(link, packet)
                    self.used_links.add(link.dst)
                    break

    def route(self, packets):
        for src, packet in packets:
            if isinstance(packet, MetaPacket):
                logging.debug('Router {} received graph {} from {}'.format(self.router.id, packet.payload, src.dst))
                """handling graph from neighbors"""
                for router_id, router_dict in packet.payload.items():
                    if router_id not in self.graph.keys():
                        self.graph[router_id] = dict()
                    for link_dst, edge in router_dict.items():
                        if link_dst in self.graph[router_id].keys():
                            """if information is up-to-date"""
                            if edge[1] >= self.graph[router_id][link_dst][1]:
                                self.graph[router_id][link_dst] = edge
                        else:
                            self.graph[router_id][link_dst] = edge
            else:
                self.router.store_packet(packet)
        if self.tick % 5 == 0:
            #SEND my graph to neighbors every 5-th round
            for link in self.router.links:
                self.graph[self.router.id][link.dst] = (True, self.tick)

            logging.debug('Router {} sending graph {} to neighbors'.format(self.router.id, self.graph))
            for link in self.router.links:
                self.router.forward_packet(link, MetaPacket(self.router.id, link.dst, self.graph))
        else:
            """BFS to search best paths for our packets"""
            self.used_links.clear()
            for packet in self.router.stored_packets:
                self.predecessors.clear()
                self.predecessors[self.router.id] = "NONE"
                q = deque()
                visited = dict()
                current = None
                got_destination = False
                for x, y in self.graph[self.router.id].items():
                    if y[0]:
                        q.append(x)
                        self.predecessors[x] = self.router.id
                while len(q) > 0:
                    current = q.popleft()
                    if current in visited:
                        continue
                    visited[current] = True
                    if current == packet.dst:
                        got_destination = True
                        break
                    if current not in self.graph.keys():
                        continue
                    for x, y in self.graph[current].items():
                        if x in visited and visited[x] is True:
                            continue
                        if y[0] and x != self.router.id:
                            q.append(x)
                            self.predecessors[x] = current
                if got_destination:
                    v = packet.dst
                    while True:
                        if v not in self.graph.keys():
                            break
                        if self.predecessors[v] == self.router.id:
                            self.forward_through_link(v, packet)
                            break
                        v = self.predecessors[v]

        self.tick += 1

    def add_link(self, link):
        self.graph[self.router.id][link.dst] = (True, self.tick)

    def del_link(self, link):
        self.graph[self.router.id][link.dst] = (False, self.tick)

###
#
# Simulation scenario
#
###
logging.basicConfig(level=logging.DEBUG)
sim = Simulator()
algo = whole_graph_router

r1 = sim.add_router(algo, 'p.a')
r2 = sim.add_router(algo, 'p.b')
r3 = sim.add_router(algo, 'p.c')
r4 = sim.add_router(algo, 'p.d')
r5 = sim.add_router(algo, 'p.e')
r6 = sim.add_router(algo, 'p.f')
r7 = sim.add_router(algo, 'p.g')

q1 = sim.add_router(algo, 'q.a')
q2 = sim.add_router(algo, 'q.b')
q3 = sim.add_router(algo, 'q.c')
q4 = sim.add_router(algo, 'q.d')
q5 = sim.add_router(algo, 'q.e')
q6 = sim.add_router(algo, 'q.f')
q7 = sim.add_router(algo, 'q.g')

sim.add_link(r1, r2)
sim.add_link(r2, r3)
sim.add_link(r3, r4)
sim.add_link(r4, r5)
sim.add_link(r5, r6)
sim.add_link(r6, r7)
sim.add_link(r7, r1)

sim.add_link(q1, q2)
sim.add_link(q2, q3)
sim.add_link(q3, q4)
sim.add_link(q4, q5)
sim.add_link(q5, q6)
sim.add_link(q6, q7)
sim.add_link(q7, q1)

sim.add_link(r4, q4)

sim.add_packet(r1, q7)
for i in range(50):
    sim.route()
    if( i == 7 ) :
        sim.add_link(r1, q5)

print(sim.stats)
