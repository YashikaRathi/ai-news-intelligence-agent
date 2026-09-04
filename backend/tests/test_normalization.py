from app.services.ingestion import IngestionService

def test_article_normalization():
    service = IngestionService()

    raw_article = {
        "title": " <h1>Apple  unveils   new AI model!</h1> ",
        "description": "<p>Apple has <b>announced</b> its new frontier AI framework.</p>",
        "url": "https://techcrunch.com/2026/09/04/apple-ai/?utm_source=rss&utm_medium=feed&fbclid=123456",
        "source_name": " TechCrunch ",
        "author": "<b>John Doe</b>",
        "published_at": "2026-09-04T12:00:00Z",
        "topic": "AI"
    }

    normalized = service.normalize_article(raw_article)

    assert normalized["title"] == "Apple unveils new AI model!"
    assert normalized["normalized_title"] == "apple unveils new ai model"
    assert normalized["description"] == "Apple has announced its new frontier AI framework."
    assert normalized["canonical_url"] == "https://techcrunch.com/2026/09/04/apple-ai"
    assert normalized["url"] == "https://techcrunch.com/2026/09/04/apple-ai/?utm_source=rss&utm_medium=feed&fbclid=123456"
    assert normalized["source_name"] == "TechCrunch"
    assert normalized["author"] == "John Doe"
    assert len(normalized["id"]) > 0
