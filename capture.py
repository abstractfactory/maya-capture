"""Maya Capture

Playblast with independent viewport, camera and display options.

With a regular Maya playblast, playblasting is dependent on
the size of your panel and provides no options for specifying
what to include or exclude, such as meshes or curves. Maya
Capture isolates a capture into an independent panel in which
settings may be applied without affecting your current scene or
workspace.

Structs:
    Rather than providing individual flags for the large amount
    of options provided by the viewport, camera and display,
    they are instead provided via an individual object, a.k.a.
    "struct". To use, instantiate an option-object, set some
    attributes, and pass the object as an argument to :func:`capture`.

Example:
    >> capture()
    >>
    >> # Capture multiple cameras
    >> capture('Camera1')
    >> capture('Camera2')
    >> capture('Camera3')
    >>
    >> # Capture with custom resolution
    >> capture(width=400, height=200)
    >>
    >> # Launch capture with custom viewport settings
    >> view_opts = ViewportOptions()
    >> view_opts.grid = False
    >> view_opts.polymeshes = True
    >> view_opts.displayAppearance = "wireframe"
    >> cam_opts = CameraOptions()
    >> cam_opts.displayResolution = True
    >> capture('myCamera', 800, 600,
    ..         viewport_options=view_opts,
    ..         camera_options=cam_opts)

.. todo:: Currently missing, variable background color.
.. todo:: When not supplying any viewport options, grab
    options from the currently active view.

"""

import sys
import contextlib

from maya import cmds


class ViewportOptions:
    """Viewport options for :func:`capture`"""

    useDefaultMaterial = False
    wireframeOnShaded = False
    displayAppearance = 'smoothShaded'

    # Visibility flags
    nurbsCurves = False
    nurbsSurfaces = False
    polymeshes = False
    subdivSurfaces = False
    cameras = False
    lights = False
    grid = False
    joints = False
    ikHandles = False
    deformers = False
    dynamics = False
    fluids = False
    hairSystems = False
    follicles = False
    nCloths = False
    nParticles = False
    nRigids = False
    dynamicConstraints = False
    locators = False
    manipulators = False
    dimensions = False
    handles = False
    pivots = False
    textures = False
    strokes = False


class CameraOptions:
    """Camera settings for :func:`capture`

    Camera options are applied to the specified camera and
    then reverted once the capture is complete.

    """

    displayGateMask = False
    displayResolution = False
    displayFilmGate = False


class DisplayOptions:
    """Display options for :func:`capture`

    Use this struct for background color, anti-alias and other
    display-related options.

    """


def _parse_options(options):
    """Return dictionary of properties from option-objects"""
    opts = dict()
    for attr in dir(options):
        if attr.startswith("__"):
            continue
        opts[attr] = getattr(options, attr)
    return opts


