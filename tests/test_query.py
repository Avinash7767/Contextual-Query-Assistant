from app.config import Settings
from app.document.chunker import TextChunk
from app.services.query_service import QueryService


class FakeClient:
    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]

    def answer(self, query, excerpts):
        citation = excerpts[0][0]
        return {
            "query": query,
            "answer": f"The answer is in the document [{citation}]",
            "summary": f"The document supports the answer [{citation}]",
            "key_information": [{"field": "Answer", "value": "Supported", "citation": citation}],
            "citations": [{"claim": "The answer is supported", "location": citation}],
            "confidence": "High",
        }


def test_query_returns_structured_response():
    service = QueryService(Settings(), FakeClient())
    service.chunks = [TextChunk("Payment is due in 30 days.", 1, "Payment Terms", 1, 1, 1)]

    response = service.query("When is payment due?")

    assert response.confidence == "High"
    assert response.key_information[0].citation == "Page 1, Section: Payment Terms"
