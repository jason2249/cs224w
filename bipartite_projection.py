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
#this code implements the bipartite_projection described in tao zhou et al
NETWORKX_MOVIE_BIPARTITE_ID = 0
NETWORKX_USER_BIPARTITE_ID = 1
NETWORKX_MOVIE_CLASS = "movie"
NETWORKX_USER_CLASS = "user"

def load_graph(graph_name):
	return nx.read_gpickle(graph_name)

def a(i,j, graph):
	if graph.has_edge(i,j):
		return 1
	return 0

#graph is original bipartite graph, movie_graph is projection ointo movies
def assign_weights(user, graph, movie_graph):
	user_nodes = set(n for n,d in graph.nodes(data=True) if d['bipartite']==NETWORKX_USER_BIPARTITE_ID)
	movies_iterator = graph.neighbors(user)
	movies_list = [movie for movie in movies_iterator]
	print(len(movies_list))
	train = int(.9 * len(movies_list))
	#only use the first 90% so that we have some stuff to test on
	movies_to_train = movies_list[:train]
	movies_to_test = movies_list[train:]
	#assign initial weights per user
	for movie in movie_graph.nodes:
		print movie_graph.nodes[movie]
		if movie in movies_to_train:
			print graph.edges[user,movie]
			movie_graph.nodes[movie]["weight"] =  graph.edges[user,movie]['rating']
		else:
			movie_graph.nodes[movie]["weight"] = 0
	new_graph_nodes = {}
	for movie in movie_graph.nodes:
		new_movie_weight = 0.
		for node in user_nodes:
			if a(movie,node,graph) == 0:
				continue

			weight_on_users = 0.
			for transfer_movie in movie_graph.nodes:
				weight_on_users += a(transfer_movie,node, graph) * movie_graph.nodes[transfer_movie]["weight"]/float(graph.degree(transfer_movie))
			new_movie_weight += weight_on_users * a(movie, node, graph) / float(graph.degree(node))
		new_graph_nodes[movie] = new_movie_weight
	return new_graph_nodes, movies_to_test
				

# Usage: python bipartite_projection.py graph_name
# note: graph_name should be a gpickle file from networkx
if __name__ == '__main__':
	graph =load_graph(sys.argv[1])
	movie_nodes = set(n for n,d in graph.nodes(data=True) if d['bipartite']==NETWORKX_MOVIE_BIPARTITE_ID)
	movie_graph = bipartite.projected_graph(graph,movie_nodes)
	mse = []
	for node in graph.nodes:
		true_value = []
		predicted_value = []
		if graph.nodes[node]['bipartite'] == 1:
			if graph.degree(node) < 30:
				continue
			new_movie_weights, movies_to_test = assign_weights(node, graph, movie_graph)
			min_weight = new_movie_weights[min(new_movie_weights.keys(), key = lambda x: new_movie_weights[x])]
			max_weight = new_movie_weights[max(new_movie_weights.keys(), key = lambda  x: new_movie_weights[x])]
			for movie in movies_to_test:
				scaled_score = (new_movie_weights[movie] - min_weight)/(max_weight - min_weight+.00000000001) * 4
				true_value.append(graph.edges[node,movie]["rating"])
				predicted_value.append(scaled_score)
		if true_value:
			mse.append(mean_squared_error(true_value, predicted_value))
	print mse
	print np.mean(mse)