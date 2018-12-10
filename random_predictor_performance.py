from os import listdir
from os.path import isfile, join
import numpy as np
import random

files = [join("user_ratings", "{:07d}".format(user_id) + ".txt") for user_id in range(1, 6000) if isfile(join("user_ratings", "{:07d}".format(user_id) + ".txt"))]
mse = []
for file in files:
    count = 0
    error_sum = 0
    with open(file, "rb") as f:
        for line in f:
            line = line[:-1]
            if ":" not in line:
                rating = int(line.split(",")[1])
                error_sum += (random.randint(1, 5) - rating) ** 2
                count += 1
    mse.append((error_sum * 1. / count))

print "Mean squared error for random predictor on first", len(files), "user ratings is", np.mean(mse)
