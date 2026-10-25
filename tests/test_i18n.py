from goldpulse.i18n import tr


def test_english_is_identity():
    assert tr("Overview", "English") == "Overview"


def test_thai_translates_core_navigation_and_disclosure():
    assert tr("Overview", "ไทย") == "ภาพรวม"
    assert "ไม่ใช่คำแนะนำการลงทุน" in tr(
        "GoldPulse is an educational analytics project. Reference prices are not shop quotes. Forecasts are estimates and are not investment advice.",
        "ไทย",
    )


def test_unknown_source_name_is_preserved():
    assert tr("World Gold Council", "ไทย") == "World Gold Council"
