import pytest
from app.services.translation.clients.deepl_client import DeepLClient


@pytest.mark.parametrize(
    "language,locale,expected",
    [
        ("english", "united states", "EN-US"),
        ("english", "uk", "EN-GB"),
        ("portuguese", "brazil", "PT-BR"),
        ("portuguese", "portugal", "PT-PT"),
        ("spanish", "colombia", "ES"),
        ("en", "us", "EN-US"),
        ("EN-US", "", "EN-US"),
        ("fr", "france", "FR"),
        ("chinese", "simplified", "ZH"),
    ],
)
def test_resolver(language, locale, expected):
    client = DeepLClient()
    assert client._resolve_language_code(language, locale) == expected
