from pmr.market import select_observations


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
