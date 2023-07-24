# -*- coding: utf-8 -*-
# !/usr/bin/python3
import pytest
import awadb
from langchain.vectorstores import AwaDB
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

def Test_EmbeddingText(awadb_client):
    """
       Test the ability to add text embedded data to awadb and search for it.

       Args:
           awadb_client: awadb client object.

       Returns:
           A list of search results.
       """

    awadb_client.Create("test_llm2")

    sentences_set = ["The man is happy", "The man is very happy", "The cat is happy", "The man is eating"]

    awadb_client.Add([{'embedding_text': 'The man is happy'}, {'source': 'pic1'}])
    awadb_client.Add([{'embedding_text': 'The man is very happy'}, {'source': 'pic2'}])
    awadb_client.Add([{'embedding_text': 'The cat is happy'}, {'source': 'pic3'}])
    awadb_client.Add(['The man is eating', 'pic4'])

    query = "The man is happy"

    results = awadb_client.Search(query, 3)
    return results


def Test_Vector1(awadb_client):
    """
        Test the functionality to add vector data to awadb and search for it.

        Args:
            awadb_client: awadb client object.

        Returns:
            A list of search results.
        """
    awadb_client.Create("testdb3")
    awadb_client.Add(
        [{'primary': '123'}, {'name': 'lj'}, {'gender': 'male'}, {'age': 39}, 'hello', 'world', [1, 3.5, 3]])
    awadb_client.Add(
        [{'primary': '235'}, {'name': 'hu'}, {'gender': 'male'}, {'age': 28}, 'what', 'doing', [1, 3.4, 2]])
    awadb_client.Add([{'primary': '398'}, {'name': 'er'}, {'gender': 'female'}, {'age': 45}, 'yu', 'hi', [1, 2.4, 4]])
    awadb_client.Add(
        [{'primary': '345'}, {'name': 'hehe'}, {'gender': 'female'}, {'age': 25}, 'hhuhu', 'hello', [1.3, 2.9, 8.9]])

    doc1 = awadb_client.Get('1')


    result = awadb_client.Search([3.0, 3.1, 4.2], 3)

    query = [3.0, 3.1, 4.2]

    return result



def Test_Vector2(awadb_client):
    """
        Test the functionality of adding vector data to awadb.

        Args:
            awadb_client: awadb client object.

        Returns:
            Add the result of the document.
        """
    awadb_client.Create("testdb10")
    awadb_client.Add(
        [{'primary': '298'}, {'name': 'lv'}, {'gender': 'male'}, {'age': 39}, 'hello', 'world', [1, 3.5, 3]])
    return awadb_client.Add(
        [{'primary': '209'}, {'name': 'ho'}, {'gender': 'male'}, {'age': 28}, 'what', 'doing', [1, 3.4, 2]])

def Test_Load(awadb_client):
    """
        Test the functionality of loading the awadb database.

        Args:
            awadb_client: awadb client object.

        Returns:
            The result of loading the database (Boolean).
        """
    ret = awadb_client.Load('testdb3')
    if ret:
        print('awadb load table success')
    else:
        print('awadb load table failed')
    return ret



def Test_LangChain_Interface(awadb_client):
    awadb_client.Create("test_langchain")

    texts = ["lion", "tiger", "tree", "flower", "frog", "elephant", "cabbage"]
    ids = awadb_client.AddTexts("embedding_text", "text_embedding", texts=texts)

    not_include_fields: Set[str] = {"text_embedding"}
    result = awadb_client.Search(query="giraffe", topn=3, not_include_fields=not_include_fields)


    keys1: List[str] = []
    keys2: List[str] = []
    i = 0
    for item_id in ids:
        if i < 3:
            keys1.append(item_id)
        if i >= 5:
            keys2.append(item_id)
        i = i + 1


    not_pack_fields: Set[str] = {"text_embedding"}
    show1 = awadb_client.Get(ids=keys1, not_include_fields=not_pack_fields)
    awadb_client.Delete(keys1)
    show2 = awadb_client.Get(ids=keys1, not_include_fields=not_pack_fields)


    awadb_client.UpdateTexts(ids=keys2, text_field_name="embedding_text", texts=["dolphine", "rose"])

    show3 = awadb_client.Get(keys2, not_include_fields=not_pack_fields)

    return [keys1,keys2,show2,show3]


def Test_LangChain_MMR_Search():
    """
        Test LangChain's ability to search using the MMR algorithm.

        Returns:
            A list of multiple results, including page content for MMR search results and similarity search results.
        """
    documents = TextLoader("state_of_the_union.txt", encoding="utf-8").load()

    docsearch = AwaDB.from_documents(
        RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=0, keep_separator=False)
        .split_documents(documents), table_name='langchain_awadb_qa')

    results = docsearch.max_marginal_relevance_search("What is the purpose of the NATO Alliance?")

    s_results = docsearch.similarity_search("What is the purpose of the NATO Alliance?")

    return [results[0].page_content,results[1].page_content,results[2].page_content,s_results[0].page_content,s_results[1].page_content,s_results[2].page_content]

