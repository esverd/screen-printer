from __future__ import annotations

from screen_printer.session import DevelopSessionTimer, TripleClickDetector


def test_timer_reports_elapsed_time() -> None:
    ticks = iter([10.0, 12.5, 13.0])
    timer = DevelopSessionTimer(clock=lambda: next(ticks))

    timer.start()
    assert timer.elapsed_seconds == 2.5
    assert timer.stop() == 3.0


def test_triple_click_detector_requires_three_clicks_in_window() -> None:
    detector = TripleClickDetector(window_seconds=0.5)

    assert detector.register_click(now=1.0) is False
    assert detector.register_click(now=1.2) is False
    assert detector.register_click(now=1.4) is True


def test_triple_click_detector_expires_old_clicks() -> None:
    detector = TripleClickDetector(window_seconds=0.5)

    assert detector.register_click(now=1.0) is False
    assert detector.register_click(now=1.2) is False
    assert detector.register_click(now=2.0) is False
    assert detector.register_click(now=2.1) is False
    assert detector.register_click(now=2.2) is True
