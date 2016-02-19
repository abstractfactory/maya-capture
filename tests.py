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


def test_viewport2_options():
    """(Optional) viewport2 options works"""
    capture.capture(viewport2_options={"ssaoEnable": True})


def test_parse_active_view():
    """Parse active view works"""

    # Set focus to modelPanel1 (assume it exists)
    # Otherwise the panel with focus (temporary panel from capture)
    # got deleted and there's no "active panel"
    import maya.cmds as cmds
    cmds.setFocus("modelPanel1")

    options = capture.parse_active_view()
    capture.capture(**options)


def test_parse_view():
    """Parse view works"""

    options = capture.parse_view("modelPanel1", "front")
    capture.capture(**options)


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
