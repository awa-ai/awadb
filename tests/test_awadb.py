# -*- coding:utf-8 -*-
#!/usr/bin/python3

import awadb

def Test_EmbeddingText(awadb_client):
    awadb_client.Create("test_llm2") 

    sentences_set = ["The man is happy", "The man is very happy", "The cat is happy", "The man is eating"]

    awadb_client.Add([{'embedding_text':'The man is happy'}, {'source' : 'pic1'}])
    awadb_client.Add([{'embedding_text':'The man is very happy'}, {'source' : 'pic2'}])
    awadb_client.Add([{'embedding_text':'The cat is happy'}, {'source' : 'pic3'}])
    awadb_client.Add(['The man is eating', 'pic4'])

    query = "The man is happy"
    print('Dataset :',sentences_set)
    print('Query :', query)
    results = awadb_client.Search(query, 3)
    print(results)

    #doc = awadb_client.Get('2')
    #print(doc)


def Test_Vector1(awadb_client):
    awadb_client.Create("testdb3")
    awadb_client.Add([{'primary':'123'}, {'name':'lj'}, {'gender':'male'}, {'age':39}, 'hello', 'world', [1, 3.5, 3]])
    awadb_client.Add([{'primary':'235'}, {'name':'hu'}, {'gender':'male'}, {'age':28}, 'what', 'doing', [1, 3.4, 2]])
    awadb_client.Add([{'primary':'398'}, {'name':'er'}, {'gender':'female'}, {'age':45}, 'yu', 'hi', [1, 2.4, 4]])
    awadb_client.Add([{'primary':'345'}, {'name':'hehe'}, {'gender':'female'}, {'age':25}, 'hhuhu', 'hello', [1.3, 2.9, 8.9]])

    doc1 = awadb_client.Get('1')
    print(doc1) 

    result = awadb_client.Search([3.0, 3.1, 4.2], 3)
    
    query = [3.0, 3.1, 4.2]
    print('Query:', query)
    print(result)


def Test_Vector2(awadb_client):
    awadb_client.Create("testdb10")
    awadb_client.Add([{'primary':'298'}, {'name':'lv'}, {'gender':'male'}, {'age':39}, 'hello', 'world', [1, 3.5, 3]])
    awadb_client.Add([{'primary':'209'}, {'name':'ho'}, {'gender':'male'}, {'age':28}, 'what', 'doing', [1, 3.4, 2]])

if __name__ == "__main__":
    awadb_client = awadb.Client()
    #Test_EmbeddingText(awadb_client)
    Test_Vector1(awadb_client) 
    #Test_Vector2(awadb_client) 
