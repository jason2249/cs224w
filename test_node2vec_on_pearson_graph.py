from os import listdir
from os.path import isfile, join
from dateutil.parser import parse
import progressbar
import networkx as nx
import numpy as np
import gensim
from gensim.models import Word2Vec
import scipy.spatial
from random import choice

# Get the movies in the test set
# For each movie, get all the users movies and find the most similar movies to that movie
# Take the average of the top 3-5 movies to get the predicted rating for that movie!

edge_thresholds = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300]

probe_ratings = {}

movie_info_memo = {}

def read_probe_file(filename):
    with open(filename, "rb") as f:
        current_movie_id = None
        for line in f:
            # Strip newline character
            line = line[:-1]

            if ":" in line:
                # Movie ID
                current_movie_id = int(line[:-1])
                probe_ratings[current_movie_id] = set()
            else:
                # Customer ID
                customer_id = int(line)
                probe_ratings[current_movie_id].add(customer_id)

def create_movie_projection_graph(data_directory):
    g = nx.Graph()
    files = [join(data_directory, f) for f in listdir(data_directory) if isfile(join(data_directory, f))]
    num_files = 5000 #len(files) # NOTE: We decided to only use 5000 files
    print "Creating movie projection graph with edge threshold " + str(edge_threshold) + "..."
    for i in range(num_files):
        g.add_node((i + 1))
    with progressbar.ProgressBar(max_value=num_files) as bar:
        for i in range(num_files):
            movie_i, users_i = get_movie_info(files[i])
            for j in range(i + 1, num_files):
                movie_j, users_j = get_movie_info(files[j])
                num_users_in_common = len(users_i.intersection(users_j))
                if num_users_in_common > edge_threshold:
                    g.add_edge(movie_i, movie_j)
            bar.update(i)
    return g

def get_movie_info(filename):
    if filename in movie_info_memo:
        return movie_info_memo[filename]
    movie_id = None
    users_rated = set()
    with open(filename, "rb") as f:
        for line in f:
            line = line[:-1]
            if ":" in line:
                movie_id = int(line[:-1])
            else:
                user_id = int(line.split(",")[0])
                if movie_id not in probe_ratings or user_id not in probe_ratings[movie_id]:
                    users_rated.add(user_id)
    movie_info_memo[filename] = (movie_id, users_rated)
    return movie_info_memo[filename]

def get_ratings_in_directory(directory):
    files = [join(directory, f) for f in listdir(directory) if isfile(join(directory, f))]
    num_files_to_test = len(files)
    if directory == "training_set":
        num_files_to_test = 5000 # Can set this to 5000 optionally
    total_lines = 0
    zero_files = 0
    with progressbar.ProgressBar(max_value=num_files_to_test) as bar:
        for i in range(num_files_to_test):
            file_lines = sum(1 for line in open(files[i]))
            total_lines += file_lines - 1
            if file_lines == 0:
                print "Error: File", files[i], "is empty!"
            bar.update(i)
    print "Total ratings for directory " + directory + " were", total_lines
    print "There were", zero_files, "files with zero ratings."

def get_ratings_in_file(file):
    num_lines = 0
    with open(file, "rb") as f:
        for line in f:
            if ":" not in line:
                num_lines += 1
    print num_lines, "in file", file


def get_user_ratings(user_id):
    user_file = "user_ratings/{:07d}".format(user_id) + ".txt"
    user_ratings = {}
    with open(user_file, "rb") as f:
        for line in f:
            line = line[:-1]
            if ":" not in line:
                data = line.split(",")
                movie_id = int(data[0])
                rating = int(data[1])
                if movie_id <= 1000:
                    user_ratings[movie_id] = rating
    return user_ratings

