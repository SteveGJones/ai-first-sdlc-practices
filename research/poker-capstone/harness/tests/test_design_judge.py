from harness.design_judge import build_judge_prompt


def test_build_judge_prompt_includes_all_inputs():
    prompt = build_judge_prompt("server", "reference text here", "candidate text here")
    assert "reference text here" in prompt
    assert "candidate text here" in prompt
    assert "poker server" in prompt
    assert "completeness" in prompt and "superior_choices" in prompt
