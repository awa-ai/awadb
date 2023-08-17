# -*- coding:utf-8 -*-
#!/usr/bin/python3

import sys
import os

# Get the current directory path
current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(current_directory)
# Add the current directory to sys.path
sys.path.insert(0, current_directory)

import awadb
from langchain.vectorstores import AwaDB
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.schema import Document



def Test_EmbeddingText(awadb_client):
    awadb_client.Create("test_llm2", "HuggingFace")

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

    from awadb import AwaEmbedding
    test_embedding = AwaEmbedding("HuggingFace")
    print("Test the Embedding model ##########\n\n")
    print(test_embedding.Embedding("Test the embedding"))

    #doc = awadb_client.Get('2')
    #print(doc)


def Test_Vector1(awadb_client):
    awadb_client.Create("testdb3")
    awadb_client.Add([{'primary':'123'}, {'name':'lj'}, {'gender':'male'}, {'age':39}, {'word1':'hello'}, {'word2':'world'}, {'emb1':[1, 3.5, 3]}])
    awadb_client.Add([{'primary':'235'}, {'name':'hu'}, {'gender':'male'}, {'age':28}, {'word1':'what'}, {'word2':'doing'}, {'emb1':[1, 3.4, 2]}])
    awadb_client.Add([{'primary':'398'}, {'name':'er'}, {'gender':'female'}, {'age':45}, {'word1':'yu'}, {'word2':'hi'}, {'emb1':[1, 2.4, 4]}])
    awadb_client.Add([{'primary':'345'}, {'name':'hehe'}, {'gender':'female'}, {'age':25}, {'word1':'hhuhu'}, {'word2':'hello'}, {'emb1':[1.3, 2.9, 8.9]}])

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
    result = awadb_client.Search(query="giraffe", topn=3, not_include_fields=not_include_fields)

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
    print('finish')

def Test_LangChain_MMR_Search():
    documents = TextLoader("state_of_the_union.txt", encoding="utf-8").load()

    docsearch = AwaDB.from_documents(
        RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=0, keep_separator=False)
        .split_documents(documents), table_name='langchain_awadb_qa')

    results = docsearch.max_marginal_relevance_search("What is the purpose of the NATO Alliance?")

    print(results[0])
    print(results[1])
    print(results[2])

    print('------------------')
    s_results = docsearch.similarity_search("What is the purpose of the NATO Alliance?", text_in_page_content="NATO")
    for s_result in s_results:
        print(s_result)
    print('------------------')
     
    s_results = docsearch.similarity_search("What is the purpose of the NATO Alliance?", text_in_page_content="Alliance")
    for s_result in s_results:
        print(s_result)
    print('------------------')
    s_results = docsearch.similarity_search("What is the purpose of the NATO Alliance?")
    for s_result in s_results:
        print(s_result)

    print('#################')
    r_results = docsearch.similarity_search_with_score("What is the purpose of the NATO Alliance?")
    for r_result in r_results:
        print(r_result)

    print('*****************')
    f_results = docsearch.get(text_in_page_content="American people")
    for id in f_results:
        print(id)
        print(f_results[id])

    print('*****************')
    f_results1 = docsearch.get(text_in_page_content="Alliance")
    for id in f_results1:
        print(id)
        print(f_results1[id])

    print('*****************')
    f_results2 = docsearch.get(text_in_page_content="American President")
    for id in f_results2:
        print(id)
        print(f_results2[id])

    print('*****************')
    f_results3 = docsearch.get(text_in_page_content="create jobs")
    for id in f_results3:
        print(id)
        print(f_results3[id])

