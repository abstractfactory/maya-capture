"""Tests for capture.

Within Maya, setup a scene of moderate range (e.g. 10 frames)
and run the following.

Example:
    >>> nose.run(argv=[sys.argv[0], "tests", "-v"])

"""

import capture
from maya import cmds


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

    options = capture.parse_view("modelPanel1")
    capture.capture(**options)


def test_apply_view():
    """Apply view works"""
    capture.apply_view("modelPanel1", camera_options={"overscan": 2})


def test_apply_parsed_view():
    """Apply parsed view works"""
    options = capture.parse_view("modelPanel1")
    capture.apply_view("modelPanel1", **options)


def test_apply_parsed_view_exact():
    """Apply parsed view sanity check works"""

    import maya.cmds as cmds
    panel = "modelPanel1"

    cmds.modelEditor(panel, edit=True, displayAppearance="wireframe")
    parsed = capture.parse_view(panel)
    display = parsed["viewport_options"]["displayAppearance"]
    assert display == "wireframe"

    # important to test both, just in case wireframe was already
    # set when making the first query, and to make sure this
    # actually does something.
    cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded")
    parsed = capture.parse_view(panel)
    display = parsed["viewport_options"]["displayAppearance"]
    assert display == "smoothShaded"

    capture.apply_view(panel,
                       viewport_options={"displayAppearance": "wireframe"})
    assert cmds.modelEditor(panel,
                            query=True,
                            displayAppearance=True) == "wireframe"


def test_apply_parsed_view_all():
    """Apply parsed view all options works"""

    # A set of options all trying to be different from the default
    # settings (in `capture.py`) so we can test "changing states"
    camera_options = {}
    display_options = {}
    viewport_options = {}
    viewport2_options = {}

    for key, value in capture.CameraOptions.items():
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, (int, float)):
            value = value + 1
        else:
            raise Exception("Unexpected value in CameraOptions: %s=%s"
                            % (key, value))

    for key, value in capture.DisplayOptions.items():
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, tuple):
            value = (1, 0, 1)
        else:
            raise Exception("Unexpected value in DisplayOptions: %s=%s"
                            % (key, value))

    for key, value in capture.ViewportOptions.items():
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, (int, float)):
            value = value + 1
        elif isinstance(value, tuple):
            value = (1, 0, 1)
        elif isinstance(value, basestring):
            pass  # Don't bother, for now
        else:
            raise Exception("Unexpected value in ViewportOptions: %s=%s"
                            % (key, value))

    for key, value in capture.Viewport2Options.items():
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, (int, float)):
            value = value + 1
        elif isinstance(value, tuple):
            value = (1, 0, 1)
        elif isinstance(value, basestring):
            pass  # Don't bother, for now
        else:
            raise Exception("Unexpected value in Viewport2Options: %s=%s"
                            % (key, value))

    defaults = {
        "camera_options": capture.CameraOptions.copy(),
        "display_options": capture.DisplayOptions.copy(),
        "viewport_options": capture.ViewportOptions.copy(),
        "viewport2_options": capture.Viewport2Options.copy(),
    }

    others = {
        "camera_options": camera_options,
        "display_options": display_options,
        "viewport_options": viewport_options,
        "viewport2_options": viewport2_options,
    }

    panel = "modelPanel1"

    def compare(this, other):
        """Compare options for only settings available in `this`

        Some color values will be returned with possible floating
        point precision errors as such result in a slightly
        different number. We'd need to compare whilst keeping
        such imprecisions in mind.
        """
        precision = 1e-4

        for opt in this:
            this_option = this[opt]
            other_option = other[opt]

            for key, value in this_option.iteritems():
                other_value = other_option[key]

                if isinstance(value, float) or isinstance(other_value, float):
                    if abs(value - other_value) > precision:
                        return False
                elif isinstance(value, (tuple, list)):
                    # Assuming for now that any tuple or list contains floats
                    if not all((abs(a-b) < precision)
                               for a, b in zip(value, other_value)):
                        return False
                else:
                    if value != other_value:
                        return False

        return True

    # Apply defaults and check
    capture.apply_view(panel, **defaults)
    parsed_defaults = capture.parse_view(panel)
    assert compare(defaults, parsed_defaults)

    # Apply others and check
    capture.apply_view(panel, **others)
    parsed_others = capture.parse_view(panel)
    assert compare(others, parsed_others)


def test_preset():
    """Creating and applying presets works"""

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


def test_parse_active_scene():
    """parse_active_scene() works"""

    parsed = capture.parse_active_scene()
    reference = {
        "start_frame": cmds.playbackOptions(minTime=True, query=True),
        "end_frame": cmds.playbackOptions(maxTime=True, query=True),
        "width": cmds.getAttr("defaultResolution.width"),
        "height": cmds.getAttr("defaultResolution.height"),
        "compression": cmds.optionVar(query="playblastCompression"),
        "filename": (cmds.optionVar(query="playblastFile")
                     if cmds.optionVar(query="playblastSaveToFile") else None),
        "format": cmds.optionVar(query="playblastFormat"),
        "off_screen": (True if cmds.optionVar(query="playblastOffscreen")
                       else False),
        "show_ornaments": (True if cmds.optionVar(query="playblastShowOrnaments")
                       else False),
        "quality": cmds.optionVar(query="playblastQuality")
    }

    for key, value in reference.items():

        assert parsed[key] == value
