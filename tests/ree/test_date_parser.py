# Date parsing tests
from datetime import datetime

import pytest

from pv_stats.ree.ree_api import parse_date


def test_parse_date_returns_correct_format_for_string_input():
    date = "2022-01-01T00:00"
    assert parse_date(date) == date

def test_parse_date_returns_correct_format_for_string_input_cut():
    date = "2022-01-01T00:00:30"
    assert parse_date(date) == "2022-01-01T00:00"

def test_parse_date_raises_error_incorrect_format():
    date = "1-1-2022"
    with pytest.raises(ValueError):
        parse_date(date)

def test_parse_date_returns_correct_format_for_datetime_input():
    date = datetime(2022, 1, 1, 0, 0)
    assert parse_date(date) == "2022-01-01T00:00"

def test_parse_date_returns_correct_format_for_datetime_input_cut():
    date = datetime(2022, 1, 1, 0, 0, 30)
    assert parse_date(date) == "2022-01-01T00:00"

def test_parse_date_raises_value_error_for_invalid_input():
    with pytest.raises(ValueError):
        parse_date(123)
