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
from project_onto_movies import project_graph 

#assumes projected_graph is a projected graph as done in project_onto_movies
def predict_rating(bipartite_graph, projected_graph, user, movie):
	similar_movies = set(projected_graph.neighbors(movie))

	#this didn't work
	# avg_ratings = []
	# for similar_movie in similar_movies:
	# 	user1 = set(bipartite_graph.neighbors(movie))
	# 	user2 = set(bipartite_graph.neighbors(similar_movie))
	# 	#make sure that our user rated both movies
	# 	if user not in user2:
	# 		continue
	# 	shared = user1.intersection(user2)
	# 	ratings = 0.
	# 	count = 0.
	# 	for shared_user in shared:
	# 		ratings += bipartite_graph.edges[shared_user,similar_movie]['rating']
	# 		count += 1
	# 	avg_ratings.append(ratings/count)
	# print(np.mean(avg_ratings))
	# print(bipartite_graph.edges[user,movie]['rating'])
	# return np.mean(avg_ratings)
	ratings = []
	for similar_movie in similar_movies:
		if user in bipartite_graph.neighbors(similar_movie):
			ratings.append(bipartite_graph.edges[user,similar_movie]['rating'])
	return np.mean(ratings)

#uses a weighted graph, where edges represent positive or negative correlation
def predict_weighted(graph, projected_graph, user, movie):
	similar_movies = set(projected_graph.neighbors(movie))
	ratings = []
	for similar_movie in similar_movies:
		if user in graph.neighbors(similar_movie):
			if projected_graph.edges[movie, similar_movie]['weight'] == -1:
				ratings.append(6 - graph.edges[user,similar_movie]['rating'])
			else:
				ratings.append(graph.edges[user,similar_movie]['rating'])
	return np.mean(ratings)

if __name__ == '__main__':
	graph = nx.read_gpickle('netflix_tiny.gpickle')
	projected,weighted_projected = project_graph(graph)
	num = 0
	mse = []
	mse_weighted = []
	for node in graph.nodes:
		if num == 250:
			break
		true_value = []
		predicted_value = []
		weighted_predicted = []
		if graph.nodes[node]['bipartite'] == 1:
			if graph.degree(node) < 50:
				continue
			if num % 10 == 1:
				print num
			
			movies = list(graph.neighbors(node))
			test_index = int(.9*len(movies))
			movies_to_test = movies[test_index:]
			for movie in movies_to_test:
				predicted = predict_rating(graph,projected,node,movie)
				weighted = predict_weighted(graph,weighted_projected, node,movie)
				if predicted != predicted:
					continue
				else:
					predicted_value.append(predicted)
				if weighted != weighted:
					continue
				else:
					weighted_predicted.append(weighted)
				true_value.append(graph.edges[node,movie]['rating'])
			num += 1
		if true_value:
			mse.append(mean_squared_error(true_value, predicted_value))
			mse_weighted.append(mean_squared_error(true_value, weighted_predicted))
	print "Mean squared error for unweighted graph"
	print np.mean(mse)
	print "MEan squared error for weighted projection"
	print np.mean(mse_weighted)