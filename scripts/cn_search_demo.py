import os
import json
import requests

BACKEND_URL = 'http://127.0.0.1:8000'
UPLOAD_ENDPOINT = f'{BACKEND_URL}/api/documents/upload'
SEARCH_ENDPOINT = f'{BACKEND_URL}/api/query'

TEST_DOC_REL = os.path.join('tests', '中文测试文档.md')

DOC_CONTENT = """# 中文测试文档

标题：中文搜索功能验证
作者：测试用户
标签：中文, 测试, 搜索
语言：zh-CN

正文内容：

这是一个用于验证检索系统的中文测试文档。文档包含多个与搜索相关的关键词，例如：检索、向量、关键词、混合搜索、最大边际相关性（MMR）。

此外，还包含一些具体的句子，便于关键词匹配：
- 我们正在测试中文内容的检索效果。
- 该系统支持关键词搜索和语义相似度搜索。
- 这是一段包含中文标签和作者信息的元数据示例。

结束语：
希望系统能够正确解析中文文本、生成向量嵌入，并在不同策略下返回合理的搜索结果。
"""


def ensure_test_doc(abs_path: str) -> str:
    if os.path.exists(abs_path):
        return abs_path
    tmp_dir = os.path.join('backend', 'data', 'uploads')
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, 'cn_test_doc.md')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(DOC_CONTENT)
    return tmp_path


def upload_cn_doc():
    project_root = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.abspath(os.path.join(project_root, TEST_DOC_REL))
    file_path = ensure_test_doc(file_path)

    metadata = {
        'author': '测试用户',
        'title': '中文搜索功能验证',
        'description': '用于验证中文检索与元数据显示',
        'source': '本地测试',
        'language': 'zh-CN',
        'tags': ['中文', '测试', '搜索']
    }
    data = {
        'metadata': json.dumps(metadata, ensure_ascii=False),
        'tags': '中文,测试,搜索',
        'language': 'zh-CN',
        'auto_process': 'true'
    }

    # 使用兼容字段 `file`，避免 FastAPI 列表校验错误
    with open(file_path, 'rb') as f:
        files = {
            'file': (os.path.basename(file_path), f, 'text/markdown')
        }
        resp = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=60)

    print('上传状态码:', resp.status_code)
    try:
        print('上传响应:', resp.json())
    except Exception:
        print('上传响应文本:', resp.text[:500])
    if resp.status_code not in (200, 201):
        raise RuntimeError('上传失败')


def search_cn_doc():
    strategies = ['similarity', 'keyword', 'hybrid', 'mmr']
    # 使用更贴近文档的完整中文句子，提高匹配概率
    query = '该系统支持关键词搜索和语义相似度搜索。'
    for strat in strategies:
        payload = {
            'query': query,
            'strategy': strat,
            'top_k': 5,
            'threshold': 0.0,  # 放宽相似度阈值，避免被过滤掉
            # 首轮不加过滤器，观察基础命中情况
            'include_metadata': True
        }
        print(f"\n=== 策略: {strat} ===")
        resp = requests.post(SEARCH_ENDPOINT, json=payload, timeout=60)
        print('搜索状态码:', resp.status_code)
        data = resp.json()
        print('总结果数:', data.get('total_results'))
        for i, item in enumerate(data.get('results', [])[:5], 1):
            title = item.get('title') or '(无标题)'
            score = item.get('score')
            metadata = item.get('metadata') or {}
            author = metadata.get('author') or metadata.get('作者')
            tags = metadata.get('tags') or metadata.get('标签')
            print(f"{i}. 标题: {title} | 分数: {score}")
            print(f"   作者: {author} | 标签: {tags}")
            snippet = (item.get('content') or '')
            print(f"   内容片段: {snippet[:80]}")


def main():
    # 健康检查
    try:
        h = requests.get(f'{BACKEND_URL}/health').json()
        print('健康检查:', h)
    except Exception as e:
        print('健康检查失败:', e)
    upload_cn_doc()
    search_cn_doc()


if __name__ == '__main__':
    main()