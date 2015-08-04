"""Maya Capture

Playblasting with independent viewport, camera and display options

"""

import sys
import contextlib
import re

version_info = (1, 0, 0)

__version__ = "%s.%s.%s" % version_info
__license__ = "MIT"


def capture(camera=None,
            width=None,
            height=None,
            filename=None,
            start_frame=None,
            end_frame=None,
            frame=None,
            format='qt',
            compression='h264',
            off_screen=False,
            viewer=True,
            isolate=None,
            maintain_aspect_ratio=True,
            overwrite=False,
            raw_frame_numbers=False,
            camera_options=None,
            viewport_options=None,
            display_options=None,
            complete_filename=None):
    """Playblast in an independent panel

    Arguments:
        camera (str, optional): Name of camera, defaults to "persp"
        width (int, optional): Width of output in pixels
        height (int, optional): Height of output in pixels
        filename (str, optional): Name of output file. If
            none is specified, no files are saved.
        start_frame (float, optional): Defaults to current start frame.
        end_frame (float, optional): Defaults to current end frame.
        frame (float or tuple, optional): A single frame or list of frames.
            Use this to capture a single frame or an arbitrary sequence of
            frames.
        format (str, optional): Name of format, defaults to "qt".
        compression (str, optional): Name of compression, defaults to "h264"
        off_screen (bool, optional): Whether or not to playblast off screen
        viewer (bool, optional): Display results in native player
        isolate (list): List of nodes to isolate upon capturing
        maintain_aspect_ratio (bool, optional): Modify height in order to
            maintain aspect ratio.
        overwrite (bool, optional): Whether or not to overwrite if file
            already exists. If disabled and file exists and error will be
            raised.
        raw_frame_numbers (bool, optional): Whether or not to use the exact
            frame numbers from the scene or capture to a sequence starting at
            zero. Defaults to False. When set to True `viewer` can't be used
            and will be forced to False.
        camera_options (CameraOptions, optional): Supplied camera options,
            using :class:`CameraOptions`
        viewport_options (ViewportOptions, optional): Supplied viewport
            options, using :class:`ViewportOptions`
        display_options (DisplayOptions, optional): Supplied display
            options, using :class:`DisplayOptions`
        complete_filename (str, optional): Exact name of output file. Use this
            to override the output of `filename` so it excludes frame padding.

    Example:
        >>> # Launch default capture
        >>> capture()
        >>> # Launch capture with custom viewport settings
        >>> view_opts = ViewportOptions()
        >>> view_opts.grid = False
        >>> view_opts.polymeshes = True
        >>> view_opts.displayAppearance = "wireframe"
        >>> cam_opts = CameraOptions()
        >>> cam_opts.displayResolution = True
        >>> capture('myCamera', 800, 600,
        ...         viewport_options=view_opts,
        ...         camera_options=cam_opts)

    """

    from maya import cmds

    camera = camera or "persp"

    # Ensure camera exists
    if not cmds.objExists(camera):
        raise RuntimeError("Camera does not exist: {0}".format(camera))

    width = width or cmds.getAttr("defaultResolution.width")
    height = height or cmds.getAttr("defaultResolution.height")
    if maintain_aspect_ratio:
        ratio = cmds.getAttr("defaultResolution.deviceAspectRatio")
        height = width / ratio

    start_frame = start_frame or cmds.playbackOptions(minTime=True, query=True)
    end_frame = end_frame or cmds.playbackOptions(maxTime=True, query=True)

    # We need to wrap `completeFilename`, otherwise even when None is provided
    # it will use filename as the exact name. Only when lacking as argument
    # does it function correctly.
    playblast_kwargs = dict()
    if complete_filename:
        playblast_kwargs['completeFilename'] = complete_filename
    if frame:
        playblast_kwargs['frame'] = frame

    with _independent_panel(
            width=width+10,
            height=height+10) as panel:

        cmds.lookThru(panel, camera)
        cmds.setFocus(panel)

        assert panel in cmds.playblast(activeEditor=True)

        with _applied_viewport_options(viewport_options, panel):
            with _applied_camera_options(camera_options, panel, camera):
                with _applied_display_options(display_options):
                    with _isolated_nodes(isolate, panel):
                        output = cmds.playblast(
                            compression=compression,
                            format=format,
                            percent=100,
                            quality=100,
                            viewer=viewer,
                            startTime=start_frame,
                            endTime=end_frame,
                            offScreen=off_screen,
                            forceOverwrite=overwrite,
                            filename=filename,
                            widthHeight=[width, height],
                            rawFrameNumbers=raw_frame_numbers,
                            **playblast_kwargs)

        return output


def snap(*args, **kwargs):
    """Single frame playblast in an independent panel.

    The arguments of `capture` are all valid here as well, except for
    `start_frame` and `end_frame`.

    Arguments:
        frame (float, optional): The frame to snap. If not provided current
            frame is used.
        clipboard (bool, optional): Whether to add the output image to the
            global clipboard. This allows to easily paste the snapped image
            into another application, eg. into Photoshop.

    Keywords:
        See `capture`.
    """

    from maya import cmds

    # capture single frame
    frame = kwargs.pop('frame', cmds.currentTime(q=1))
    kwargs['start_frame'] = frame
    kwargs['end_frame'] = frame
    kwargs['frame'] = frame

    if not isinstance(frame, (int, float)):
        raise TypeError("frame must be a single frame (integer or float). "
                        "Use `capture()` for sequences.")

    # override capture defaults
    format = kwargs.pop('format', "image")
    compression = kwargs.pop('compression', "png")
    viewer = kwargs.pop('viewer', False)
    raw_frame_numbers = kwargs.pop('raw_frame_numbers', True)
    kwargs['compression'] = compression
    kwargs['format'] = format
    kwargs['viewer'] = viewer
    kwargs['raw_frame_numbers'] = raw_frame_numbers

    # pop snap only keyword arguments
    clipboard = kwargs.pop('clipboard', False)

    # perform capture
    output = capture(*args, **kwargs)

    def replace(m):
        """Substitute # with frame number"""
        return str(int(frame)).zfill(len(m.group()))

    output = re.sub("#+", replace, output)

    # add image to clipboard
    if clipboard:
        _image_to_clipboard(output)

    return output


