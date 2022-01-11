import pytest

from unittest.mock import patch, MagicMock


def test_additional_properties(additional_properties_spec):
    resp = MagicMock(status_code=200, headers={"Content-Type": "application/json"}, json=lambda: {"foo": "bar", "additional": "property"})
    with patch("requests.sessions.Session.send", return_value=resp) as s:
        additional_properties_spec.call_test_operation()
