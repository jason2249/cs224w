from os import listdir
from os.path import isfile, join
from dateutil.parser import parse
import snap
import networkx as nx
from networkx.algorithms import bipartite

# User IDs and movie IDs collide... sigh
USER_ID_OFFSET = 20000

SNAP_MM_MOVIE_MODE = "movie_mode"
SNAP_MM_USER_MODE = "user_mode"
SNAP_MM_CROSSNET = "movie_user_crossnet"
SNAP_ATTRIBUTE_RATING = "rating"
SNAP_ATTRIBUTE_TIMESTAMP = "timestamp"

NETWORKX_MOVIE_BIPARTITE_ID = 0
NETWORKX_USER_BIPARTITE_ID = 1
NETWORKX_MOVIE_CLASS = "movie"
NETWORKX_USER_CLASS = "user"

# Important stuff
# Documentation: https://snap.stanford.edu/snappy/doc/reference/multimodal.html
#graph_mode = "snap-multimodal-network"
graph_mode = "networkx-bipartite"
INCLUDE_TIMESTAMPS = False
TEST_MODE = True # Set to true to build a smaller graph of the first 100 movies
graph = None

def create_graph():
    global graph
    if graph_mode == "snap-multimodal-network":
        # There will be 497959 nodes and 100480507 edges
        graph = snap.TMMNet.New()
        graph.AddModeNet(SNAP_MM_MOVIE_MODE)
        graph.AddModeNet(SNAP_MM_USER_MODE)
        graph.AddCrossNet(SNAP_MM_USER_MODE, SNAP_MM_MOVIE_MODE, SNAP_MM_CROSSNET, False)
        rating_crossnet = graph.GetCrossNetByName(SNAP_MM_CROSSNET)
        rating_crossnet.AddIntAttrE(SNAP_ATTRIBUTE_RATING)
        if INCLUDE_TIMESTAMPS:
            rating_crossnet.AddStrAttrE(SNAP_ATTRIBUTE_TIMESTAMP)
    elif graph_mode == "networkx-bipartite":
        graph = nx.Graph()
    else:
        raise Exception("Unsupported graph type")

def open_data_directory(file_dir):
    files = [join(file_dir, f) for f in listdir(file_dir) if isfile(join(file_dir, f))]
    if TEST_MODE:
        for file in files[:100]:
            load_file(file)
    else:
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
                if movie_id % 10 == 0:
                    print("The movie id is " + str(movie_id))
                add_movie(movie_id)
            else:
                # Format of this line is "USER_ID,STAR_RATING,YYYY-MM-DD_TIMESTAMP"
                split_line = line.split(",")
                user_id = int(split_line[0])
                rating = int(split_line[1])
                timestamp = split_line[2]
                #timestamp = parse(split_line[2])
                #print(user_id, rating, timestamp)
                add_rating(movie_id, user_id, rating, timestamp)

def add_movie(movie_id):
    if graph_mode == "snap-multimodal-network":
        movie_net = graph.GetModeNetByName(SNAP_MM_MOVIE_MODE)
        if not movie_net.IsNode(movie_id):
            movie_net.AddNode(movie_id)
    elif graph_mode == "networkx-bipartite":
        graph.add_node(movie_id, bipartite=NETWORKX_MOVIE_BIPARTITE_ID)
    else:
        raise Exception("Unsupported graph type")

def add_rating(movie_id, user_id, rating, timestamp):
    if graph_mode == "snap-multimodal-network":
        user_net = graph.GetModeNetByName(SNAP_MM_USER_MODE)
        rating_crossnet = graph.GetCrossNetByName(SNAP_MM_CROSSNET)
        user_id += USER_ID_OFFSET
        # Add the user if they don't already exist
        if not user_net.IsNode(user_id):
            user_net.AddNode(user_id)
        # Add edge from user to movie and edge attributes
        edge_id = rating_crossnet.AddEdge(user_id, movie_id)
        rating_crossnet.AddIntAttrDatE(edge_id, rating, SNAP_ATTRIBUTE_RATING)
        if INCLUDE_TIMESTAMPS:
            rating_crossnet.AddStrAttrDatE(edge_id, timestamp, SNAP_ATTRIBUTE_TIMESTAMP)
        #print("For rating " + str(rating) + ", the received rating was " + str(rating_crossnet.GetIntAttrDatE(edge_id, SNAP_ATTRIBUTE_RATING)))
        #print("For timestamp " + timestamp + ", the received timestamp was " + str(rating_crossnet.GetStrAttrDatE(edge_id, SNAP_ATTRIBUTE_TIMESTAMP)))
    elif graph_mode == "networkx-bipartite":
        user_id += USER_ID_OFFSET
        graph.add_node(user_id, bipartite=NETWORKX_USER_BIPARTITE_ID)
        if INCLUDE_TIMESTAMPS:
            graph.add_edge(user_id, movie_id, rating=rating, timestamp=timestamp)
        else:
            graph.add_edge(user_id, movie_id, rating=rating)
    else:
        raise Exception("Unsupported graph type")


if __name__=="__main__":
    if TEST_MODE:
        print("Test mode is on! Graph will only be created with the first 100 movies.")
        print("To turn off test mode, set TEST_MODE = False in the file.")
    if INCLUDE_TIMESTAMPS:
        print("Timestamps are included! Note that the final graph file will be about 25% bigger.")
    else:
        print("Timestamps are not included in the graph! This should save some space on disk.")
    create_graph()
    open_data_directory("training_set")

    # Here's how to do bipartite stuff with the graph:
    #print(nx.is_connected(graph))
    #movie_nodes = set(n for n,d in graph.nodes(data=True) if d['bipartite']==NETWORKX_MOVIE_BIPARTITE_ID)
    #print(movie_nodes)
    #movie_graph = bipartite.projected_graph(graph, movie_nodes)
    #print(movie_graph.edges())
    nx.write_gpickle(graph, "netflix.gpickle")
    # To load the graph again, write:
    #loaded = nx.read_gpickle("test.gpickle")

    # NOTE: The following code is only for snap.
    #FOut = snap.TFOut("netflix.graph")
    #graph.Save(FOut)
    #FOut.Flush()
    #print("Saved graph to filename netflix.graph.")


    # Note: You can convert the graph to a network like this:
    # This can then be saved as an edge list.
    # The advantage of this is that we can use our standard graph algorithms on it.
    #crossnetids = snap.TIntV()
    #crossnetids.Add(graph.GetCrossId(SNAP_MM_CROSSNET))
    #nodeattrmapping = snap.TIntStrStrTrV()
    #edgeattrmapping = snap.TIntStrStrTrV()
    #pneanet = graph.ToNetwork(crossnetids, nodeattrmapping, edgeattrmapping)
    #snap.SaveEdgeList(pneanet, "testing.txt")

    #DegToCntV = snap.TIntPrV()
    #snap.GetDegCnt(pneanet, DegToCntV)
    #for item in DegToCntV:
    #    print "%d nodes with degree %d" % (item.GetVal2(), item.GetVal1())


