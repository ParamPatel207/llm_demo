from datetime import date

from odyssey_watcher.amc import _parse_imax_showtimes_from_html
from odyssey_watcher.config import Settings


def _settings() -> Settings:
    return Settings(
        ntfy_base_url="https://ntfy.sh",
        ntfy_topic_all="odyssey_nyc_all",
        ntfy_token=None,
        poll_interval_seconds=45,
        lookahead_days=25,
        theatre_location="new-york-city",
        theatre_key="amc-lincoln-square-13",
        movie_title="The Odyssey",
        premium_offering="70mm",
        state_path=__import__("pathlib").Path("/tmp/state.json"),
        amc_graph_url="https://graph.amctheatres.com",
        amc_web_base="https://www.amctheatres.com",
    )


FIXTURE_HTML = """
<div class="ShowtimesByTheatre-film">
  <div class="MovieTitleHeader-title"><h2>The Odyssey</h2></div>
  <div class="PremiumOffering">
    <h3>IMAX 70MM: EXTRAORDINARY AWAITS</h3>
    <a href="/showtimes/143822214">2:00pm</a>
    <a href="/showtimes/143822215">6:00pm</a>
  </div>
  <div class="PremiumOffering">
    <h3>70mm: GREATER DETAIL AND DEPTH</h3>
    <a href="/showtimes/143822148">12:30pm</a>
  </div>
</div>
"""


def test_parse_only_imax_70mm_showtimes() -> None:
    settings = _settings()
    showtimes = _parse_imax_showtimes_from_html(
        FIXTURE_HTML, settings, date(2026, 7, 28)
    )
    ids = {s.showtime_id for s in showtimes}
    assert ids == {143822214, 143822215}
