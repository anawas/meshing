import networkx as nx

G = nx.Graph()
G.add_node((1,1,1))
G.add_nodes_from([(1,0,0),(0,0,1)])
G.add_edges_from([(1, 2), (1, 3)])
print(G.number_of_edges())

print(list(G.neighbors(2)))
sp = nx.shortest_path(G, 1,2)
print(sp)