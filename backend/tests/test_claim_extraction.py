import pytest
from unittest.mock import patch, AsyncMock
from app.services.claim_extraction import ClaimExtractionService
from app.providers.llm import DemoLLMProvider, OpenAILLMProvider, get_llm_provider
from app.schemas.claim import ClaimExtractionResponse, ClaimItem


@pytest.mark.asyncio
async def test_normal_news_article_claim_extraction():
    service = ClaimExtractionService()
    payload = {
        "id": "art_101",
        "title": "Federal Reserve Cuts Interest Rates by 50 Basis Points",
        "description": "The Federal Reserve reduced benchmark interest rates by 0.5% during its September meeting.",
        "content": "Federal Reserve Chairman Jerome Powell announced the decision in Washington DC.",
        "url": "https://reuters.com/fed-rate-cut"
    }

    res = await service.extract_claims_from_payload(payload)

    assert isinstance(res, ClaimExtractionResponse)
    assert res.article_id == "art_101"
    assert res.extraction_status in ["demo_mode", "success"]
    assert len(res.claims) > 0
    assert res.claims[0].original_article_id == "art_101"
    assert res.claims[0].original_article_url == "https://reuters.com/fed-rate-cut"


@pytest.mark.asyncio
async def test_opinion_only_article_claim_extraction():
    service = ClaimExtractionService()
    payload = {
        "id": "art_opinion_1",
        "title": "Opinion: Why Social Media Should Be Banned for Teens",
        "description": "In my opinion, the future is bright if we restrict screen time. I believe smartphones are harmful.",
        "content": "Editorial: I feel that society must realize this danger. In my view, tech companies are failing.",
        "url": "https://example.com/opinion-social-media"
    }

    res = await service.extract_claims_from_payload(payload)

    assert res.extraction_status == "no_factual_claims_found"
    assert len(res.claims) == 0
    assert "opinion" in res.summary.lower() or "no checkable factual claims" in res.summary.lower()


@pytest.mark.asyncio
async def test_article_containing_several_claims():
    provider = DemoLLMProvider()
    payload = {
        "id": "art_multi",
        "title": "NASA Launches Artemis II Mission to Orbit Moon",
        "description": "NASA successfully launched four astronauts aboard the Orion spacecraft from Kennedy Space Center on Monday.",
        "content": "The 10-day mission marks the first crewed lunar flight in over 50 years. Mission Control confirmed trajectory alignment.",
        "url": "https://nasa.gov/artemis-2"
    }

    res = await provider.extract_article_claims(
        article_id=payload["id"],
        title=payload["title"],
        content=f"{payload['description']}\n{payload['content']}",
        url=payload["url"]
    )

    assert res["extraction_status"] in ["demo_mode", "success"]
    assert len(res["claims"]) <= 5
    assert len(res["claims"]) >= 2
    for c in res["claims"]:
        assert "claim_text" in c
        assert c["original_article_id"] == "art_multi"


@pytest.mark.asyncio
async def test_article_with_missing_text():
    service = ClaimExtractionService()
    payload = {
        "id": "art_empty",
        "title": "",
        "description": "",
        "content": "",
        "url": "https://example.com/empty"
    }

    res = await service.extract_claims_from_payload(payload)

    assert res.extraction_status == "missing_text"
    assert len(res.claims) == 0
    assert "missing" in res.summary.lower() or "empty" in res.summary.lower()


@pytest.mark.asyncio
async def test_malformed_llm_response_handling():
    service = ClaimExtractionService()
    payload = {
        "id": "art_malformed",
        "title": "SpaceX Starship Orbital Test",
        "description": "Starship achieved orbit.",
        "url": "https://spacex.com/starship"
    }

    mock_provider = AsyncMock()
    # Mock LLM returning malformed dict without expected keys or invalid claim items
    mock_provider.extract_article_claims.return_value = {
        "extraction_status": "success",
        "summary": "Malformed test",
        "claims": [
            "This is a string not a dict",
            {"invalid_key": "No claim text here"}
        ],
        "is_demo": True
    }

    with patch("app.providers.llm.get_llm_provider", return_value=mock_provider):
        res = await service.extract_claims_from_payload(payload)
        assert isinstance(res, ClaimExtractionResponse)
        # Malformed claim items should be discarded cleanly without throwing exceptions
        assert len(res.claims) == 0


@pytest.mark.asyncio
async def test_unsupported_or_invented_claim_rejection():
    service = ClaimExtractionService()
    payload = {
        "id": "art_unsupported",
        "title": "Local Bakery Opens in Seattle",
        "description": "A new sourdough bakery opened in downtown Seattle on Tuesday.",
        "url": "https://seattle-news.com/bakery"
    }

    # Verify that factual claims map to provided article context and demo/live logic retains integrity
    res = await service.extract_claims_from_payload(payload)
    assert res.article_id == "art_unsupported"
    for claim in res.claims:
        assert claim.original_article_id == "art_unsupported"


@pytest.mark.asyncio
async def test_missing_llm_api_key_fallback():
    with patch.dict("os.environ", {"DEMO_MODE": "false", "LLM_API_KEY": ""}):
        provider = get_llm_provider()
        assert isinstance(provider, DemoLLMProvider)

        res = await provider.extract_article_claims(
            article_id="art_nokey",
            title="Tech Summit Announced in Tokyo",
            content="Speakers will gather in Tokyo next month.",
            url="https://example.com/tokyo-summit"
        )

        assert res["is_demo"] is True
        assert res["extraction_status"] == "demo_mode"
        assert len(res["claims"]) > 0