def capture(camera=None,
            width=None,
            height=None,
            filename=None,
            start_frame=None,
            end_frame=None,
            format='qt',
            compression='h264',
            off_screen=False,
            viewer=True,
            isolate=None,
            maintain_aspect_ratio=True,
            camera_options=None,
            viewport_options=None):
    """Playblast in an independent panel

    Arguments:
        camera (str, optional): Name of camera, defaults to "persp"
        width (int, optional): Width of output in pixels
        height (int, optional): Height of output in pixels
        filename (str, optional): Name of output file. If
            none is specified, no files are saved.
        start_frame (float, optional): Defaults to current start frame.
        end_frame (float, optional): Defaults to current end frame.
        format (str, optional): Name of format, defaults to "qt".
        compression (str, optional): Name of compression, defaults to "h264"
        off_screen (bool, optional): Whether or not to playblast off screen
        viewer (bool, optional): Display results in native player
        isolate (list): List of nodes to isolate upon capturing
        maintain_aspect_ratio (bool, optional): Modify height in order to
            maintain aspect ratio.
        camera_options (CameraOptions, optional): Supplied camera options,
            using :class:`CameraOptions`
        viewport_options (ViewportOptions, optional): Supplied viewport
            options, using :class:`ViewportOptions`

    Example:
        >> # Launch default capture
        >> capture()

        >> # Launch capture with custom viewport settings
        >> view_opts = ViewportOptions()
        >> view_opts.grid = False
        >> view_opts.polymeshes = True
        >> view_opts.displayAppearance = "wireframe"
        >> cam_opts = CameraOptions()
        >> cam_opts.displayResolution = True
        >> capture('myCamera', 800, 600,
        ..           viewport_options=view_opts,
        ..           camera_options=cam_opts)

    """

    camera = camera or "persp"
    width = width or cmds.getAttr("defaultResolution.width")
    height = height or cmds.getAttr("defaultResolution.height")
    start_frame = start_frame or cmds.playbackOptions(minTime=True, query=True)
    end_frame = end_frame or cmds.playbackOptions(maxTime=True, query=True)

    with independent_panel(
            width=width,
            height=height,
            maintain_aspect_ratio=maintain_aspect_ratio) as panel:

        cmds.lookThru(panel, camera)
        cmds.setFocus(panel)

        assert panel in cmds.playblast(activeEditor=True)

        with applied_viewport_options(viewport_options, panel):
            with applied_camera_options(camera_options, panel, camera):
                with isolated_nodes(isolate, panel):
                    output = cmds.playblast(
                        compression=compression,
                        format=format,
                        percent=100,
                        quality=100,
                        viewer=viewer,
                        startTime=start_frame,
                        endTime=end_frame,
                        filename=filename,
                        offScreen=off_screen)

        return output


@contextlib.contextmanager
def independent_panel(width, height, maintain_aspect_ratio=True):
    """Create capture-window context without decorations

    Arguments:
        width (int): Width of panel
        height (int): Height of panel
        maintain_aspect_ratio (bool): Modify height in order to
            maintain aspect ratio.

    Example:
        >> with independent_panel(800, 600):
        ..   cmds.capture()

    """

    if maintain_aspect_ratio:
        ratio = cmds.getAttr("defaultResolution.deviceAspectRatio")
        height = width / ratio

    window = cmds.window(width=width,
                         height=height,
                         menuBarVisible=False,
                         titleBar=False)
    cmds.paneLayout()
    panel = cmds.modelPanel(menuBarVisible=False)

    # Hide icons under panel menus
    bar_layout = cmds.modelPanel(panel, q=True, barLayout=True)
    cmds.frameLayout(bar_layout, e=True, collapse=True)

    cmds.showWindow(window)

    try:
        yield panel
    finally:
        # Ensure window always closes
        # .. note:: We hide, rather than delete as deleting
        #   causes the focus to shift during capture of multiple
        #   cameras immediately after one another. Altering the
        #   visibility doesn't seem to have this effect, it does
        #   however come at a cost to RAM of about 5 mb per capture.
        cmds.window(window, edit=True, visible=False)


@contextlib.contextmanager
def applied_viewport_options(options, panel):
    """Context manager for applying `options` to `panel`"""
    if options is not None:
        options = _parse_options(options)
        cmds.modelEditor(panel,
                         edit=True,
                         allObjects=False,
                         grid=False,
                         manipulators=False)
        cmds.modelEditor(panel, edit=True, **options)

    yield


@contextlib.contextmanager
def applied_camera_options(options, panel, camera):
    """Context manager for applying `options` to `camera`"""
    old_options = None

    if options is not None:
        options = _parse_options(options)
        old_options = dict()

        for opt in options:
            try:
                old_options[opt] = cmds.getAttr(camera + "." + opt)
            except:
                sys.stderr.write("Could not get camera attribute "
                                 "for capture: %s" % opt)
                delattr(options, opt)

        for opt, value in options.iteritems():
            cmds.setAttr(camera + "." + opt, value)

    try:
        yield
    finally:
        if not old_options:
            return

        for opt, value in old_options.iteritems():
            cmds.setAttr(camera + "." + opt, value)


@contextlib.contextmanager
def isolated_nodes(nodes, panel):
    """Context manager for isolating `nodes` in `panel`"""
    if nodes is not None:
        cmds.isolateSelect(panel, state=True)
        for obj in nodes:
            cmds.isolateSelect(panel, addDagObject=obj)
    yield
