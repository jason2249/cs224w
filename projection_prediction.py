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

	avg_ratings = []
	for similar_movie in similar_movies:
		user1 = set(bipartite_graph.neighbors(movie))
		user2 = set(bipartite_graph.neighbors(similar_movie))
		#make sure that our user rated both movies
		if user not in user2:
			continue
		shared = user1.intersection(user2)
		ratings = 0.
		count = 0.
		for shared_user in shared:
			ratings += bipartite_graph.edges[shared_user,similar_movie]['rating']
			count += 1
		avg_ratings.append(ratings/count)
	return np.mean(avg_ratings)

if __name__ == '__main__':
	graph = nx.read_gpickle('netflix_tiny.gpickle')
	projected,_ = project_graph(graph)
	num = 0
	mse = []
	for node in graph.nodes:
		if num == 100:
			break
		true_value = []
		predicted_value = []
		if graph.nodes[node]['bipartite'] == 1:
			if graph.degree(node) < 50:
				continue
			if num % 10 == 1:
				print num
			
			movies = list(graph.neighbors(node))
			test_index = int(.9*len(movies))
			movies_to_test = movies[test_index:]
			for movie in movies_to_test:
				true_value.append(graph.edges[node,movie]['rating'])
				predicted = predict_rating(graph,projected,node,movie)
				if predicted != predicted:
					predicted_value.append(3)
				else:
					predicted_value.append(predicted)
			print true_value
			print predicted_value
			num += 1
		if true_value:
			mse.append(mean_squared_error(true_value, predicted_value))
	print mse
	print np.mean(mse)