"""Every matching decision (D-005 to D-008, D-024) as one table of cases."""

import pytest

from app.modules.scan.matcher import count_matches


@pytest.mark.parametrize(
    ("keywords", "text", "case_sensitive", "expected"),
    [
        (["salary"], "the salary is attached", False, 1),
        (["salary"], "salary, (salary) and salary-related", False, 3),
        (["salary"], "salaryman earns salary2024", False, 0),
        (["salary"], "salary_2024.xlsx and customer_salary", False, 2),
        (["salary"], "SALARY and Salary", False, 2),
        (["salary"], "SALARY and Salary", True, 0),
        (["salary"], "salary salary salary", False, 3),
        (["credit", "credit card"], "my credit card", False, 1),
        (["credit card"], "credit  card, credit\ncard, credit-card", False, 3),
        (["c++"], "we use c++ daily", False, 1),
        (["salary"], "", False, 0),
    ],
    ids=[
        "whole word",
        "punctuation separates",
        "inside a longer word: no",
        "underscore separates",
        "case-insensitive by default",
        "case-sensitive flag",
        "every occurrence counts",
        "overlap counts once",
        "multi-word gaps",
        "special characters escaped",
        "empty text",
    ],
)
def test_count_matches(keywords: list[str], text: str, case_sensitive: bool, expected: int) -> None:
    assert count_matches(keywords, text, case_sensitive) == expected
