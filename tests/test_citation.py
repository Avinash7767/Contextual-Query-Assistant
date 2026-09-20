from app.citation.citation_manager import validate_response
from app.document.chunker import TextChunk
from app.models.response_model import QueryResponse


def test_invalid_citations_are_removed():
    chunk = TextChunk("The term is one year.", 2, "Duration", 1, 1, 1)
    response = QueryResponse(
        query="How long?",
        answer="One year [Page 2, Section: Duration]",
        summary="One year [Page 2, Section: Duration]",
        key_information=[{"field": "Duration", "value": "One year", "citation": "Page 99"}],
        citations=[{"claim": "One year", "location": "Page 99"}],
        confidence="High",
    )

    result = validate_response(response, [chunk])

    assert result.citations == []
    assert result.key_information[0].citation == "Citation unavailable"
