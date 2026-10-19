"""Unit tests for the uvicorn access-log filter in app.main that keeps view-link signatures out of the log."""

import logging

import pytest

import app.main

SIGNATURE = "ab" * 32
REQUEST_PATH = f"/a/some-slug?v=1&e=1900000300&s={SIGNATURE}"


def _log_access_line() -> None:
    """Log a record shaped like uvicorn's access line, which passes the request path as an argument."""
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %d', "127.0.0.1:50000", "GET", REQUEST_PATH, "1.1", 200
    )


def _redacting_filters() -> list[logging.Filter]:
    return [f for f in logging.getLogger("uvicorn.access").filters if isinstance(f, app.main.SignatureRedactingFilter)]


def test_importing_app_main_puts_the_filter_on_the_uvicorn_access_logger():
    assert _redacting_filters()


def test_the_signature_is_redacted_and_the_record_kept(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        _log_access_line()

    assert len(caplog.records) == 1
    assert SIGNATURE not in caplog.text
    assert "/a/some-slug?v=1&e=1900000300&s=REDACTED" in caplog.text


def test_without_the_filter_the_raw_signature_is_logged(caplog: pytest.LogCaptureFixture):
    logger = logging.getLogger("uvicorn.access")
    filters = _redacting_filters()
    for f in filters:
        logger.removeFilter(f)
    try:
        with caplog.at_level(logging.INFO, logger="uvicorn.access"):
            _log_access_line()
    finally:
        for f in filters:
            logger.addFilter(f)

    assert SIGNATURE in caplog.text


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/a/x?s=abc", "/a/x?s=REDACTED"),
        ("/a/x?s=abc&v=1", "/a/x?s=REDACTED&v=1"),
        ("/a/x?v=1&s=", "/a/x?v=1&s=REDACTED"),
        ("/a/x?ss=abc&s=def", "/a/x?ss=abc&s=REDACTED"),
        ("/api/notes", "/api/notes"),
    ],
)
def test_every_s_parameter_value_is_replaced(path: str, expected: str):
    record = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, "%s %s", ("GET", path), None)

    assert app.main.SignatureRedactingFilter().filter(record) is True
    assert record.args == ("GET", expected)