def predict_rating(emb, user_ratings, movie_id):
    sims = [(scipy.spatial.distance.cosine(emb[u"" + str(movie_id)], emb[u"" + str(other_movie_id)]), other_movie_id)
            for other_movie_id in user_ratings if other_movie_id != movie_id and 
            u"" + str(other_movie_id) in emb]
    #n_val = 3
    #print(sorted(sims, reverse=True)[:n_val])
    top_n_movies = [m_data[1] for m_data in sorted(sims, reverse=True)[:n_val]]
    return sum([user_ratings[mov] for mov in top_n_movies]) / (1. * min(n_val, len(top_n_movies)))


if __name__=="__main__":
    print "Reading probe file..."
    read_probe_file("probe.txt")
    print "Done reading probe file."
    embedding_filenames = ["node2vec-master/emb/graph_positive_small_q03.emb",
                           "node2vec-master/emb/graph_positive_small_q05.emb",
                           "node2vec-master/emb/graph_positive_small_q10.emb",
                           "node2vec-master/emb/graph_positive_small_q15.emb",
                           "node2vec-master/emb/graph_positive_small_q20.emb"]
    #emb_filename = "node2vec-master/emb/graph_positive_q03.emb"
    all_user_ratings = {}
    for emb_filename in embedding_filenames:
        mse = []
        #print "Loading embeddings from", emb_filename
        embeddings = Word2Vec.load_word2vec_format(emb_filename)
        number_to_test = 10
        with progressbar.ProgressBar(max_value=number_to_test) as bar:
            for n_val in range(5, 5 + number_to_test):
                sum_error = 0
                count = 0
                for movie_id in range(1, 1001):
                    if movie_id in probe_ratings and u"" + str(movie_id) in embeddings:
                        for user_id in probe_ratings[movie_id]:
                            if user_id in all_user_ratings:
                                user_ratings = all_user_ratings[user_id]
                            else:
                                user_ratings = get_user_ratings(user_id)
                                all_user_ratings[user_id] = user_ratings
                            # Only test if this user has rated 30 or more movies
                            if len(user_ratings) >= 30 and movie_id in user_ratings:
                                sum_error += (predict_rating(embeddings, user_ratings, movie_id) - user_ratings[movie_id]) ** 2
                                count += 1
                mse.append(sum_error / count)
                bar.update(n_val - 4)
        print "mse for file", emb_filename, "is", mse
    #for edge_threshold in edge_thresholds:
    #    g = create_movie_projection_graph("training_set")
    #    nx.write_edgelist(g, "node2vec-master/graph/movie-projection-" + str(edge_threshold) + ".edgelist", data=False)
    # NOTE: Movie IDs start at 1!
    # For each movie/user pair, make sure that user has rated at least n movies.
    # Use an edge threshold of 100 for now.
    # Node2Vec with p = 1 and q = 2

