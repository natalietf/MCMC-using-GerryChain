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
​
import random
import matplotlib.pyplot as plt
from functools import partial
import networkx as nx

k_partitions = 8 # Number of districts
node_size = 30 # Size of each point on graph
grid_height = 40 # Number or nodes vertically
grid_width = 60 # Number of nodes horizontally

graph = nx.grid_graph([grid_height, grid_width])

plt.figure()
nx.draw(graph, pos={x: x for x in graph.nodes()}, node_size=node_size, node_shape="p")
plt.show()

random_boundary = 0.50 # chance of party 1 vote
P1 = "skyblue"
P2 = "navy"

for node in graph.nodes():
    graph.nodes[node]["population"] = 1 # counts population

    if random.random() < random_boundary: # creates party 1 and 2 votes at random
        graph.nodes[node][P1] = 1
        graph.nodes[node][P2] = 0
    else:
        graph.nodes[node][P1] = 0
        graph.nodes[node][P2] = 1

vote_dict = {1: P1, 0: P2} # translates binary to votes

plt.figure() #plots grid figure
nx.draw(
    graph,
    pos={x: x for x in graph.nodes()},
    node_color=[vote_dict[graph.nodes[x][P1]] for x in graph.nodes()],
    node_size=node_size,
    node_shape="p",
)
plt.show()

def step_num(partition):
    parent = partition.parent
    if not parent:
        return 0
    return parent["step_num"] + 1

updaters = {
    "population": Tally("population"),
    "cut_edges": cut_edges,
    "step_num": step_num,
    "P1 vs P2": Election("P1 vs P2", {"P1": P1, "P2": P2}),
}

part_dict = {x: int(x[0]/(grid_width/k_partitions)) for x in graph.nodes()} # assigns each node to a district

init_part = Partition(graph, assignment=part_dict, updaters=updaters) # initial partition

plt.figure() # plots grid figure
nx.draw(
    graph,
    pos={x: x for x in graph.nodes()},
    node_color=[part_dict[x] for x in graph.nodes()],
    node_size=node_size,
    node_shape="p",
    cmap="Set2",
)
plt.show()

def p1_wins(partition): # when called shows percentage of seats won by first party
    if partition["P1 vs P2"].wins("P1")+partition["P1 vs P2"].wins("P2") > k_partitions:
        return equal_check(partition, "P1")
    else:
        return (partition["P1 vs P2"].wins("P1")/k_partitions)*100

def p2_wins(partition): # when called shows percentage of seats won by second party
    if partition["P1 vs P2"].wins("P1")+partition["P1 vs P2"].wins("P2") > k_partitions:
        return equal_check(partition, "P2")
        #return ((partition["P1 vs P2"].wins("P2")/k_partitions)*100)-(100/k_partitions)/2
    else:
        return (partition["P1 vs P2"].wins("P2")/k_partitions)*100
    
def equal_check(partition, party): # gives disrtict 50/50 split if votes for each party are the same
    for number in range(1, k_partitions+1):
        if partition["P1 vs P2"].wins("P1")+partition["P1 vs P2"].wins("P2") == k_partitions + number:
            return ((partition["P1 vs P2"].wins(party)/k_partitions)*100)-((100/k_partitions)/2)*number
    raise error

ideal_population = sum(init_part["population"].values()) / len(init_part)
popbound = within_percent_of_ideal_population(init_part, 0.1) # population constraint
cutedgebound = UpperBound(lambda part: len(part["cut_edges"]), 400) # compactness constraint

flip_steps = 250000 # number of steps to be taken

flip_chain = MarkovChain(
    propose_random_flip, # proposal function
    Validator([single_flip_contiguous, popbound, cutedgebound]), # list of constraints
    accept = always_accept,
    initial_state = init_part,
    total_steps = flip_steps, 
)

flip_steps = 250000 # number of steps to be taken

flip_chain = MarkovChain(
    propose_random_flip, # proposal function
    Validator([single_flip_contiguous, popbound, cutedgebound]), # list of constraints
    accept = always_accept,
    initial_state = init_part,
    total_steps = flip_steps, 
)

flip_p1_seats = [] # records P1 seats

step_counter = 0 # records steps

print("Step " + str(step_counter) + ":")

plt.figure() # shows initial partition
nx.draw(
    graph,
    pos = {x: x for x in graph.nodes()},
    node_color = [part_dict[x] for x in graph.nodes()],
    node_size = node_size,
    node_shape = "p",
    cmap = "Set2",
)
plt.show()

for part in flip_chain: # runs flip chain
    step_counter = step_counter + 1
    flip_p1_seats.append(part["P1 vs P2"].wins("P1"))
    if step_counter % flip_steps == 0:
        print(part["P1 vs P2"])

plt.figure() # prints map
nx.draw(
    graph,
    pos = {x: x for x in graph.nodes()},
    node_color = [dict(part.assignment)[x] for x in graph.nodes()],
    node_size = node_size,
    node_shape = "p",
    cmap = "Set2",
)
plt.show()

tree_proposal = partial( # defines the proposal function
    recom,
    pop_col = "population",
    pop_target = ideal_population,
    epsilon = 0.1, # percentage of deviation from ideal population
    node_repeats = 1,
)

recom_steps = 50 # number of steps to be taken

recom_chain = MarkovChain(
    tree_proposal, # proposal function
    Validator([popbound]),
    accept = always_accept,
    initial_state = init_part,
    total_steps = recom_steps,
)

recom_P1_seats = [] # records P1 seats
step_counter = 0 # records steps taken

print("Step " + str(step_counter) + ":")

plt.figure() # shows inital partition
nx.draw(
    graph,
    pos={x: x for x in graph.nodes()},
    node_color=[part_dict[x] for x in graph.nodes()],
    node_size=node_size,
    node_shape="p",
    cmap="Set2",
)
plt.show()

for part in recom_chain: # runs recom chain
    step_counter = step_counter + 1
    recom_P1_seats.append(part["P1 vs P2"].wins("P1"))
    if step_counter % recom_steps == 0:
        print(part["P1 vs P2"])

plt.figure() # prints map
nx.draw(
    graph,
    pos = {x: x for x in graph.nodes()},
    node_color = [dict(part.assignment)[x] for x in graph.nodes()],
    node_size = node_size,
    node_shape = "p",
    cmap = "Set2",
)
plt.show()

seats_won = [] # makes a list of the P1 seat percentage of each map

for i in range(1, 11): # creates 10 maps
    seats_won.append(p1_wins(part)) # records P1 seats
    recom_P1_seats = []
    for part in recom_chain:
        recom_P1_seats.append(part["P1 vs P2"].wins("P1"))
    print("Map " + str(i) + ":")
    print(str(p1_wins(part)) + "% seats for first party")
    print(str(p2_wins(part)) + "% seats for second party")
    print(" ")

plt.plot(100, 2, 3)
plt.hist(seats_won)
plt.title("Outlier Analysis (P1 vs P2)")
plt.xlabel("Percentage seats for P1 (%)")
plt.ylabel("Frequency")
plt.show()
