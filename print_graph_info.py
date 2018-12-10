import timeit
import networkx as nx
from os import listdir
from os.path import isfile, join
from collections import Counter
import numpy as np


def open_data_directory(file_dir):
    files = [join(file_dir, f) for f in listdir(file_dir) if isfile(join(file_dir, f))]
    for file in files:
        load_file(file)

def load_file(filename):
    movie_id = -1
    with open(filename, "rb") as f:
        for line in f:
            # Strip newline character
            line = line[:-1]
            
            if ":" in line:
                # Format of first line of file is "MOVIE_ID:"
                movie_id = int(line[:-1])
                if movie_id % 1000 == 0:
                    print("The movie id is " + str(movie_id))
                add_movie(movie_id)
            else:
                # Format of this line is "USER_ID,STAR_RATING,YYYY-MM-DD_TIMESTAMP"
                split_line = line.split(",")
                user_id = int(split_line[0])
                rating = int(split_line[1])
                timestamp = split_line[2]
                add_rating(movie_id, user_id, rating, timestamp)
    ratings[movie_id] = np.mean(ratings[movie_id])

def add_movie(movie_id):
    ratings[movie_id] = []

def add_rating(movie_id, user_id, rating, timestamp):
    movie_counter[movie_id] += 1
    user_counter[user_id] += 1
    rating_counter[rating] += 1
    ratings[movie_id].append(rating)

if __name__=="__main__":
    movie_counter = Counter()
    user_counter = Counter()
    rating_counter = Counter()
    ratings = {}
    open_data_directory("training_set")