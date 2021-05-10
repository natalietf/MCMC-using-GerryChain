from gerrychain import MarkovChain
from gerrychain.constraints import (
Validator,
single_flip_contiguous,
within_percent_of_ideal_population,
UpperBound)
from gerrychain.proposals import propose_random_flip
from gerrychain.accept import always_accept
from gerrychain.updaters import Election, Tally, cut_edges
from gerrychain.partition import Partition
from gerrychain.proposals import recom
import random
import matplotlib.pyplot as plt
from functools import partial
import networkx as nx

k_partitions = 8
node_size = 30
grid_height = 40
grid_width = 60

graph = nx.grid_graph([grid_height, grid_width])
random_boundary = 0.50
P1 = "skyblue"
P2 = "navy"

for node in graph.nodes():
    graph.nodes[node]["population"] = 1
if random.random() < random_boundary:
    graph.nodes[node][P1] = 1
    graph.nodes[node][P2] = 0
else:
    graph.nodes[node][P1] = 0
    graph.nodes[node][P2] = 1
    
vote_dict = {1: P1, 0: P2}

def step_num(partition):
    parent = partition.parent
    if not parent:
        return 0
    return parent["step_num"] + 1

updaters = {
    "population": Tally("population"),
    "cut_edges": cut_edges,
    "step_num": step_num,
    "P1 vs P2": Election("P1 vs P2", {"P1": P1, "P2": P2}),}

part_dict = {x: int(x[0]/(grid_width/k_partitions))
             
for x in graph.nodes()}
    init_part = Partition(graph, assignment=part_dict, updaters=updaters)
    
def p1_wins(partition):
    if partition["P1 vs P2"].wins("P1")+partition["P1 vs P2"].wins("P2") > k_partitions:
        return equal_check(partition, "P1")
    else:
        return (partition["P1 vs P2"].wins("P1")/k_partitions)*100
    
def p2_wins(partition):
    if partition["P1 vs P2"].wins("P1")+partition["P1 vs P2"].wins("P2") > k_partitions:
        return equal_check(partition, "P2")
    else:
        return (partition["P1 vs P2"].wins("P2")/k_partitions)*100

def equal_check(partition, party):
    for number in range(1, k_partitions+1):
        if partition["P1 vs P2"].wins("P1")+partition["P1 vs P2"].wins("P2") == k_partitions + number:
            return ((partition["P1 vs P2"].wins(party)/k_partitions)*100)-((100/k_partitions)/2)*number
    raise error
    
ideal_population = sum(init_part["population"].values()) / len(init_part)
popbound = within_percent_of_ideal_population(init_part, 0.1)
cutedgebound = UpperBound(lambda part: len(part["cut_edges"]), 400)

flip_steps = 250000
flip_chain = MarkovChain(
propose_random_flip,
Validator([single_flip_contiguous, popbound, cutedgebound]), 
    accept = always_accept, 
    initial_state = init_part, 
    total_steps = flip_steps, )

flip_p1_seats = []
for part in flip_chain:
    flip_p1_seats.append(part["P1 vs P2"].wins("P1"))
plt.figure()
nx.draw(
graph,
pos = {x: x for x in graph.nodes()},
node_color = [dict(part.assignment)[x]
for x in graph.nodes()],
node_size = node_size,
node_shape = "p",
cmap = "Set2",)
plt.show()

tree_proposal = partial(recom,
    pop_col = "population",
    pop_target = ideal_population,
    epsilon = 0.1,
    node_repeats = 1,)

recom_steps = 100
recom_chain = MarkovChain(
    tree_proposal,
    Validator([popbound]),
    accept = always_accept,
    initial_state = init_part,
    total_steps = recom_steps,)

recom_P1_seats = []
    for part in recom_chain:
        recom_P1_seats.append(part["P1 vs P2"].wins("P1"))
plt.figure()
nx.draw(
graph,
pos = {x: x for x in graph.nodes()},
node_color = [dict(part.assignment)[x]
for x in graph.nodes()],
node_size = node_size,
node_shape = "p",
cmap = "Set2",)
plt.show()

seats_won = []
for i in range(1, 101):
    seats_won.append(p1_wins(part))
    recom_P1_seats = []
    for part in recom_chain:
        recom_P1_seats.append(part["P1 vs P2"].wins("P1"))
plt.plot(100, 2, 3)
plt.hist(seats_won)
plt.title("Outlier Analysis (P1 vs P2)")
plt.xlabel("Percentage seats for P1 (%)")
plt.ylabel("Frequency")
plt.show()
