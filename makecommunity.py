import networkx as nx
import numpy as np

# communities = list(nx.algorithms.community.greedy_modularity_communities(G))
# print nx.algorithms.cluster.clustering(G)
# communities = list(nx.algorithms.community.k_clique_communities(G, 20))
# print len(communities)
# for community in communities:
# 	print sorted(community)
# 	print "---------------"

def get_adjacency_matrix(Graph):
    '''
    This function might be useful for you to build the adjacency matrix of a
    given graph and return it as a numpy array
    '''
    ##########################################################################
    arr = np.zeros((Graph.number_of_nodes(), Graph.number_of_nodes()))
    i = 0
    for node1 in Graph.nodes():
        j = 0
        for node2 in Graph.nodes():
            if Graph.has_edge(node1, node2):
                arr[i][j] += 1
            j += 1
        i += 1
    return arr

def get_sparse_degree_matrix(Graph):
    '''
    This function might be useful for you to build the degree matrix of a
    given graph and return it as a numpy array
    '''
    ##########################################################################
    arr = np.zeros((Graph.number_of_nodes(), Graph.number_of_nodes()))
    i = 0
    for node in Graph.nodes():
        deg = Graph.degree(node)
        arr[i][i] = deg
        i += 1 
    return arr

def getIndexToNodeIdMap(Graph):
    m = {}
    i = 0
    for nId in Graph.nodes():
        m[i] = nId
        i += 1
    return m

def normalized_cut_minimization(Graph, A, D):
    '''
    Implement the normalized cut minimizaton algorithm we derived in the last
    homework here
    '''
    ##########################################################################
    L = D - A
    Dinv = np.linalg.inv(np.sqrt(D))
    temp = np.dot(Dinv, L)
    Lhat = np.dot(temp, Dinv)
    eigenvalues, eigenvectors = np.linalg.eigh(Lhat)
    v = eigenvectors[:, 1]
    c1indexes = set()
    c2indexes = set()
    for i, num in enumerate(v):
        if num < 0:
            c1indexes.add(i)
        else:
            c2indexes.add(i)
    indexToNodeId = getIndexToNodeIdMap(Graph)
    c1 = set()
    c2 = set()
    for i in c1indexes:
        c1.add(indexToNodeId[i])
    for i in c2indexes:
        c2.add(indexToNodeId[i])
    return (c1, c2)

def kmeans_fast(features, k, num_iters=100):
    N, D = features.shape
    assert N >= k, 'Number of clusters cannot be greater than number of points'

    # Randomly initalize cluster centers
    idxs = np.random.choice(N, size=k, replace=False)
    centers = features[idxs]
    assignments = np.zeros(N, dtype=np.int)
    prev_assignments = np.zeros(N, dtype=np.int)
    for n in range(num_iters):
        ### YOUR CODE HERE
        centers = np.repeat(np.swapaxes(np.expand_dims(centers, axis=0),1,2), N, axis=0)
        assignments = np.array(np.argmin([np.linalg.norm(features - centers[:,:,num], axis=1) for num in range(k)], axis=0))
        if np.array_equal(prev_assignments, assignments): return assignments
        centers = np.array([np.average(features[np.argwhere(assignments==num)], axis=0).flatten() for num in range(k)])
        prev_assignments = assignments.copy()
        ### END YOUR CODE
    return assignments

def kWaySpectralClustering(Graph,A,D,k):
    L = D - A
    Dinv = np.linalg.inv(np.sqrt(D))
    print "1"
    temp = np.dot(Dinv, L)
    print "2"
    Lhat = np.dot(temp, Dinv)
    print "3"
    eigenvalues, eigenvectors = np.linalg.eigh(Lhat)
    print "4"
    topTen = eigenvectors[:,:10]

    cluster_assignments = kmeans_fast(topTen, k,1000)
    print "5"
    node_to_cluster = {}
    i = 0
    for node in Graph.nodes():
    	node_to_cluster[node] = cluster_assignments[i]
        i += 1
    return node_to_cluster

G = nx.read_gpickle("movies2500.gpickle")
A = get_adjacency_matrix(G)
D = get_sparse_degree_matrix(G)

# c1, c2 = normalized_cut_minimization(G,A,D)
# print len(c1), len(c2)
# print c1
# print c2
k = 50
movie_to_cluster = kWaySpectralClustering(G,A,D,k)
movieMap = {}
for i in range(k):
	movieMap[i] = []
with open("movie_titles.txt") as f:
	for line in f:
		splitline = line.split(",")
		movieId = int(splitline[0])
		if movieId in movie_to_cluster:
			movieMap[movie_to_cluster[movieId]].append(splitline[2][:-1])
	for i in range(k):
		print len(movieMap[i]), "movies in cluster #", i
		print movieMap[i]


