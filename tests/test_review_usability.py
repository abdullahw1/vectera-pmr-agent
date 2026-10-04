"""Readable run summaries and the client-facing approval download contract."""

from pmr.review import diagnostics_summary


def test_summary_names_metrics_and_combines_provider_token_usage():
    page = diagnostics_summary(dict(
        provider="openai", model="writer", vision_model="reader",
        api_calls=2, cache_hits=3, failed_calls=1,
        token_usage=[dict(prompt_tokens=1000, completion_tokens=20),
                     dict(input_tokens=200, output_tokens=30)],
        stages=[dict(stage="exact_finance", status="ok", seconds=1.2)],
    ))
    assert "Run Summary" in page
    assert "OpenAI" in page
    assert "Saved responses reused</dt><dd>3" in page
    assert "Tokens used</dt><dd>1,250" in page
    assert "Check financial figures: ok (1.2 seconds)" in page
    assert "Technical log" in page
    assert "<pre>" not in page


def test_summary_escapes_model_and_stage_text_and_handles_no_key():
    page = diagnostics_summary(dict(model="<script>bad</script>",
        stages=[dict(stage="<img>", status="<error>")]))
    assert "No model access" in page
    assert "&lt;script&gt;bad&lt;/script&gt;" in page
    assert "&lt;img&gt;: &lt;error&gt;" in page
    assert "Tokens used</dt><dd>0" in page
