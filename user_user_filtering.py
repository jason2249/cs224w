import networkx as nx
from create_graphs import get_graph
import numpy as np
import matplotlib.pyplot as plt
from threading import Thread
from Queue import Queue

def compute_rating_mean(user_id, exclude_movie=None):
    user_ratings = {movie: graph.get_edge_data(user_id, movie)["rating"] for movie in graph.neighbors(user_id)}
    if exclude_movie in user_ratings:
        del user_ratings[exclude_movie]
    return np.mean(user_ratings.values())

def get_rating_vector(user_id, rating_means, exclude_movie=None):
    user_vec = np.zeros(len(movies))
    user_ratings = {movie: graph.get_edge_data(user_id, movie)["rating"] for movie in graph.neighbors(user_id)}
    for movie_id in user_ratings:
        if movie_id != exclude_movie:
            user_vec[movie_id - 1] = user_ratings[movie_id] - rating_means[user_id]
    return user_vec


def get_cosine_similarity(user1, user2, rating_means, exclude_movie=None):
    user1_vec = get_rating_vector(user1, rating_means, exclude_movie)
    user2_vec = get_rating_vector(user2, rating_means)
    user1_norm = np.linalg.norm(user1_vec)
    user2_norm = np.linalg.norm(user2_vec)
    if user1_norm == 0 or user2_norm == 0:
        return 0
    return np.dot(user1_vec, user2_vec) / (user1_norm * user2_norm)

def get_similar_users(chosen_user, rating_means, exclude_movie):
    similarities = []
    for user in users:
        if user != chosen_user:
            sim = get_cosine_similarity(chosen_user, user, rating_means, exclude_movie)
            similarities.append((sim, user))
    most_similar = [packet[1] for packet in sorted(similarities)[-31:-1]]
    return [u for u in reversed(most_similar)]

def predict_rating(chosen_user, rating_means, movie_id, most_similar_users):
    similar_users_who_have_seen_movie = []
    for sim_user_id in most_similar_users:
        if graph.has_edge(sim_user_id, movie_id):
            similar_users_who_have_seen_movie.append(sim_user_id)
    if len(similar_users_who_have_seen_movie) == 0:
        return None  # Really not much more we can say about this
    else:
        avg_rating = np.mean(
            [(graph.get_edge_data(sim_user_id, movie_id)["rating"] - rating_means[sim_user_id]) for sim_user_id in
             similar_users_who_have_seen_movie])
        return avg_rating + rating_means[chosen_user]

class SimilarityComputer(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        next_movie_id = self.queue.get()
        self.movie_id = next_movie_id
        self.compute_similarity()
        self.queue.task_done()

    def compute_similarity(self):
        rating_means = {}
        for user in users:
            if user == chosen_user:
                rating_means[user] = compute_rating_mean(user, self.movie_id)
            else:
                rating_means[user] = compute_rating_mean(user)
        actual_rating = graph.get_edge_data(chosen_user, self.movie_id)["rating"]
        sim_users = get_similar_users(chosen_user, rating_means, self.movie_id)
        predicted_rating = predict_rating(chosen_user, rating_means, self.movie_id, sim_users)
        if not predicted_rating:
            print "For movie", self.movie_id, "predicted rating was average rating! (No data)"
        if predicted_rating < 1:
            predicted_rating = 1
        elif predicted_rating > 5:
            predicted_rating = 5
        print "For movie", self.movie_id, "predicted/actual is", predicted_rating, "/", actual_rating
        errors.append((actual_rating - predicted_rating) ** 2)


if __name__=="__main__":
    graph = get_graph()
    movies = {n for n, d in graph.nodes(data=True) if d['bipartite'] == 0}
    users = {n for n, d in graph.nodes(data=True) if d['bipartite'] == 1}
    #rating_means = {}
    #for user in users:
    #    compute_rating_mean(user)

    chosen_user = 1398909
    errors = []
    task_queue = Queue()

    worker_threads = []
    for t in range(5):
        thread = SimilarityComputer(task_queue)
        thread.setDaemon(True)
        thread.start()
        worker_threads.append(thread)

    for movie_id in graph.neighbors(chosen_user):
        task_queue.put(movie_id)
        """
        rating_means = {}
        for user in users:
            if user == chosen_user:
                rating_means[user] = compute_rating_mean(user, movie_id)
            else:
                rating_means[user] = compute_rating_mean(user)
        actual_rating = graph.get_edge_data(chosen_user, movie_id)["rating"]
        sim_users = get_similar_users(chosen_user, rating_means, movie_id)
        predicted_rating = predict_rating(chosen_user, rating_means, movie_id, sim_users)
        if not predicted_rating:
            continue
        if predicted_rating < 1:
            predicted_rating = 1
        elif predicted_rating > 5:
            predicted_rating = 5
        print "For movie", movie_id, "predicted/actual is", predicted_rating, "/", actual_rating
        errors.append((actual_rating - predicted_rating) ** 2)
        """


    """
    similarities = []
    pure_similarities = []
    for user in users:
        sim = get_cosine_similarity(chosen_user, user)
        similarities.append((sim, user))
        if user != chosen_user:
            pure_similarities.append(sim)
    
    plt.title("User-user cosine similarities for user " + str(chosen_user))
    plt.xlabel("Cosine similarity")
    plt.ylabel("# users")
    plt.xlim((0., 1.))
    plt.hist(pure_similarities, 20)
    plt.savefig("user-" + str(chosen_user) + "-cosine-similarities")
    plt.show()
    """

