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


def test_apply_view():
    """Apply view works"""
    capture.apply_view("modelPanel1", "persp", camera_options={"overscan": 2})


def test_apply_parsed_view():
    """Apply parsed view works"""
    options = capture.parse_view("modelPanel1", "persp")
    capture.apply_view("modelPanel1", "persp", **options)


def test_apply_parsed_view_exact():
    """Apply parsed view sanity check works"""

    import maya.cmds as cmds
    panel = "modelPanel1"
    camera = "persp"

    cmds.modelEditor(panel, edit=True, displayAppearance="wireframe")
    parsed = capture.parse_view(panel, camera)
    display = parsed["viewport_options"]["displayAppearance"]
    assert display == "wireframe"

    # important to test both, just in case wireframe was already
    # set when making the first query, and to make sure this
    # actually does something.
    cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded")
    parsed = capture.parse_view(panel, camera)
    display = parsed["viewport_options"]["displayAppearance"]
    assert display == "smoothShaded"

    capture.apply_view(panel,
                       camera,
                       viewport_options={"displayAppearance": "wireframe"})
    assert cmds.modelEditor(panel,
                            query=True,
                            displayAppearance=True) == "wireframe"


def test_apply_parsed_view_all():
    """Apply parsed view all options works"""

    # A set of options all trying to be different from the default
    # settings (in `capture.py`) so we can test "changing states"
    camera_options = {
        "displayGateMask": True,
        "displayResolution": True,
        "displayFilmGate": True,
        "displayFieldChart": True,
        "displaySafeAction": True,
        "displaySafeTitle": True,
        "displayFilmPivot": True,
        "displayFilmOrigin": True,
        "overscan": 2.0,
        "depthOfField": True,
    }

    display_options = {
        "displayGradient": False,
        "background": (0.0, 1, 0.1),
        "backgroundTop": (0.6, 0.1, 0.1),
        "backgroundBottom": (0.1, 0.1, 0.1),
    }

    viewport_options = {
        "rendererName": "vp2Renderer",
        "fogging": True,
        "fogMode": "linear",
        "fogDensity": 0.2,
        "fogStart": 0,
        "fogEnd": 5,
        "fogColor": (0.3, 1, 2, 3),
        "shadows": True,
        "depthOfFieldPreview": True,
        "displayTextures": False,
        "displayLights": "default",
        "useDefaultMaterial": True,
        "wireframeOnShaded": True,
        "displayAppearance": 'smoothShaded',
        "selectionHiliteDisplay": True,
        "headsUpDisplay": False,
        "nurbsCurves": True,
        "nurbsSurfaces": True,
        "polymeshes": False,
        "subdivSurfaces": True,
        "cameras": True,
        "lights": True,
        "grid": True,
        "joints": True,
        "ikHandles": True,
        "deformers": True,
        "dynamics": True,
        "fluids": True,
        "hairSystems": True,
        "follicles": True,
        "nCloths": True,
        "nParticles": True,
        "nRigids": True,
        "dynamicConstraints": True,
        "locators": True,
        "manipulators": True,
        "dimensions": True,
        "handles": True,
        "pivots": True,
        "textures": True,
        "strokes": True
    }

    viewport2_options = {
        "consolidateWorld": False,
        "enableTextureMaxRes": True,
        "bumpBakeResolution": 32,
        "colorBakeResolution": 32,
        "floatingPointRTEnable": False,
        "floatingPointRTFormat": 2,
        "gammaCorrectionEnable": True,
        "gammaValue": 1.0,
        "holdOutDetailMode": 2,
        "holdOutMode": False,
        "hwFogEnable": True,
        "hwFogColorR": 0.4,
        "hwFogColorG": 0.3,
        "hwFogColorB": 0.2,
        "hwFogAlpha": 0.4,
        "hwFogDensity": 0.4,
        "hwFogEnd": 200.0,
        "hwFogFalloff": 1,
        "hwFogStart": 10.0,
        "lineAAEnable": True,
        "maxHardwareLights": 4,
        "motionBlurEnable": True,
        "motionBlurSampleCount": 4,
        "motionBlurShutterOpenFraction": 0.4,
        "motionBlurType": 0,
        "multiSampleCount": 4,
        "multiSampleEnable": True,
        "singleSidedLighting": True,
        "ssaoEnable": True,
        "ssaoAmount": 0.5,
        "ssaoFilterRadius": 8,
        "ssaoRadius": 8,
        "ssaoSamples": 8,
        "textureMaxResolution": 1024,
        "threadDGEvaluation": True,
        "transparencyAlgorithm": 1,
        "transparencyQuality": 0.55,
        "useMaximumHardwareLights": False,
        "vertexAnimationCache": 0
     }

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
    camera = "persp"

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
    capture.apply_view(panel, camera, **defaults)
    parsed_defaults = capture.parse_view(panel, camera)
    assert compare(defaults, parsed_defaults)

    # Apply others and check
    capture.apply_view(panel, camera, **others)
    parsed_others = capture.parse_view(panel, camera)
    assert compare(others, parsed_others)


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
