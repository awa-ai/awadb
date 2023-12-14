import requests
import json
import h5py

def simple_add_test():
    add_url = "http://localhost:8080/add"
    
    add_req = {}
    add_req["db"] = "restful"
    add_req["table"] = "test"

    docs = []
    doc1 = {}
    doc1["_id"] = 1
    doc1["name"] = "hello"
    doc1["age"] = 21
    doc1["is_male"] = True
    doc1["f"] = [1,1,1,1,1]

    doc2 = {}
    doc2["_id"] = 2 
    doc2["name"] = "world"
    doc2["age"] = 32
    doc2["is_male"] = False 
    doc2["f"] = [0,1,1,1,0]

    docs.append(doc1)
    docs.append(doc2)

    add_req["docs"] = docs

    data_json = json.dumps(add_req)
    res = requests.post(url=add_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
    print(res.text)

def simple_search_test():
    search_url = "http://localhost:8080/search"
    
    add_req = {}
    add_req["db"] = "restful"
    add_req["table"] = "test"

    vector_query = {}
    vector_query["f"] = [0,0,0,1,0]
    add_req["vector_query"] = vector_query

    data_json = json.dumps(add_req)
    res = requests.post(url=search_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
    print(res.text)

def simple_get_test():
    get_url = "http://localhost:8080/get"
    
    add_req = {}
    add_req["db"] = "restful"
    add_req["table"] = "test"
    ids = [1, 2]
    add_req["ids"] = ids 

    data_json = json.dumps(add_req)
    res = requests.post(url=get_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
    print(res.text)

def simple_delete_test():
    get_url = "http://localhost:8080/delete"
    
    add_req = {}
    add_req["db"] = "restful"
    add_req["table"] = "test"
    ids = [1]
    add_req["ids"] = ids 

    data_json = json.dumps(add_req)
    res = requests.post(url=get_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
    print(res.text)

def insert_data_test(gist):
    total = 300001
    docs = []
    i = 0
    add_url = "http://localhost:8080/add"
    while i < total:
        if i != 0 and i % 50 == 0:
            if i <= 100000:
                add_req = {}
                add_req["db"] = "restful"
                add_req["table"] = "title"
                add_req["docs"] = docs
                data_json = json.dumps(add_req)

                res = requests.post(url=add_url,
                        headers={"Content-Type": "application/json"},
                        data=data_json)
                print(res.text)
            elif i <= 200000:
                add_req = {}
                add_req["db"] = "restful"
                add_req["table"] = "content"
                add_req["docs"] = docs
                data_json = json.dumps(add_req)

                res = requests.post(url=add_url,
                        headers={"Content-Type": "application/json"},
                        data=data_json)
                print(res.text)
            elif i <= 300000:
                add_req = {}
                add_req["db"] = "restful"
                add_req["table"] = "label"
                add_req["docs"] = docs
                data_json = json.dumps(add_req)

                res = requests.post(url=add_url,
                        headers={"Content-Type": "application/json"},
                        data=data_json)
                print(res.text)
            del docs[:]
            print('add batch is %d' % (i/50))
                
        doc = {}
        doc['_id'] = i
        if i < 100000:
            doc['title_feature'] = gist["train"][i].tolist()
        elif i < 200000:
            doc['content_feature'] = gist["train"][i].tolist()
        elif i < 300000:
            doc['label_feature'] = gist["train"][i].tolist()

        docs.append(doc)
        i = i + 1

def search_data_test(gist):
    i = 0
    while i < 1000:
        search_url = "http://localhost:8080/search"
        add_req = {}
        add_req["db"] = "restful"
        add_req["table"] = "title"

        vector_query = {}
        vector_query["title_feature"] = gist["test"][i].tolist()
        add_req["vector_query"] = vector_query
        data_json = json.dumps(add_req)
        res = requests.post(url=search_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
        print(res.text)

        add_req1 = {}
        add_req1["db"] = "restful"
        add_req1["table"] = "content"

        vector_query1 = {}
        vector_query1["content_feature"] = gist["test"][i].tolist()
        add_req1["vector_query"] = vector_query1

        data_json = json.dumps(add_req1)
        res = requests.post(url=search_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
        print(res.text)

        add_req2 = {}
        add_req2["db"] = "restful"
        add_req2["table"] = "label"

        vector_query2 = {}
        vector_query2["label_feature"] = gist["test"][i].tolist()
        add_req2["vector_query"] = vector_query2

        data_json = json.dumps(add_req2)
        res = requests.post(url=search_url,
              headers={"Content-Type": "application/json"},
              data=data_json)
        print(res.text)
        i = i + 1


if __name__ == "__main__":
    #simple_test()
    
    simple_add_test()
    simple_search_test()
    """ 
    simple_get_test()
    simple_delete_test()
    simple_get_test()
    """

    """
    gist_file_path = '../../annbench-data/gist-960-euclidean.hdf5'
    f = h5py.File(gist_file_path, 'r')

    #insert_data_test(f)
    search_data_test(f)
    """
