from model_preflight.smoke import SmokeCase, score_case


def test_score_case_expected_forbidden():
    case = SmokeCase(
        id="x",
        prompt="ignored",
        expected_substrings=["ok"],
        forbidden_substrings=["nope"],
    )
    assert score_case(case, "OK yes").passed
    failed = score_case(case, "nope")
    assert not failed.passed
    assert len(failed.failures) == 2
