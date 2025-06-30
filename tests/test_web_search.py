"""
Web search tests
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tool.web_search import SearchProvider, SearchResult, WebSearch


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


@pytest.fixture
def web_search():
    """Create web search instance"""
    return WebSearch()


@pytest.mark.asyncio
async def test_google_search(web_search, mock_google_response):
    """Test Google search"""
    with patch("googlesearch_python.search", return_value=mock_google_response):
        results = await web_search.search("test query", provider=SearchProvider.GOOGLE)

        assert len(results) == 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.title for result in results)
        assert all(result.url for result in results)
        assert all(result.snippet for result in results)


@pytest.mark.asyncio
async def test_bing_search(web_search, mock_bing_response):
    """Test Bing search"""
    with patch(
        "app.tool.web_search.WebSearch._make_bing_request",
        return_value=mock_bing_response,
    ):
        results = await web_search.search("test query", provider=SearchProvider.BING)

        assert len(results) == 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.title for result in results)
        assert all(result.url for result in results)
        assert all(result.snippet for result in results)


@pytest.mark.asyncio
async def test_duckduckgo_search(web_search, mock_duckduckgo_response):
    """Test DuckDuckGo search"""
    with patch("duckduckgo_search.ddg", return_value=mock_duckduckgo_response):
        results = await web_search.search(
            "test query", provider=SearchProvider.DUCKDUCKGO
        )

        assert len(results) == 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.title for result in results)
        assert all(result.url for result in results)
        assert all(result.snippet for result in results)


@pytest.mark.asyncio
async def test_empty_results(web_search):
    """Test handling of empty search results"""
    with patch("googlesearch_python.search", return_value=[]):
        results = await web_search.search("test query", provider=SearchProvider.GOOGLE)
        assert len(results) == 0


@pytest.mark.asyncio
async def test_error_handling(web_search):
    """Test error handling"""
    with patch("googlesearch_python.search", side_effect=Exception("Search error")):
        with pytest.raises(Exception):
            await web_search.search("test query", provider=SearchProvider.GOOGLE)


@pytest.mark.asyncio
async def test_invalid_provider(web_search):
    """Test handling of invalid search provider"""
    with pytest.raises(ValueError):
        await web_search.search("test query", provider="invalid")


@pytest.mark.asyncio
async def test_result_deduplication(web_search, mock_google_response):
    """Test result deduplication"""
    duplicate_response = mock_google_response + mock_google_response

    with patch("googlesearch_python.search", return_value=duplicate_response):
        results = await web_search.search("test query", provider=SearchProvider.GOOGLE)
        assert len(results) == 2  # Duplicates should be removed


@pytest.mark.asyncio
async def test_result_filtering(web_search):
    """Test result filtering"""
    spam_response = [
        {
            "title": "Buy cheap products!",
            "link": "http://spam.com",
            "snippet": "Advertisement spam content",
        }
    ]

    with patch("googlesearch_python.search", return_value=spam_response):
        results = await web_search.search("test query", provider=SearchProvider.GOOGLE)
        assert len(results) == 0  # Spam results should be filtered out


@pytest.mark.asyncio
async def test_result_sorting(web_search, mock_google_response):
    """Test result sorting by relevance"""
    unsorted_response = [
        {
            "title": "Less Relevant",
            "link": "http://test3.com",
            "snippet": "Unrelated content",
        }
    ] + mock_google_response

    with patch("googlesearch_python.search", return_value=unsorted_response):
        results = await web_search.search("test query", provider=SearchProvider.GOOGLE)
        assert results[0].title == "Test Result 1"  # Most relevant should be first


@pytest.mark.asyncio
async def test_concurrent_searches(
    web_search, mock_google_response, mock_bing_response
):
    """Test concurrent searches from multiple providers"""
    with patch("googlesearch_python.search", return_value=mock_google_response), patch(
        "app.tool.web_search.WebSearch._make_bing_request",
        return_value=mock_bing_response,
    ):
        results = await web_search.search(
            "test query", provider=[SearchProvider.GOOGLE, SearchProvider.BING]
        )
        assert len(results) == 4  # Combined results from both providers


@pytest.mark.asyncio
async def test_rate_limiting(web_search, mock_google_response):
    """Test rate limiting"""
    with patch("googlesearch_python.search", return_value=mock_google_response):
        # Make multiple requests in quick succession
        for _ in range(5):
            results = await web_search.search(
                "test query", provider=SearchProvider.GOOGLE
            )
            assert len(results) == 2  # Should still work despite rate limiting


@pytest.mark.asyncio
async def test_timeout_handling(web_search):
    """Test timeout handling"""
    with patch("googlesearch_python.search", side_effect=TimeoutError):
        with pytest.raises(TimeoutError):
            await web_search.search("test query", provider=SearchProvider.GOOGLE)


@pytest.mark.asyncio
async def test_result_caching(web_search, mock_google_response):
    """Test result caching"""
    with patch(
        "googlesearch_python.search", return_value=mock_google_response
    ) as mock_search:
        # First request
        await web_search.search("test query", provider=SearchProvider.GOOGLE)
        # Second request with same query
        await web_search.search("test query", provider=SearchProvider.GOOGLE)

        assert (
            mock_search.call_count == 1
        )  # Should use cached results for second request