def Test_LangChain_MetaFilter():
    texts = ["Men's Regular-Fit Cotton Pique Polo Shirt (Available in Big & Tall)",
             "It's Weird Being The Same Age As Old People Sarcastic Retro T-Shirt",
             "I Have Selective Hearing You Weren't Selected Today T-Shirt",
             "Men's Loose Fit Heavyweight Short-Sleeve Pocket T-Shirt",
             "Men's Essentials Camouflage Print Tee",
             "Men's Cotton Linen Henley Shirt Long Sleeve Hippie Casual Beach T Shirts"]
    metadatas = [{"color": "red", "price": 25},
                 {"color": "black", "price": 150},
                 {"color": "green", "price": 35},
                 {"color": "black", "price": 25},
                 {"color": "blue", "price": 39},
                 {"color": "green", "price": 15}]

    docsearch = AwaDB.from_texts(
        texts=texts,
        metadatas=metadatas,
        table_name='langchain_awadb_filter')

    # results1 = docsearch.similarity_search("Men Shirt", meta_filter={"min_price":14, "max_price":36})
    results1 = docsearch.similarity_search("Men Shirt", text_in_page_content="Pocket", meta_filter={"color": "black"})
    # results1 = docsearch.similarity_search("Men Shirt", k=5)

    results2 = docsearch.similarity_search("Men Shirt", meta_filter={"color": "black"})
    
    return [results1[0].page_content,results1[1].page_content,results1[2].page_content,results1[3].page_content,results2[0].page_content,results2[1].page_content,results2[2].page_content,results2[3].page_content,]
def test_EmbeddingText():
    """
        Test the Test_EmbeddingText function.

        Load the expected results from the file and compare them with the actual results.

        Raises:
            AssertionError: If the actual result does not match the expected result.

        Returns:
            None
        """
    awadb_client = awadb.Client()
    with open('./test_EmbeddingText.txt', "r") as file:
        t = json.load(file)
    result=Test_EmbeddingText(awadb_client)
    assert result==t


def test_Vector1():
    """
       Test the Test_Vector1 function.

       Load the expected results from the file and compare them with the actual results.

       Raises:
            AssertionError: If the actual result does not match the expected result.

       Returns:
           None
       """
    awadb_client = awadb.Client()
    with open('test_Vector1.txt', "r") as file:
        t = json.load(file)
    result=Test_Vector1(awadb_client)
    assert result==t

def test_Vector2():
    """
        Test the Test_Vector2 function.

        Test the function and assert that the return value is true.

        Raises:
            AssertionError: If the return value is not true.

        Returns:
            None
        """
    awadb_client = awadb.Client()
    t=True
    result=Test_Vector2(awadb_client)
    assert result==t


def test_LangChain_Interface():
    """
       Test the Test_LangChain_Interface function.

       Load the expected results from the file and compare them with the actual results.

       Raises:
           AssertionError: If the actual result does not match the expected result.

       Returns:
           None
       """
    awadb_client = awadb.Client()
    t=[['6b42d00c4ca6ddc33a604c54b8ce4adc', '43b90920409618f188bfc6923f16b9fa', 'c0af77cf8294ff93a5cdb2963ca9f038'],['e4b48fd541b3dcb99cababc87c2ee88f', 'b3188adab3f07e66582bbac456dcd212'],[],[{'_id': 'e4b48fd541b3dcb99cababc87c2ee88f', 'embedding_text': 'dolphine'}, {'_id': 'b3188adab3f07e66582bbac456dcd212', 'embedding_text': 'rose'}]]
    result=Test_LangChain_Interface(awadb_client)
    assert result==t


def test_Load():
    """
        Test the Test_Load function.

        Test the function and assert that the return value is true.

        Raises:
            AssertionError: If the return value is not true.

        Returns:
            None
        """
    awadb_client = awadb.Client()
    t=True
    result=Test_Load(awadb_client)
    assert result==t


def test_LangChain_MMR_Search():
    """
        Test the Test_LangChain_MMR_Search function.

        Load the expected results from the file and compare them with the actual results.

        Raises:
            AssertionError: If the actual result does not match the expected result.

        Returns:
            None
        """
    with open("test_LangChain_MMR_Search.txt", "r") as file:
        t = [line.strip().replace("\\n", "\n") for line in file]
    result=Test_LangChain_MMR_Search()
    assert result==t


def test_LangChain_MetaFilter():
    """
        Test the Test_LangChain_MetaFilter function.

        Load the expected results from the file and compare them with the actual results.

        Raises:
            AssertionError: If the actual result does not match the expected result.

        Returns:
            None
        """
    with open("test_LangChain_MetaFilter.txt", "r") as file:
        t = [line.strip() for line in file]
    result=Test_LangChain_MetaFilter()
    assert result==t
