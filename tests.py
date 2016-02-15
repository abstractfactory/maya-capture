import capture


def test_capture():
    """Plain capture works"""
    capture.capture()


def test_camera_options():
    """(Optional) camera options works"""

    options = capture.CameraOptions.copy()
    options["displayGateMask"] = not options["displayGateMask"]

    capture.capture(camera_options=options)


def test_display_options():
    """(Optional) display options works"""
    options = capture.DisplayOptions.copy()
    options["displayGradient"] = not options["displayGradient"]

    capture.capture(display_options=options)


def test_viewport_options():
    """(Optional) viewport options works"""
    options = capture.ViewportOptions.copy()
    options["wireframeOnShaded"] = not options["wireframeOnShaded"]

    capture.capture(viewport_options=options)