def Test_LangChain_MetaFilter():
    texts = ["Men's Regular-Fit Cotton Pique Polo Shirt (Available in Big & Tall)",
             "It's Weird Being The Same Age As Old People Sarcastic Retro T-Shirt",
             "I Have Selective Hearing You Weren't Selected Today T-Shirt",
             "Men's Loose Fit Heavyweight Short-Sleeve Pocket T-Shirt",
             "Men's Essentials Camouflage Print Tee",
             "Men's Cotton Linen Henley Shirt Long Sleeve Hippie Casual Beach T Shirts"]
    metadatas = [{"color":"red", "price":25},
                 {"color":"black", "price":150},
                 {"color":"green", "price":35},
                 {"color":"black", "price":25},
                 {"color":"blue", "price":39},
                 {"color":"green", "price":15}]

    docsearch = AwaDB.from_texts(
            texts=texts, 
            metadatas=metadatas,
            table_name='langchain_awadb_filter')

    #results = docsearch.similarity_search("Men Shirt", meta_filter={"min_price":14, "max_price":36})
    results = docsearch.similarity_search("Men Shirt", text_in_page_content="Pocket", meta_filter={"color":"black"})
    #results = docsearch.similarity_search("Men Shirt", k=5)

    for result in results:
        print(result)
    results = docsearch.similarity_search("Men Shirt", meta_filter={"color":"black"})
    
    for result in results:
        print(result)

def Test_Not_Complete_Fields():
    docs = [
    Document(page_content="A bunch of scientists bring back dinosaurs and mayhem breaks loose", metadata={"year": 1993, "rating": 7.7, "genre": "science fiction"}),
    Document(page_content="Leo DiCaprio gets lost in a dream within a dream within a dream within a ...", metadata={"year": 2010, "director": "Christopher Nolan", "rating": 8.2}),
    Document(page_content="A psychologist / detective gets lost in a series of dreams within dreams within dreams and Inception reused the idea", metadata={"year": 2006, "director": "Satoshi Kon", "rating": 8.6}),
    Document(page_content="A bunch of normal-sized women are supremely wholesome and some men pine after them", metadata={"year": 2019, "director": "Greta Gerwig", "rating": 8.3}),
    Document(page_content="Toys come alive and have a blast doing so", metadata={"year": 1995, "genre": "animated"}),
    Document(page_content="Three men walk into the Zone, three men walk out of the Zone", metadata={"year": 1979, "rating": 9.9, "director": "Andrei Tarkovsky", "genre": "thriller", "rating": 9.9})
]
    docsearch = AwaDB.from_documents(docs, table_name="langchain-self-retriever-demo")

    results = docsearch.similarity_search("What are some movies about dinosaurs")
 
    for result in results:
        print(result)

def Test_Multi_String_Fields():
    docs = [
    Document(
        page_content="A bunch of scientists bring back dinosaurs and mayhem breaks loose",
        metadata={"year": 1993, "rating": 7.7, "genre": ["action", "science fiction"]},
    ),
    Document(
        page_content="Leo DiCaprio gets lost in a dream within a dream within a dream within a ...",
        metadata={"year": 2010, "director": "Christopher Nolan", "rating": 8.2},
    ),
    Document(
        page_content="A psychologist / detective gets lost in a series of dreams within dreams within dreams and Inception reused the idea",
        metadata={"year": 2006, "director": "Satoshi Kon", "rating": 8.6},
    ),
    Document(
        page_content="A bunch of normal-sized women are supremely wholesome and some men pine after them",
        metadata={"year": 2019, "director": "Greta Gerwig", "rating": 8.3},
    ),
    Document(
        page_content="Toys come alive and have a blast doing so",
        metadata={"year": 1995, "genre": "animated"},
    ),
    Document(
        page_content="Three men walk into the Zone, three men walk out of the Zone",
        metadata={
            "year": 1979,
            "rating": 9.9,
            "director": "Andrei Tarkovsky",
            "genre": ["science fiction", "thriller"],
            "rating": 9.9,
        },
    ),
    ]

    docsearch = AwaDB.from_documents(docs, table_name="langchain-multi-string-demo")

    results = docsearch.similarity_search("What are some movies about dinosaurs")
 
    for result in results:
        print(result)




if __name__ == "__main__":
    awadb_client = awadb.Client()
    Test_EmbeddingText(awadb_client)
    Test_Vector1(awadb_client)
    Test_Vector2(awadb_client)
    Test_Load(awadb_client)
    Test_LangChain_Interface(awadb_client)
    Test_LangChain_MMR_Search()
    Test_LangChain_MetaFilter()
    Test_Not_Complete_Fields()
    Test_Multi_String_Fields()
