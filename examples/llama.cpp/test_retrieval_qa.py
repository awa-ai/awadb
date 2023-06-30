from langchain.document_loaders import TextLoader
from langchain.prompts import PromptTemplate

from langchain.vectorstores import AwaDB
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import LlamaCpp
from langchain.chains import RetrievalQA

import time

# 1: 加载本地关于《流浪地球2》的电影介绍文章
documents = TextLoader("./data/liulangdiqiu.txt", encoding="utf-8").load()

# 2: 对文章按每70个字符做切分，同时AwaDB默认会对每70个字符的文本片段执行embedding成语义向量的操作，写入指定表langchain_awadb_qa
docsearch = AwaDB.from_documents(RecursiveCharacterTextSplitter(chunk_size=70, chunk_overlap=0, keep_separator=False).split_documents(documents), table_name='langchain_awadb_qa')

# 3-6: 自定义上下文问答提示词模版
prompt_template = """使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。{context}
问题: {question}
答案:"""
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# 7: langchain内置的问答检索类链式调用。大模型基于Llama系列中斯坦福微调的Alpaca-7b，并通过中文数据微调，最后经llama.cpp量化压缩到原始大小的1/8。
#    LlamaCpp类中的model_path请设置为本地经过量化后的实际大模型地址
qa = RetrievalQA.from_chain_type(llm=LlamaCpp(model_path="../models/alpaca_chinese_lora_7b/ggml-model-q4_0.bin", n_ctx=2048, temperature=0), chain_type="stuff", retriever=docsearch.as_retriever(), chain_type_kwargs={"prompt": PROMPT})

# 8: 问答检索类链式调用执行对应的问题推理，并返回答案
qa.run("流浪地球讲的什么故事?")


start = time.time()
query = "流浪地球讲的什么故事?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))

start = time.time()
query = "太空电梯是什么?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))

start = time.time()
query = "地球能逃出太阳系以外吗?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))

start = time.time()
query = "流浪地球电影中主要角色是哪几个?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))

start = time.time()
query = "流浪地球作者是谁?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))


start = time.time()
query = "流浪地球票房怎么样?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))

start = time.time()
query = "流浪地球值得看吗?"
print("问题: %s" % query)
print("答案:%s" % qa.run(query))
end = time.time()
print("耗时: %f秒\n" % (end - start))
