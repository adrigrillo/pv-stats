from pv_stats.ree.ree_api import throttle_request_dates


def test_throttle_request_dates_within_limit():
    dates = throttle_request_dates('2022-01-01T00:00', '2022-01-10T00:00')
    assert len(dates) == 1
    assert dates[0] == ('2022-01-01T00:00', '2022-01-10T00:00')


def test_throttle_request_dates_exceeding_limit():
    dates = throttle_request_dates('2022-01-01T00:00', '2022-03-01T00:00')
    assert len(dates) > 1
