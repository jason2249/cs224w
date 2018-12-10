from os import listdir
from os.path import isfile, join
from dateutil.parser import parse
import progressbar
import networkx as nx

user_ratings_directory = "user_ratings"

user_ratings_map = {}

def open_data_directory(file_dir, start):
    files = [join(file_dir, f) for f in listdir(file_dir) if isfile(join(file_dir, f))]
    counter = 0
    with progressbar.ProgressBar(max_value=len(files[start:start + 5000])) as bar:
        for file in files[start:start + 5000]:
            load_file(file)
            bar.update(counter)
            counter += 1

def load_file(filename):
    movie_id = -1
    with open(filename, "rb") as f:
        for line in f:
            # Strip newline character
            line = line[:-1]
            
            if ":" in line:
                # Format of first line of file is "MOVIE_ID:"
                movie_id = int(line[:-1])
                #if movie_id % 5 == 0:
                #    print("The movie id is " + str(movie_id))
            else:
                # Format of this line is "USER_ID,STAR_RATING,YYYY-MM-DD_TIMESTAMP"
                split_line = line.split(",")
                user_id = int(split_line[0])
                rating = int(split_line[1])
                timestamp = split_line[2]
                #timestamp = parse(split_line[2])
                #print(user_id, rating, timestamp)
                add_rating(movie_id, user_id, rating, timestamp)

def add_rating(movie_id, user_id, rating, timestamp):
    if not user_id in user_ratings_map:
        user_ratings_map[user_id] = set([(movie_id, rating)])
    else:
        pass
        #user_ratings_map[user_id].add((movie_id, rating))

def write_ratings():
    num_users = len(user_ratings_map)
    counter = 0
    with progressbar.ProgressBar(max_value=num_users) as bar:
        for user_id in user_ratings_map:
            user_file = "{:07d}".format(user_id) + ".txt"
            qualified_path = join(user_ratings_directory, user_file)
            print_first_line = False
            if not isfile(qualified_path):
                print_first_line = True
            with open(qualified_path, "a+") as f:
                if print_first_line:
                    f.write(str(user_id) + ":\n")
                for user_rating in user_ratings_map[user_id]:
                    f.write(str(user_rating[0]) + "," + str(user_rating[1]) + "\n")
            bar.update(counter)
            counter += 1

if __name__=="__main__":
    print "Reading in all the files..."
    open_data_directory("training_set", 0)
    print "There are", len(user_ratings_map), "user IDs in the ratings map."
    print "Preparing to write user ratings to disk..."
    write_ratings()
    print "Done writing user ratings to disk!"
