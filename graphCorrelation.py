import networkx as nx
import numpy as np
import scipy.stats

NETWORKX_MOVIE_BIPARTITE_ID = 0
graph = nx.read_gpickle("netflix500.gpickle")

count = 0
sumPearson = 0.0
for node1, d1 in graph.nodes(data =True):
	if d1['bipartite'] != NETWORKX_MOVIE_BIPARTITE_ID:
		continue
	for node2, d2 in graph.nodes(data=True):
		if d2['bipartite'] != NETWORKX_MOVIE_BIPARTITE_ID:
			continue
		if count % 1000 == 0:
			print count
		node1_ratings = []
		node2_ratings = []
		neighbors = set(graph.neighbors(node1)).intersection(set(graph.neighbors(node2)))
		for user in neighbors:
			node1_ratings.append(graph.edges[user,node1]['rating'])
			node2_ratings.append(graph.edges[user,node2]['rating'])
		if node1_ratings == []:
			continue
		pearson = scipy.stats.pearsonr(node1_ratings, node2_ratings)[0]
		if pearson != pearson:
			continue
		sumPearson += pearson
		count += 1
print "Correlation of whole graph:", sumPearson / count
		