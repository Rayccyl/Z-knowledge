# Z-knowledge
[https://github.com/langgenius/dify](Dify)是一款开源零代码AI应用搭建工具,其自带了知识库功能,可以通过pdf txt等多种定义了一种接入外部支持库的格式[](https://docs.dify.ai/guides/knowledge-base/external-knowledge-api-documentation),然而,默认情况下上传到知识库的文件最大只能是15MB,这不符合需要读较大pdf的用户的需求。因此,本项目期望提供一个从Zotero到Dify的外部知识库接口,使得Dify知识库可以access到您的Zotero library中大量的文献.目前的定位是本地或局域网内运行。
## the following opensource models , packages and SDKs is used
[pyzotero](https://github.com/urschrei/pyzotero)
[pymongo](https://github.com/mongodb/mongo-python-driver)
[pymilvus](https://github.com/milvus-io/pymilvus)
[MinerU](https://github.com/opendatalab/MinerU)
[M3ebase-embedding](https://huggingface.co/moka-ai/m3e-base)
[langchain_text_splitters](https://github.com/langchain-ai/langchain)
[Fastapi](https://github.com/fastapi/fastapi)
## Requirement
需要安装MongoDB 及上述包,环境配置有些复杂,建议用conda,其中MinerU要求python=3.10
## Tips
如果一切依赖成功安装 可以在目录下`uvicorn main:app --host 0.0.0.0 --port 8000`而后发送如下请求来模拟Dify端
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/retrieval/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer {your zotero api key}' \
  -d '{
  "knowledge_id": "{user/group}&{userId or groupId}",
  "query": "What is RAG",
  "retrieval_setting": {
    "top_k": 3,
    "score_threshold": 0.75
  }
}'
```
[zotero api key&userId](https://www.zotero.org/settings/keys)

## Todo
这是项目的demo版0.0.1,尚有很多问题,如
1. 尚未docker化
2. **[BUG]**因为检索速度过慢,导致dify.ai获取信息超时
![image](https://github.com/user-attachments/assets/9ffe4956-087a-4aab-83bf-3a959071725d)
按上述curl POST查询时在一段时间等待后能正常返回数据。先前开发过程中做最小可运行实例,返回固定值时也能与Dify.ai正常交互,因此考虑是检索时间超时导致。
![image](https://github.com/user-attachments/assets/f811a1c0-31f1-48ae-b420-89a020f51a54)  
(172.18.0.3是本地部署的Dify,127.0.0.1是curl POST)
4. 首次POST查询时会连接到zotero服务器获取你的pdf(暂不支持其他格式),并将其转化为markdown,而后再存向量数据库+查询,因此时间很长,未来应该改进为,在部署本api而未收到POST时就提前进行这些步骤.
5. 加入LOG
6. etc  

如果对本项目您能提供帮助欢迎PR  
本人双非本科非科班(信息管理与信息系统)在读,能力有限,2025.10保研上岸之后有时间可能会做进一步改进(10月之前有点忙估计挤不出时间).

