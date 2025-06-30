"""
Search tools tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tool.search.baidu_search import BaiduSearchTool
from app.tool.search.base import BaseSearchTool
from app.tool.search.bing_search import BingSearchTool
from app.tool.search.duckduckgo_search import DuckDuckGoSearchTool
from app.tool.search.google_search import GoogleSearchTool


class TestSearchTool(BaseSearchTool):
    """Test search tool implementation"""

    async def search(self, query: str) -> list[dict]:
        return [
            {
                "title": "Test Result",
                "link": "http://test.com",
                "snippet": "Test snippet",
            }
        ]


@pytest.fixture
def mock_google_response():
    """Mock Google search response"""
    return [
        {
            "title": "Test Result 1",
            "link": "http://test1.com",
            "snippet": "Test snippet 1",
        },
        {
            "title": "Test Result 2",
            "link": "http://test2.com",
            "snippet": "Test snippet 2",
        },
    ]


@pytest.fixture
def mock_bing_response():
    """Mock Bing search response"""
    return {
        "webPages": {
            "value": [
                {
                    "name": "Test Result 1",
                    "url": "http://test1.com",
                    "snippet": "Test snippet 1",
                },
                {
                    "name": "Test Result 2",
                    "url": "http://test2.com",
                    "snippet": "Test snippet 2",
                },
            ]
        }
    }


@pytest.fixture
def mock_baidu_response():
    """Mock Baidu search response"""
    return [
        {
            "title": "Test Result 1",
            "url": "http://test1.com",
            "abstract": "Test snippet 1",
        },
        {
            "title": "Test Result 2",
            "url": "http://test2.com",
            "abstract": "Test snippet 2",
        },
    ]


@pytest.fixture
def mock_duckduckgo_response():
    """Mock DuckDuckGo search response"""
    return [
        {
            "title": "Test Result 1",
            "link": "http://test1.com",
            "snippet": "Test snippet 1",
        },
        {
            "title": "Test Result 2",
            "link": "http://test2.com",
            "snippet": "Test snippet 2",
        },
    ]


def test_base_search_tool():
    """Test base search tool"""
    tool = TestSearchTool()
    assert isinstance(tool, BaseSearchTool)


@pytest.mark.asyncio
async def test_google_search(mock_google_response):
    """Test Google search"""
    with patch("googlesearch_python.search", return_value=mock_google_response):
        tool = GoogleSearchTool()
        results = await tool.search("test query")

        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)
        assert all("title" in result for result in results)
        assert all("link" in result for result in results)
        assert all("snippet" in result for result in results)


@pytest.mark.asyncio
async def test_bing_search(mock_bing_response):
    """Test Bing search"""
    with patch(
        "app.tool.search.bing_search.BingSearchTool._make_request",
        return_value=mock_bing_response,
    ):
        tool = BingSearchTool()
        results = await tool.search("test query")

        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)
        assert all("title" in result for result in results)
        assert all("link" in result for result in results)
        assert all("snippet" in result for result in results)


@pytest.mark.asyncio
async def test_baidu_search(mock_baidu_response):
    """Test Baidu search"""
    with patch("baidusearch.search", return_value=mock_baidu_response):
        tool = BaiduSearchTool()
        results = await tool.search("test query")

        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)
        assert all("title" in result for result in results)
        assert all("link" in result for result in results)
        assert all("snippet" in result for result in results)


@pytest.mark.asyncio
async def test_duckduckgo_search(mock_duckduckgo_response):
    """Test DuckDuckGo search"""
    with patch("duckduckgo_search.ddg", return_value=mock_duckduckgo_response):
        tool = DuckDuckGoSearchTool()
        results = await tool.search("test query")

        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)
        assert all("title" in result for result in results)
        assert all("link" in result for result in results)
        assert all("snippet" in result for result in results)


@pytest.mark.asyncio
async def test_empty_results():
    """Test handling of empty search results"""
    with patch("googlesearch_python.search", return_value=[]):
        tool = GoogleSearchTool()
        results = await tool.search("test query")
        assert results == []


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in search tools"""
    with patch("googlesearch_python.search", side_effect=Exception("Search error")):
        tool = GoogleSearchTool()
        with pytest.raises(Exception):
            await tool.search("test query")


@pytest.mark.asyncio
async def test_result_formatting():
    """Test search result formatting"""
    tool = TestSearchTool()
    results = await tool.search("test query")

    assert isinstance(results, list)
    assert len(results) == 1
    assert "title" in results[0]
    assert "link" in results[0]
    assert "snippet" in results[0]


@pytest.mark.asyncio
async def test_query_validation():
    """Test query validation"""
    tool = TestSearchTool()

    with pytest.raises(ValueError):
        await tool.search("")  # Empty query

    with pytest.raises(ValueError):
        await tool.search("   ")  # Whitespace only query
