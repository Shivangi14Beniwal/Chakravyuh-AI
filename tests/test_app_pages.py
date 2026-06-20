"""
Boot-level tests for the command center app, using Streamlit's AppTest
harness to actually run app.py and each page's render() through
Streamlit's script-running machinery (catches errors that a plain HTTP
GET on the default page cannot, since page switches happen via widget
interaction inside one script).
"""

from streamlit.testing.v1 import AppTest


def test_app_boots_to_homepage():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert not at.exception


def test_map_view_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("🗺  Map view").run(timeout=30)
    assert not at.exception


def test_event_intelligence_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("🔍  Event intelligence").run(timeout=30)
    assert not at.exception


def test_alerts_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("🔔  Active alerts").run(timeout=30)
    assert not at.exception


def test_decision_support_page():
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    at.sidebar.radio[0].set_value("📊  Decision support").run(timeout=30)
    assert not at.exception