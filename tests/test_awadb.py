# -*- coding:utf-8 -*-
#!/usr/bin/python3

import awadb
from langchain.vectorstores import AwaDB
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter




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

def Test_Load(awadb_client):
    ret = awadb_client.Load('testdb3')
    if ret : print('awadb load table success')
    else:
        print('awadb load table failed')


def Test_LangChain_Interface(awadb_client):
    awadb_client.Create("test_langchain")

    texts = ["lion", "tiger", "tree", "flower", "frog", "elephant", "cabbage"]
    ids = awadb_client.AddTexts("embedding_text", "text_embedding", texts=texts)

    not_include_fields: Set[str] = {"text_embedding"}
    result = awadb_client.Search("giraffe", 3, not_include_fields)

    print(result)

    keys1: List[str] = []
    keys2: List[str] = []
    i = 0
    for item_id in ids:
        if i < 3:
            keys1.append(item_id)
        if i >= 5:
            keys2.append(item_id)
        i = i + 1

    print(keys1)
    print(keys2)
    not_pack_fields: Set[str] = {"text_embedding"}
    show1 = awadb_client.Get(ids=keys1, not_include_fields=not_pack_fields)
    print(show1)
    awadb_client.Delete(keys1)
    show2 = awadb_client.Get(ids=keys1, not_include_fields=not_pack_fields)
    print(show2)

    awadb_client.UpdateTexts(ids=keys2, text_field_name="embedding_text", texts=["dolphine", "rose"])

    show3 = awadb_client.Get(keys2, not_include_fields=not_pack_fields)
    print(show3)

def Test_LangChain_MMR_Search():
    documents = TextLoader("state_of_the_union.txt", encoding="utf-8").load()

    docsearch = AwaDB.from_documents(
        RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=0, keep_separator=False)
        .split_documents(documents), table_name='langchain_awadb_qa')

    results = docsearch.max_marginal_relevance_search("What is the purpose of the NATO Alliance?")

    print(results[0])
    print(results[1])
    print(results[2])

    print('=================')
    s_results = docsearch.similarity_search("What is the purpose of the NATO Alliance?")
    print(s_results[0])
    print(s_results[1])
    print(s_results[2])



if __name__ == "__main__":
    awadb_client = awadb.Client()
    #Test_EmbeddingText(awadb_client)
    #Test_Vector1(awadb_client)
    #Test_Vector2(awadb_client)
    #Test_Load(awadb_client)
    Test_LangChain_Interface(awadb_client)
    #Test_LangChain_MMR_Search()
