import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.credibility import CredibilityVerificationService, SourceRating

@pytest.fixture
def service():
    return CredibilityVerificationService()

def test_extract_domain(service):
    assert service.extract_domain("https://www.bbc.com/news/world-12345") == "bbc.com"
    assert service.extract_domain("http://techcrunch.com/2026/10/10/article") == "techcrunch.com"
    assert service.extract_domain("https://sub.news.google.com/rss") == "sub.news.google.com"
    assert service.extract_domain("invalid-url-string") == "invalid-url-string"
    assert service.extract_domain(None) == "unknown_domain"
    assert service.extract_domain("") == "unknown_domain"

def test_evaluate_publisher_known_and_unknown(service):
    # Test known high-credibility domain
    bbc_rating = service.evaluate_publisher("bbc.com")
    assert bbc_rating.assessment_status == "rated"
    assert bbc_rating.rating == "high_credibility"
    assert "bbc.com" in bbc_rating.domain

    # Test subdomain fallback
    sub_bbc = service.evaluate_publisher("news.bbc.com")
    assert sub_bbc.assessment_status == "rated"
    assert sub_bbc.rating == "high_credibility"

    # Test unknown domain: must be marked "not_assessed", NOT fake or unreliable
    unknown_rating = service.evaluate_publisher("randomuntrackeddomain.xyz")
    assert unknown_rating.assessment_status == "not_assessed"
    assert unknown_rating.rating == "not_assessed"
    assert "not currently indexed" in unknown_rating.explanation or "not assessed" in unknown_rating.explanation.lower()

@pytest.mark.asyncio
async def test_search_fact_checks_missing_key(service):
    service.fact_check_api_key = ""
    status, fact_checks = await service.search_fact_checks("Some Headline")
    assert status == "Not checked"
    assert fact_checks == []

@pytest.mark.asyncio
async def test_search_fact_checks_mocked_success(service):
    service.fact_check_api_key = "test_fake_api_key"

    mock_response_data = {
        "claims": [
            {
                "text": "Claim headline",
                "claimant": "Public Figure",
                "claimReview": [
                    {
                        "publisher": {"name": "FactCheck.org"},
                        "reviewDate": "2026-10-01",
                        "textualRating": "False",
                        "url": "https://factcheck.org/claim-123"
                    }
                ]
            }
        ]
    }

    mock_resp = httpx.Response(status_code=200, json=mock_response_data)
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    with patch("httpx.AsyncClient", return_value=mock_client):
        mock_client.__aenter__.return_value = mock_client
        status, fact_checks = await service.search_fact_checks("Claim headline")
        assert status == "Fact-check rated FALSE"
        assert len(fact_checks) == 1
        assert fact_checks[0].fact_check_publisher == "FactCheck.org"
        assert fact_checks[0].original_rating == "False"
        assert fact_checks[0].normalized_status == "Fact-check rated FALSE"

def test_analyze_cross_source_discrepancies(service):
    # Single source
    single_art = [{"title": "Single headline", "source_name": "BBC News"}]
    status, findings = service.analyze_cross_source_discrepancies(single_art)
    assert status == "Insufficient evidence"
    assert len(findings["single_source_claims"]) == 1

    # Multiple aligned sources
    multi_arts_aligned = [
        {"title": "Global Tech Summit Announced in London", "source_name": "BBC News"},
        {"title": "Global Tech Summit Announced in London Today", "source_name": "The Guardian"}
    ]
    status_aligned, findings_aligned = service.analyze_cross_source_discrepancies(multi_arts_aligned)
    assert status_aligned == "Unanimous consensus"

    # Divergent sources
    multi_arts_divergent = [
        {"title": "Quantum Computing Breakthrough Unveiled", "source_name": "TechCrunch"},
        {"title": "Stock Market Experiences Minor Fluctuations", "source_name": "Bloomberg"}
    ]
    status_div, findings_div = service.analyze_cross_source_discrepancies(multi_arts_divergent)
    assert status_div == "Conflicting reports"
