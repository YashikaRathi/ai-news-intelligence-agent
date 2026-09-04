from app.services.deduplication import DeduplicationService

def test_exact_duplicate_detection():
    service = DeduplicationService()

    art1 = {
        "title": "OpenAI Unveils GPT-5",
        "normalized_title": "openai unveils gpt5",
        "canonical_url": "https://techcrunch.com/openai-gpt-5",
        "url": "https://techcrunch.com/openai-gpt-5?utm_source=feed"
    }

    art2 = {
        "title": "OpenAI Unveils GPT-5",
        "normalized_title": "openai unveils gpt5",
        "canonical_url": "https://techcrunch.com/openai-gpt-5",
        "url": "https://techcrunch.com/openai-gpt-5"
    }

    assert service.is_exact_duplicate(art1, art2) is True


def test_near_duplicate_detection():
    service = DeduplicationService()

    art1 = {
        "title": "Apple announces new AI model",
        "normalized_title": "apple announces new ai model",
        "description": "Apple introduced its new artificial intelligence model for iOS."
    }

    art2 = {
        "title": "Apple unveils new artificial intelligence model",
        "normalized_title": "apple unveils new artificial intelligence model",
        "description": "Apple introduced its new artificial intelligence model for iOS smartphones."
    }

    art3 = {
        "title": "SpaceX launches Falcon Heavy rocket from Florida",
        "normalized_title": "spacex launches falcon heavy rocket from florida",
        "description": "SpaceX launched a satellite payload into orbit from Cape Canaveral."
    }

    assert service.is_near_duplicate(art1, art2, threshold=0.50) is True
    assert service.is_near_duplicate(art1, art3, threshold=0.50) is False
