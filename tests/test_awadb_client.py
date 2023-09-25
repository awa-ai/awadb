from awadb.client import Awa

import h5py

def simple_test(client):
    # Add dict with vector to table 'test'
    client.add("test", {'name':'david', 'age':25, 'feature':[1.3, 2.5, 1.9]})

    # Add list of dicts with vector to table 'test'
    docs = [{'name':'jim', 'age':28, 'feature':[1.1, 1.4, 2.3]}, {'name':'john', 'age':40, 'feature':[1.8, 2.3, 4.3]}]
    client.add("test", docs)

    # Search
    results = client.search("test", [1.0, 2.0, 3.0])

    # Output results
    print(results)

def insert_data_test(client, gist):
    total = 300001
    docs = []
    i = 0
    while i < total:
        if i != 0 and i % 50 == 0:
            if i <= 100000:
                client.add("title", docs)
            elif i <= 200000:
                client.add("content", docs)
            elif i <= 300000:
                client.add("label", docs)
            del docs[:]
            print('add batch is %d' % (i/50))
                
        doc = {}
        doc['_id'] = i
        if i < 100000:
            doc['title_feature'] = gist["train"][i]
        elif i < 200000:
            doc['content_feature'] = gist["train"][i]
        elif i < 300000:
            doc['label_feature'] = gist["train"][i]

        docs.append(doc)
        i = i + 1

def search_data_test(client, gist):
    i = 0
    while i < 1000:
        res = client.search("title", gist["test"][i])
        print(res)
        res = client.search("content", gist["test"][i])
        print(res)
        res = client.search("label", gist["test"][i])
        print(res)
        i = i + 1


if __name__ == "__main__":
    # Initialize awadb client
    client = Awa()
    # default gist vector data file path, please input your gist data path
    gist_file_path = '../data/gist-960-euclidean.hdf5'
    f = h5py.File(gist_file_path, 'r')
    # simple quick start example 
    simple_test(client) 
   
    # insert batch docs example
    insert_data_test(client, f)

    # search test example
    search_data_test(client, f)
