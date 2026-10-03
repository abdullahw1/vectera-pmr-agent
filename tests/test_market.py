from pmr.market import select_observations, observation_sentence


def point(label, series="A", value=1):
    return dict(label=label, series=series, value=value, unit="%")


def test_latest_quarter_uses_chronology_not_lexical_order():
    points = [point("4Q25"), point("1Q26")]
    assert select_observations(points, [])[0]["label"] == "1Q26"


def test_material_sectors_follow_actual_portfolio_exposure():
    points = [point("Office"), point("Industrial"), point("Residential"), point("Retail")]
    mix = [dict(label="Apartment", value=40), dict(label="Retail", value=30),
           dict(label="Industrial", value=20), dict(label="Office", value=10)]
    assert {p["label"] for p in select_observations(points, mix)} == {"Residential", "Retail"}


def test_short_return_horizon_and_latest_quarter_are_retained():
    points = [point("1-Yr"), point("3-Yr"), point("5-Yr"), point("Latest Qtr")]
    assert [p["label"] for p in select_observations(points, [])] == ["Latest Qtr", "1-Yr"]


def test_market_prose_uses_source_values_and_retains_approximation():
    chart = dict(data=dict(title="Forecast NOI Growth by Sector (% per year)", series=[
        dict(label="Industrial", series="2026", value=1.7, unit="%", method="axis_read"),
        dict(label="Industrial", series="2027", value=8.9, unit="%", method="axis_read"),
        dict(label="Residential", series="2026", value=2.2, unit="%", method="label")]))
    text = observation_sentence(chart, [dict(label="Industrial", value=40), dict(label="Apartment", value=30)])
    assert "2026 NOI growth" in text and "~1.7%" in text and "2.2%" in text
    assert "8.9%" not in text


def test_market_return_sentence_does_not_rank_against_client_benchmark():
    chart = dict(data=dict(title="U.S. Private Real Estate - Fund Total Return (net)", series=[
        point("Latest Qtr", value=0.8), point("1-Yr", value=3.3)]))
    text = observation_sentence(chart, [])
    assert "0.8%" in text and "3.3%" in text
    assert "benchmark" not in text.lower() and "outperform" not in text.lower()


def test_forward_forecast_uses_next_period_not_current_year():
    chart = dict(data=dict(title="Forecast NOI Growth by Sector", series=[
        point("Industrial", series="2025", value=1.7),
        point("Industrial", series="2026-27 (p.a.)", value=1.3),
        point("Industrial", series="2028-30 (p.a.)", value=1.8)]))
    text = observation_sentence(chart, [dict(label="Industrial", value=40)], 2025)
    assert "2026-27" in text and "1.3%" in text and "1.7%" not in text
