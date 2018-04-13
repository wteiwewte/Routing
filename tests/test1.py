import simulator
import logging

"""dwa cykle p i q, wysyłamy pakiety od jednego do drugiego bez usuwania krawędzi"""

logging.basicConfig(level=logging.DEBUG)
sim = simulator.Simulator()
algo = simulator.whole_graph_router
r1 = sim.add_router(algo, 'a')
r2 = sim.add_router(algo, 'b')
r3 = sim.add_router(algo, 'c')
r4 = sim.add_router(algo, 'd')
r5 = sim.add_router(algo, 'e')
r6 = sim.add_router(algo, 'f')
r7 = sim.add_router(algo, 'g')
sim.add_link(r1, r2)
sim.add_link(r2, r3)
sim.add_link(r3, r4)
sim.add_link(r4, r5)
sim.add_link(r5, r6)
sim.add_link(r6, r7)
sim.add_link(r7, r1)

q1 = sim.add_router(algo, 'q.a')
q2 = sim.add_router(algo, 'q.b')
q3 = sim.add_router(algo, 'q.c')
q4 = sim.add_router(algo, 'q.d')
q5 = sim.add_router(algo, 'q.e')
q6 = sim.add_router(algo, 'q.f')
q7 = sim.add_router(algo, 'q.g')
sim.add_link(q1, q2)
sim.add_link(q2, q3)
sim.add_link(q3, q4)
sim.add_link(q4, q5)
sim.add_link(q5, q6)
sim.add_link(q6, q7)
sim.add_link(q7, q1)

sim.add_packet(r1, r7)
sim.add_link(r1,q6)
sim.add_link(q3,r7)
for i in range(200):
    if i % 2 == 0:
        sim.add_packet(r1, q5)
    elif i % 3 == 2:
        sim.add_packet(q3, r7)
    else:
        sim.add_packet(r5, r6)
    sim.route()
print(sim.stats)