class ViewportOptions:
    """Viewport options for :func:`capture`"""

    useDefaultMaterial = False
    wireframeOnShaded = False
    displayAppearance = 'smoothShaded'
    selectionHiliteDisplay = False
    headsUpDisplay = True

    # Visibility flags
    nurbsCurves = False
    nurbsSurfaces = False
    polymeshes = True
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
    displayGradient = True
    background = (0.631, 0.631, 0.631)
    backgroundTop = (0.535, 0.617, 0.702)
    backgroundBottom = (0.052, 0.052, 0.052)


def _parse_options(options):
    """Return dictionary of properties from option-objects"""
    opts = dict()
    for attr in dir(options):
        if attr.startswith("__"):
            continue
        opts[attr] = getattr(options, attr)
    return opts


@contextlib.contextmanager
def _independent_panel(width, height):
    """Create capture-window context without decorations

    Arguments:
        width (int): Width of panel
        height (int): Height of panel

    Example:
        >>> with _independent_panel(800, 600):
        ...   cmds.capture()

    """

    from maya import cmds

    # center panel on screen
    screen_width, screen_height = _get_screen_size()
    topLeft = [int((screen_height-height)/2.0),
               int((screen_width-width)/2.0)]

    window = cmds.window(width=width,
                         height=height,
                         topLeftCorner=topLeft,
                         menuBarVisible=False,
                         titleBar=False)
    cmds.paneLayout()
    panel = cmds.modelPanel(menuBarVisible=False,
                            label='CapturePanel')

    # Hide icons under panel menus
    bar_layout = cmds.modelPanel(panel, q=True, barLayout=True)
    cmds.frameLayout(bar_layout, e=True, collapse=True)

    cmds.showWindow(window)

    # Set the modelEditor of the modelPanel as the active view so it takes
    # the playback focus. Does seem redundant with the `refresh` added in.
    editor = cmds.modelPanel(panel, query=True, modelEditor=True)
    cmds.modelEditor(editor, e=1, activeView=True)

    # Force a draw refresh of Maya so it keeps focus on the new panel
    # This focus is required to force preview playback in the independent panel
    cmds.refresh(force=True)

    try:
        yield panel
    finally:
        # Delete the panel to fix memory leak (about 5 mb per capture)
        cmds.deleteUI(panel, panel=True)
        cmds.deleteUI(window)


@contextlib.contextmanager
def _applied_viewport_options(options, panel):
    """Context manager for applying `options` to `panel`"""

    from maya import cmds

    options = options or ViewportOptions()
    options = _parse_options(options)
    cmds.modelEditor(panel,
                     edit=True,
                     allObjects=False,
                     grid=False,
                     manipulators=False)
    cmds.modelEditor(panel, edit=True, **options)

    yield


@contextlib.contextmanager
def _applied_camera_options(options, panel, camera):
    """Context manager for applying `options` to `camera`"""

    from maya import cmds

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
        if old_options:
            for opt, value in old_options.iteritems():
                cmds.setAttr(camera + "." + opt, value)


@contextlib.contextmanager
def _applied_display_options(options):
    """Context manager for setting background color display options."""
    from maya import cmds

    options = options or DisplayOptions()

    colors = ['background', 'backgroundTop', 'backgroundBottom']
    prefs = ['displayGradient']

    # store current settings
    original = {}
    for clr in colors:
        original[clr] = cmds.displayRGBColor(clr, query=True)
    for pref in prefs:
        original[pref] = cmds.displayPref(query=True, **{pref: True})

    # apply settings of options
    for clr in colors:
        value = getattr(options, clr)
        cmds.displayRGBColor(clr, *value)
    for pref in prefs:
        value = getattr(options, pref)
        cmds.displayPref(**{pref: value})

    yield

    # restore original settings
    for clr in colors:
        cmds.displayRGBColor(clr, *original[clr])
    for pref in prefs:
        cmds.displayPref(**{pref: original[pref]})


@contextlib.contextmanager
def _isolated_nodes(nodes, panel):
    """Context manager for isolating `nodes` in `panel`"""
    from maya import cmds

    if nodes is not None:
        cmds.isolateSelect(panel, state=True)
        for obj in nodes:
            cmds.isolateSelect(panel, addDagObject=obj)
    yield


def _image_to_clipboard(path):
    """Copies the image at path to the system's global clipboard."""
    import PySide.QtGui
    image = PySide.QtGui.QImage(path)
    clipboard = PySide.QtGui.QApplication.clipboard()
    clipboard.setImage(image, mode=PySide.QtGui.QClipboard.Clipboard)


def _get_screen_size():
    """Return available screen size without space occupied by taskbar"""
    import PySide.QtGui
    rect = PySide.QtGui.QDesktopWidget().screenGeometry(-1)
    return [rect.width(), rect.height()]
