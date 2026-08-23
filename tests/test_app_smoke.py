from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_app_initial_render_has_no_uncaught_exception() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not app.exception
