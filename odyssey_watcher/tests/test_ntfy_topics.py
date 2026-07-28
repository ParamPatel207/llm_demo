from odyssey_watcher.ntfy import ntfy_topic_for_date


def test_ntfy_topic_for_date() -> None:
    assert ntfy_topic_for_date("jul", 28) == "odyssey_nyc_jul28"
    assert ntfy_topic_for_date("aug", 1) == "odyssey_nyc_aug1"
