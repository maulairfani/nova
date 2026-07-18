"""Unit tests for app/agent/tool_labels.py's citation extraction
(parse_citations/merge_citations) - the Sources panel feature. Fixture
shapes match a real MCP tool call verified directly against the live
mcp-tv/mcp-shared servers (raw JSON-RPC tools/call), not assumed: FastMCP
wraps a tool's list return as `structuredContent.result`, and
langchain-mcp-adapters re-serializes that as
`[content_blocks, {"structured_content": {...}}]` before it reaches
ToolMessage.content."""
import json

from app.agent.tool_labels import merge_citations, parse_citations


def _mcp_content(structured_content: dict) -> str:
    return json.dumps([[{"type": "text", "text": "..."}], {"structured_content": structured_content}])


def test_parse_citations_extracts_kb_search_results():
    raw = _mcp_content(
        {
            "result": [
                {
                    "text": "## Booking Process\n1. ...",
                    "source_document": "01-ad-slot-booking-sop.md",
                    "title": "Ad Slot Booking SOP — MCN TV",
                    "section_heading": "Booking Process",
                    "score": 0.548,
                },
                {
                    "text": "## Rate Cards\n...",
                    "source_document": "01-ad-slot-booking-sop.md",
                    "title": "Ad Slot Booking SOP — MCN TV",
                    "section_heading": "Rate Cards",
                    "score": 0.294,
                },
            ]
        }
    )
    citations = parse_citations("tv_kb_search", raw)
    assert citations == [
        {
            "type": "kb",
            "unit": "tv",
            "title": "Ad Slot Booking SOP — MCN TV",
            "snippet": "## Booking Process\n1. ...",
            "source_document": "01-ad-slot-booking-sop.md",
        },
        {
            "type": "kb",
            "unit": "tv",
            "title": "Ad Slot Booking SOP — MCN TV",
            "snippet": "## Rate Cards\n...",
            "source_document": "01-ad-slot-booking-sop.md",
        },
    ]


def test_parse_citations_extracts_web_search_results():
    raw = _mcp_content(
        {"result": [{"title": "MCN Group news", "url": "https://example.com/a", "content": "...", "score": 0.9}]}
    )
    citations = parse_citations("shared_web_search", raw)
    assert citations == [
        {"type": "web", "title": "MCN Group news", "snippet": "...", "url": "https://example.com/a"}
    ]


def test_parse_citations_returns_none_for_non_citation_tools():
    assert parse_citations("tv_sql_analytics", _mcp_content({"result": []})) is None
    assert parse_citations("shared_generate_chart", _mcp_content({"result": []})) is None


def test_parse_citations_returns_none_on_malformed_content():
    assert parse_citations("tv_kb_search", "not json") is None
    assert parse_citations("tv_kb_search", json.dumps({"unexpected": "shape"})) is None


def test_merge_citations_dedupes_by_source_document_across_calls():
    first_batch = parse_citations(
        "tv_kb_search",
        _mcp_content(
            {
                "result": [
                    {"text": "a", "source_document": "doc.md", "title": "Doc", "section_heading": None, "score": 0.5},
                    {"text": "b", "source_document": "doc.md", "title": "Doc", "section_heading": None, "score": 0.4},
                ]
            }
        ),
    )
    citations = merge_citations([], first_batch)
    assert len(citations) == 1  # both chunks share the same source_document

    second_batch = parse_citations(
        "plus_kb_search",
        _mcp_content(
            {"result": [{"text": "c", "source_document": "other.md", "title": "Other", "section_heading": None, "score": 0.3}]}
        ),
    )
    citations = merge_citations(citations, second_batch)
    assert [c["source_document"] for c in citations] == ["doc.md", "other.md"]


def test_merge_citations_is_a_noop_for_none_or_empty():
    existing = [{"type": "kb", "source_document": "doc.md"}]
    assert merge_citations(existing, None) is existing
    assert merge_citations(existing, []) is existing
