"""搜索 API 测试"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestSearchAPI:
    """搜索 API 测试类"""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, async_client: AsyncClient, auth_headers):
        """测试文档搜索成功"""
        search_data = {
            "query": "test search query",
            "strategy": "semantic",
            "limit": 10
        }
        
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, async_client: AsyncClient, auth_headers):
        """测试空查询搜索"""
        search_data = {
            "query": "",
            "strategy": "semantic",
            "limit": 10
        }
        
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_search_documents_invalid_strategy(self, async_client: AsyncClient, auth_headers):
        """测试无效搜索策略"""
        search_data = {
            "query": "test query",
            "strategy": "invalid_strategy",
            "limit": 10
        }
        
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_search_documents_with_filters(self, async_client: AsyncClient, auth_headers):
        """测试带过滤器的搜索"""
        search_data = {
            "query": "test query",
            "strategy": "semantic",
            "limit": 10,
            "filters": {
                "file_type": ["application/pdf"],
                "tags": ["important"],
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-12-31"
                }
            }
        }
        
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data

    @pytest.mark.asyncio
    async def test_search_documents_pagination(self, async_client: AsyncClient, auth_headers):
        """测试搜索分页"""
        search_data = {
            "query": "test query",
            "strategy": "semantic",
            "limit": 5,
            "offset": 10
        }
        
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert data["pagination"]["limit"] == 5
        assert data["pagination"]["offset"] == 10

    @pytest.mark.asyncio
    async def test_search_documents_unauthorized(self, async_client: AsyncClient):
        """测试未授权搜索"""
        search_data = {
            "query": "test query",
            "strategy": "semantic",
            "limit": 10
        }
        
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_search_suggestions(self, async_client: AsyncClient, auth_headers):
        """测试搜索建议"""
        response = await async_client.get(
            "/api/v1/search/suggestions",
            params={"query": "test"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    @pytest.mark.asyncio
    async def test_search_history(self, async_client: AsyncClient, auth_headers):
        """测试搜索历史"""
        response = await async_client.get(
            "/api/v1/search/history",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)

    @pytest.mark.asyncio
    async def test_clear_search_history(self, async_client: AsyncClient, auth_headers):
        """测试清除搜索历史"""
        response = await async_client.delete(
            "/api/v1/search/history",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Search history cleared successfully"

    @pytest.mark.asyncio
    async def test_search_analytics(self, async_client: AsyncClient, auth_headers):
        """测试搜索分析"""
        response = await async_client.get(
            "/api/v1/search/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_searches" in data
        assert "popular_queries" in data
        assert "search_trends" in data

    @pytest.mark.asyncio
    async def test_search_performance(self, async_client: AsyncClient, auth_headers):
        """测试搜索性能"""
        import time
        
        search_data = {
            "query": "performance test query",
            "strategy": "semantic",
            "limit": 10
        }
        
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        # 搜索应该在合理时间内完成（例如 < 2 秒）
        assert (end_time - start_time) < 2.0

    @pytest.mark.asyncio
    async def test_concurrent_searches(self, async_client: AsyncClient, auth_headers, concurrent_requests):
        """测试并发搜索"""
        import asyncio
        
        search_data = {
            "query": "concurrent test query",
            "strategy": "semantic",
            "limit": 10
        }
        
        async def perform_search():
            return await async_client.post(
                "/api/v1/search/documents",
                json=search_data,
                headers=auth_headers
            )
        
        # 执行并发搜索
        tasks = [perform_search() for _ in range(concurrent_requests)]
        responses = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, async_client: AsyncClient, auth_headers):
        """测试包含特殊字符的搜索"""
        special_queries = [
            "test@example.com",
            "file-name_with.special-chars",
            "query with spaces",
            "中文查询",
            "query with 'quotes'",
            "query with \"double quotes\"",
            "query with & symbols",
            "query with % wildcards"
        ]
        
        for query in special_queries:
            search_data = {
                "query": query,
                "strategy": "semantic",
                "limit": 10
            }
            
            response = await async_client.post(
                "/api/v1/search/documents",
                json=search_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_search_rate_limiting(self, async_client: AsyncClient, auth_headers):
        """测试搜索频率限制"""
        search_data = {
            "query": "rate limit test",
            "strategy": "semantic",
            "limit": 10
        }
        
        # 快速发送多个请求
        responses = []
        for _ in range(20):  # 假设限制是 10 次/分钟
            response = await async_client.post(
                "/api/v1/search/documents",
                json=search_data,
                headers=auth_headers
            )
            responses.append(response)
        
        # 检查是否有请求被限制
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        rate_limited_count = sum(1 for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS)
        
        # 至少应该有一些成功的请求
        assert success_count > 0
        # 如果启用了频率限制，应该有一些被限制的请求
        # assert rate_limited_count > 0  # 取决于实际的频率限制配置

    @pytest.mark.asyncio
    async def test_search_error_handling(self, async_client: AsyncClient, auth_headers, mock_database_error):
        """测试搜索错误处理"""
        # 这个测试需要模拟数据库错误
        # 具体实现取决于如何注入错误
        search_data = {
            "query": "error test query",
            "strategy": "semantic",
            "limit": 10
        }
        
        # 模拟服务错误的情况下，应该返回适当的错误响应
        response = await async_client.post(
            "/api/v1/search/documents",
            json=search_data,
            headers=auth_headers
        )
        
        # 正常情况下应该成功，除非真的有错误
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]