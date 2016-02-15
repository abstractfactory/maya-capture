"""Tests for capture.

Within Maya, setup a scene of moderate range (e.g. 10 frames)
and run the following.

Example:
    >>> nose.run(argv=[sys.argv[0], "tests", "-v"])

"""

import capture


def test_capture():
    """Plain capture works"""
    capture.capture()


def test_camera_options():
    """(Optional) camera options works"""
    capture.capture(camera_options={"displayGateMask": False})


def test_display_options():
    """(Optional) display options works"""
    capture.capture(display_options={"displayGradient": False})


def test_viewport_options():
    """(Optional) viewport options works"""
    capture.capture(viewport_options={"wireframeOnShaded": True})


def test_preset():
    preset = {
        "width": 320,
        "height": 240,
        "camera_options": {
            "displayGateMask": False
        },
        "viewport_options": {
            "wireframeOnShaded": True
        },
        "display_options": {
            "displayGateMask": False
        }
    }

    capture.capture(**preset)