"""
Data for tiny:
100% (9 of 9) |#########################################################################| Elapsed Time: 0:00:09 Time:  0:00:09
mse for file node2vec-master/emb/graph_positive_q03.emb is [1.6363636363636365, 1.4318181818181819, 1.0639730639730638, 1.0170454545454546, 0.9466666666666668, 0.9288215488215489, 0.8708781694495983, 0.8536587816944962, 0.886060343609947]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:00:10 Time:  0:00:10
mse for file node2vec-master/emb/graph_positive_q05.emb is [2.4545454545454546, 1.393939393939394, 1.239057239057239, 1.0852272727272727, 0.970909090909091, 0.8901010101010102, 0.8195485466914041, 0.8214618119975264, 0.8355552931048964]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:00:10 Time:  0:00:10
mse for file node2vec-master/emb/graph_positive_q10.emb is [1.9696969696969697, 1.6666666666666667, 1.2525252525252528, 0.9791666666666666, 1.0096969696969695, 0.9321885521885522, 0.8510884353741498, 0.8555527210884355, 0.8280730634004444]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:00:10 Time:  0:00:10
mse for file node2vec-master/emb/graph_positive_q15.emb is [2.090909090909091, 1.4772727272727273, 1.303030303030303, 1.0511363636363635, 0.9406060606060604, 0.8471717171717172, 0.8449041434755722, 0.8427686301793447, 0.7981441445826368]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:00:10 Time:  0:00:10
mse for file node2vec-master/emb/graph_positive_q20.emb is [1.878787878787879, 1.5757575757575757, 1.1178451178451176, 1.0018939393939394, 1.0169696969696969, 1.0003703703703706, 0.8622201607915896, 0.8252496907854052, 0.84041874241279]

For small:
mse for file node2vec-master/emb/graph_positive_small_q03.emb is [2.0328930974333415, 1.5344297699144447, 1.3617410083894739, 1.27281647146773, 1.2117019686020674, 1.1706767819402206, 1.1427748328891771, 1.1230131124770422, 1.1054199398508593]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:07:48 Time:  0:07:48
mse for file node2vec-master/emb/graph_positive_small_q05.emb is [2.0219287316222276, 1.541012542569981, 1.3838266375022583, 1.282181867264723, 1.219134479607967, 1.173763970798652, 1.144915833819825, 1.1254790564923258, 1.107373467429438]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:07:56 Time:  0:07:56
mse for file node2vec-master/emb/graph_positive_small_q10.emb is [2.004153168867846, 1.51997674225434, 1.343762401823771, 1.2510953982888944, 1.2035418224105223, 1.1677857149449906, 1.1431155622534401, 1.1288392296794676, 1.1056178562932062]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:09:32 Time:  0:09:32
mse for file node2vec-master/emb/graph_positive_small_q15.emb is [2.009635351773403, 1.5321455270371294, 1.3622763057102183, 1.2666697815433174, 1.2135891685356235, 1.1784755101476165, 1.1489096566168249, 1.1288158681045861, 1.112071162882186]
100% (9 of 9) |#########################################################################| Elapsed Time: 0:08:39 Time:  0:08:39
mse for file node2vec-master/emb/graph_positive_small_q20.emb is [2.03131489326356, 1.5461624719661102, 1.3651096898045008, 1.2677755627543816, 1.2065786194866879, 1.1727879761147033, 1.1494877099163934, 1.1247366775571983, 1.1103391376432183]


For small:
First is users who have seen at least 30 movies. number of movies to average over ranges from 5-14 inclusive.
Second is users who have seen at least 50 movies. number of movies to average over ranges from 5-14 inclusive.
Third is users who have seen at least 100 movies. number of movies to average over ranges from 5-14 inclusive.
100% (10 of 10) |#######################################################################| Elapsed Time: 0:07:14 Time:  0:07:14
mse for file node2vec-master/emb/graph_positive_small_q03.emb is [1.2117019686020674, 1.1706767819402206, 1.1427748328891771, 1.1230131124770422, 1.1054199398508593, 1.0929839781256212, 1.0779271483595287, 1.0668493236193481, 1.0610703229367109, 1.0528399594536622]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:06:28 Time:  0:06:28
mse for file node2vec-master/emb/graph_positive_small_q05.emb is [1.219134479607967, 1.173763970798652, 1.144915833819825, 1.1254790564923258, 1.107373467429438, 1.0910261743213234, 1.0773786554792966, 1.0674809513846626, 1.060154659788691, 1.0544664759959896]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:06:07 Time:  0:06:07
mse for file node2vec-master/emb/graph_positive_small_q10.emb is [1.2035418224105223, 1.1677857149449906, 1.1431155622534401, 1.1288392296794676, 1.1056178562932062, 1.0930919605161906, 1.0846340012254585, 1.0750206833668292, 1.0669992786826086, 1.0602296334892378]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:05:47 Time:  0:05:47
mse for file node2vec-master/emb/graph_positive_small_q15.emb is [1.2135891685356235, 1.1784755101476165, 1.1489096566168249, 1.1288158681045861, 1.112071162882186, 1.0941385590708874, 1.0820109833338838, 1.0724837893833918, 1.0632073617813762, 1.0550517337721612]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:05:47 Time:  0:05:47
mse for file node2vec-master/emb/graph_positive_small_q20.emb is [1.2065786194866879, 1.1727879761147033, 1.1494877099163934, 1.1247366775571983, 1.1103391376432183, 1.0975665846544098, 1.0830969855072616, 1.0754192722123426, 1.0680142246840332, 1.0617196887687652]

100% (10 of 10) |#######################################################################| Elapsed Time: 0:04:26 Time:  0:04:26
mse for file node2vec-master/emb/graph_positive_small_q03.emb is [1.238477477477464, 1.1974474474474437, 1.1678019856591484, 1.150999436936937, 1.1272105438772184, 1.1153355855855873, 1.0966141761596395, 1.0814846096096122, 1.0762780532011287, 1.0693935006435047]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:04:02 Time:  0:04:02
mse for file node2vec-master/emb/graph_positive_small_q05.emb is [1.2342432432432302, 1.1957832832832789, 1.166537966537982, 1.14775830518018, 1.1321849627405285, 1.1129797297297301, 1.0983545529000238, 1.0868853228228261, 1.07684311530465, 1.0690453208310393]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:03:49 Time:  0:03:49
mse for file node2vec-master/emb/graph_positive_small_q10.emb is [1.2240180180180018, 1.189151651651651, 1.166023166023181, 1.1531425957207206, 1.1235457679902185, 1.1081981981981979, 1.0989259921078232, 1.087334209209211, 1.0828975425129246, 1.073931329288475]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:03:48 Time:  0:03:48
mse for file node2vec-master/emb/graph_positive_small_q15.emb is [1.2325315315315162, 1.202052052052044, 1.1703254274683004, 1.147828688063063, 1.1281670559448393, 1.1105630630630619, 1.096722135358512, 1.0861940065065085, 1.0773708619862452, 1.0674469111969138]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:03:34 Time:  0:03:34
mse for file node2vec-master/emb/graph_positive_small_q20.emb is [1.2163603603603472, 1.1868806306306259, 1.1673653245081963, 1.1410367398648649, 1.127563674785902, 1.116882882882882, 1.105736728464014, 1.0976836211211218, 1.086549123087582, 1.0800055157198023]

100% (10 of 10) |#######################################################################| Elapsed Time: 0:01:14 Time:  0:01:14
mse for file node2vec-master/emb/graph_positive_small_q03.emb is [1.304697508896798, 1.2656188216686461, 1.2235093325586448, 1.2166648131672597, 1.1688194719036988, 1.1514234875444833, 1.1441575247786842, 1.1241721035982597, 1.121122786329465, 1.1025219696419506]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:01:12 Time:  0:01:12
mse for file node2vec-master/emb/graph_positive_small_q05.emb is [1.2799288256227772, 1.2418940292605771, 1.2230735710654352, 1.2122720195729537, 1.1977944730020675, 1.169857651245553, 1.1504955736596005, 1.144634737050217, 1.1393480595506327, 1.1181095213886272]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:01:13 Time:  0:01:13
mse for file node2vec-master/emb/graph_positive_small_q10.emb is [1.2807829181494677, 1.2331455120601038, 1.2034279904132448, 1.1871663701067616, 1.1598128377487842, 1.1468861209964418, 1.1299373547836846, 1.1049451364175564, 1.102760639305944, 1.1077964993826714]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:01:12 Time:  0:01:12
mse for file node2vec-master/emb/graph_positive_small_q15.emb is [1.3090391459074737, 1.2509885330170039, 1.2297552472946445, 1.1935887455516014, 1.1776503668555887, 1.1532206405693952, 1.1284521043498732, 1.1241721035982604, 1.1246393901745648, 1.108622630546881]
100% (10 of 10) |#######################################################################| Elapsed Time: 0:01:13 Time:  0:01:13
mse for file node2vec-master/emb/graph_positive_small_q20.emb is [1.2686120996441286, 1.2198497429814168, 1.202447527053524, 1.18255115658363, 1.1479065067439944, 1.1558896797153022, 1.1317902414634873, 1.1340945037564254, 1.129114110636146, 1.1199796644636502]
"""

