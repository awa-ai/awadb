一、LLaMa系列开源大模型Alpaca经过中文LoRA微调后的大语言模型
LLaMa系列Alpaca中文微调相关项目链接：https://github.com/ymcui/Chinese-LLaMA-Alpaca
HuggingFace相关大模型链接：https://huggingface.co/shibing624/chinese-alpaca-plus-7b-hf
注意目前由于Meta对LLaMa开源大模型禁止商用，请遵守其约束条款

二、llama.cpp下载后，编译运行，并将选择的大语言模型量化精简后部署运行
按llama.cpp项目说明将大语言模型参数量化为4比特，压缩为原始大模型的1/8即可
llama.cpp项目地址：https://github.com/ggerganov/llama.cpp

三、安装langchain与awadb：pip install langchain && pip install awadb
langchain项目地址: https://github.com/hwchase17/langchain
awadb项目地址: https://github.com/awa-ai/awadb
