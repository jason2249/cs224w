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

NETWORKX_MOVIE_BIPARTITE_ID = 0
NETWORKX_USER_BIPARTITE_ID = 1
NETWORKX_MOVIE_CLASS = "movie"
NETWORKX_USER_CLASS = "user"

def pearson_similarity(i,j, graph, user_to_ignore):
	sim = 0.
	average_i = 0.
	average_j = 0.
	for edge in graph.edges(i):
		average_i += graph.edges[edge]["rating"]
	average_i /= len(graph.edges(i))
	for edge in graph.edges(j):
		average_j += graph.edges[edge]["rating"]
	average_j /= len(graph.edges(j))
	sum_i = 0.
	sum_j = 0.
	for user in graph.neighbors(i):
		if graph.has_edge(user,j) and user is not user_to_ignore:
			sim += (graph.edges[user,i]["rating"] - average_i) * (graph.edges[user,j]["rating"] - average_j)
			sum_i += (graph.edges[user,i]["rating"] - average_i)**2
			sum_j += (graph.edges[user,j]["rating"] - average_j)**2
	sum_i = np.sqrt(sum_i)
	sum_j = np.sqrt(sum_j)
	return sim/sum_i/sum_j

def cosine_similarity(i,j,graph,user_to_ignore):
	sim = 0.
	sum_i = 0.
	sum_j = 0.
	for user in graph.neighbors(i):
		if graph.has_edge(user,j) and user is not user_to_ignore:
			user_ratings = []
			for neighbor in graph.neighbors(user):
				user_ratings.append(graph.edges[user,neighbor]['rating'])
			average_u = np.mean(user_ratings)	
			sim += (graph.edges[user,i]["rating"] - average_u) * (graph.edges[user,j]["rating"] - average_u)
			sum_i += (graph.edges[user,i]["rating"] - average_u)**2
			sum_j += (graph.edges[user,j]["rating"] - average_u)**2
	sum_i = np.sqrt(sum_i)
	sum_j = np.sqrt(sum_j)
	return sim/sum_i/sum_j

def similarity(item, movie, graph, user_to_ignore, mode):
	if mode == "pearson":
		return pearson_similarity(item, movie, graph, user_to_ignore)
	return cosine_similarity(item, movie, graph, user_to_ignore)

def prediction(user, item, graph, mode, movies_to_ignore):
	numerator = 0.
	denominator = 0.
	for edge in graph.edges(user):
		movie = edge[1]
		if movie in movies_to_ignore:
			continue
		sim = similarity(item,movie,graph,user, mode)
		numerator += sim * graph.edges[edge]['rating']
		denominator += np.abs(sim)
	adjustment = 0
	if mode == "cosine":
		for neighbor in graph.neighbors(user):
			adjustment += graph.edges[user,neighbor]['rating']
	adjustment /= graph.degree(user)
	return numerator/denominator + adjustment


if __name__ == '__main__':
	graph =nx.read_gpickle(sys.argv[1])
	print "finished loading graph"
	mse_cosine = []
	mse_pearson = []
	for node in graph.nodes:
		true_value = []
		predicted_value_pearson = []
		predicted_value_cosine = []
		if graph.nodes[node]['bipartite'] == 1:
			if graph.degree(node) < 35:
				continue
			print graph.degree(node)
			movies_list = [movie for movie in graph.neighbors(node)]
			train = int(.9 * len(movies_list))
			#only use the first 90% so that we have some stuff to test on
			movies_to_test = movies_list[train:]
			for movie in movies_to_test:
				true_value.append(graph.edges[node,movie]["rating"])
				predicted_value_pearson.append(prediction(node, movie, graph, "pearson", movies_to_test))
				predicted_value_cosine.append(prediction(node, movie, graph, "cosine", movies_to_test))
			print "the true values were", true_value
			print "the predicted value for pearson was ", predicted_value_pearson
			print "the predicted value for cosine was", predicted_value_cosine
			mse_pearson.append(mean_squared_error(true_value,predicted_value_pearson))
			mse_cosine.append(mean_squared_error(true_value, predicted_value_cosine))
	print mse_cosine
	print mse_pearson
	print "cosine average mse", np.mean(mse_cosine)
	print "pearson mean_squared_error", np.mean(mse_pearson)	