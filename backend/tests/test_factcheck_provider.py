import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from app.providers.factcheck import GoogleFactCheckProvider, DemoFactCheckProvider, get_factcheck_provider
from app.services.factcheck_search import FactCheckSearchService


@pytest.mark.asyncio
async def test_relevant_existing_fact_check():
    provider = GoogleFactCheckProvider()
    provider.api_key = "test_valid_key"

    mock_response_data = {
        "claims": [
            {
                "text": "The moon is made of green cheese",
                "claimant": "Viral Tweet",
                "claimDate": "2026-01-01T00:00:00Z",
                "claimReview": [
                    {
                        "publisher": {"name": "FactCheck.org", "site": "factcheck.org"},
                        "url": "https://www.factcheck.org/2026/01/moon-cheese-claim",
                        "title": "No, the moon is not made of cheese",
                        "reviewDate": "2026-01-02T00:00:00Z",
                        "textualRating": "False"
                    }
                ]
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await provider.search_claims("moon green cheese")

        assert res["status"] == "success"
        assert res["total_results"] == 1
        assert res["results"][0]["matched_claim_text"] == "The moon is made of green cheese"
        assert res["results"][0]["claimant"] == "Viral Tweet"
        assert res["results"][0]["reviews"][0]["publisher_name"] == "FactCheck.org"
        assert res["results"][0]["reviews"][0]["textual_rating"] == "False"
        assert res["results"][0]["reviews"][0]["review_url"] == "https://www.factcheck.org/2026/01/moon-cheese-claim"


@pytest.mark.asyncio
async def test_no_matching_result():
    provider = GoogleFactCheckProvider()
    provider.api_key = "test_valid_key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"claims": []}

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await provider.search_claims("unprecedented obscure query 12345")

        assert res["status"] == "no_results_found"
        assert res["total_results"] == 0
        assert len(res["results"]) == 0


@pytest.mark.asyncio
async def test_similar_but_contextually_different_claim():
    provider = GoogleFactCheckProvider()
    provider.api_key = "test_valid_key"

    # Claim returned by API is textually overlapping, but context/word match ratio is evaluated
    mock_response_data = {
        "claims": [
            {
                "text": "Unrelated topic completely different keywords",
                "claimReview": [
                    {
                        "publisher": {"name": "Snopes"},
                        "url": "https://snopes.com/unrelated",
                        "textualRating": "Unproven"
                    }
                ]
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await provider.search_claims("quantum computer semiconductor breakthrough")

        assert res["status"] == "success"
        assert len(res["results"]) == 1
        # Check context match flag evaluates to False due to low query word overlap
        assert res["results"][0]["context_match"] is False


@pytest.mark.asyncio
async def test_api_authentication_failure():
    provider = GoogleFactCheckProvider()
    provider.api_key = "test_invalid_key"

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "API Key Invalid"

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await provider.search_claims("some claim")

        assert res["status"] == "auth_failure"
        assert res["total_results"] == 0


@pytest.mark.asyncio
async def test_rate_limiting_and_timeout():
    provider = GoogleFactCheckProvider()
    provider.api_key = "test_valid_key"

    # 1. Rate Limiting (429)
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp_429
        res_429 = await provider.search_claims("claim")
        assert res_429["status"] == "rate_limited"

    # 2. Timeout Error
    with patch.object(httpx.AsyncClient, "get", side_effect=httpx.TimeoutException("Connection timed out")):
        res_timeout = await provider.search_claims("claim")
        assert res_timeout["status"] == "timeout_error"


@pytest.mark.asyncio
async def test_malformed_response():
    provider = GoogleFactCheckProvider()
    provider.api_key = "test_valid_key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON token")

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await provider.search_claims("claim")

        assert res["status"] == "error"
        assert "Malformed" in res["summary"] or "JSON" in res["summary"]


@pytest.mark.asyncio
async def test_missing_api_key():
    with patch.dict("os.environ", {"DEMO_MODE": "false", "GOOGLE_FACTCHECK_API_KEY": ""}):
        provider = GoogleFactCheckProvider()

        res = await provider.search_claims("claim")

        assert res["status"] == "missing_api_key"
        assert res["total_results"] == 0
        assert "No GOOGLE_FACTCHECK_API_KEY" in res["summary"]


@pytest.mark.asyncio
async def test_factcheck_search_service():
    service = FactCheckSearchService()

    with patch.dict("os.environ", {"DEMO_MODE": "true"}):
        res = await service.search_claim_factchecks("climate change targets")
        assert res.query == "climate change targets"
        assert res.is_demo is True
        assert res.total_results > 0
        assert res.results[0].reviews[0].publisher_name == "FactCheck.org"
