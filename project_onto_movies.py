from os import listdir
from os.path import isfile, join
from dateutil.parser import parse
import snap
import sys
import networkx as nx
from networkx.algorithms import bipartite
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
import numpy as np
import scipy
#this code implements the bipartite_projection described in tao zhou et al
NETWORKX_MOVIE_BIPARTITE_ID = 0
NETWORKX_USER_BIPARTITE_ID = 1
NETWORKX_MOVIE_CLASS = "movie"
NETWORKX_USER_CLASS = "user"

#project an edge only if the two movies have both positive ratings (pearson coeff of > .5)
def project_graph(graph):
	new_graph = nx.Graph()
	for node, d in graph.nodes(data =True):
		if d['bipartite'] == NETWORKX_MOVIE_BIPARTITE_ID: 
			new_graph.add_node(node)
	pairs_done = set()
	print(len(new_graph.nodes))
	count = 0
	for node1 in new_graph:
		if count % 10 == 0:
			print count
		for node2 in new_graph:
			if (node1,node2) in pairs_done or node1 == node2:
				continue
			node1_ratings = []
			node2_ratings = []
			neighbors = set(graph.neighbors(node1)).intersection(set(graph.neighbors(node2)))
			for user in neighbors:
				node1_ratings.append(graph.edges[user,node1]['rating'])
				node2_ratings.append(graph.edges[user,node2]['rating'])
			#if they are strongly correlated
			if node1_ratings == []:
				continue
			if scipy.stats.pearsonr(node1_ratings, node2_ratings) > .5:
				new_graph.add_edge(node1,node2)
		count += 1
	print(len(new_graph.edges))

	return new_graph


def test_graph():
	graph = nx.Graph()
	for i in range(5):
		graph.add_node(i, bipartite = NETWORKX_USER_BIPARTITE_ID)
	for movie_id in range(6,10):
		graph.add_node(movie_id, bipartite = NETWORKX_MOVIE_BIPARTITE_ID)
	graph.add_edge(1,6, rating = 5)
	graph.add_edge(1,7, rating = 5)
	graph.add_edge(2,6, rating = 5)
	graph.add_edge(2,7, rating = 4)
	return graph

if __name__ == '__main__':
	graph = nx.read_gpickle('netflix_tiny.gpickle')
	new_graph = project_graph(graph)
	nx.write_gpickle(new_graph, "projected_graph_tiny.gpickle")
	#graph = test_graph()
	#print(project_graph(graph).edges)


