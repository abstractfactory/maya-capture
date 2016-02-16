"""Maya Capture

Playblasting with independent viewport, camera and display options

"""

import re
import sys
import contextlib

from maya import cmds

version_info = (2, 0, 0)

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
            quality=100,
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
        >>> capture('persp', 800, 600,
        ...         viewport_options={
        ...             "displayAppearance": "wireframe",
        ...             "grid": False,
        ...             "polymeshes": True,
        ...         },
        ...         camera_options={
        ...             "displayResolution": True
        ...         }
        ... )


    """

    camera = camera or "persp"
    
    # Fallback to default settings
    if camera_options is None:
        camera_options = CameraOptions.copy()
    
    if viewport_options is None:
        viewport_options = ViewportOptions.copy()
    
    if display_options is None:
        display_options = DisplayOptions.copy()

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

    # (#21) Bugfix: `maya.cmds.playblast` suffers from undo bug where it
    # always sets the currentTime to frame 1. By setting currentTime before
    # the playblast call it'll undo correctly.
    cmds.currentTime(cmds.currentTime(q=1))

    padding = 10  # Extend panel to accommodate for OS window manager
    with _independent_panel(width=width + padding,
                            height=height + padding) as panel:
        cmds.setFocus(panel)

        with contextlib.nested(
             _maintain_camera(panel, camera),
             applied_options(panel, camera,
                             camera_options,
                             viewport_options,
                             display_options),
             _isolated_nodes(isolate, panel),
             _maintained_time()):

                output = cmds.playblast(
                    compression=compression,
                    format=format,
                    percent=100,
                    quality=quality,
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


ViewportOptions = {
    "useDefaultMaterial": False,
    "wireframeOnShaded": False,
    "displayAppearance": 'smoothShaded',
    "selectionHiliteDisplay": False,
    "headsUpDisplay": True,
    "nurbsCurves": False,
    "nurbsSurfaces": False,
    "polymeshes": True,
    "subdivSurfaces": False,
    "cameras": False,
    "lights": False,
    "grid": False,
    "joints": False,
    "ikHandles": False,
    "deformers": False,
    "dynamics": False,
    "fluids": False,
    "hairSystems": False,
    "follicles": False,
    "nCloths": False,
    "nParticles": False,
    "nRigids": False,
    "dynamicConstraints": False,
    "locators": False,
    "manipulators": False,
    "dimensions": False,
    "handles": False,
    "pivots": False,
    "textures": False,
    "strokes": False,
}


CameraOptions = {
    "displayGateMask": False,
    "displayResolution": False,
    "displayFilmGate": False,
    "displayFieldChart": False,
    "displaySafeAction": False,
    "displaySafeTitle": False,
    "displayFilmPivot": False,
    "displayFilmOrigin": False,
    "overscan": 1.0,
}

DisplayOptions = {
    "displayGradient": True,
    "background": (0.631, 0.631, 0.631),
    "backgroundTop": (0.535, 0.617, 0.702),
    "backgroundBottom": (0.052, 0.052, 0.052),
}

# These display options require a different command to be queried and set
_DisplayOptionsRGB = set(["background", "backgroundTop", "backgroundBottom"])


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
        
        
def parse_active_view():
    """Parse the current settings from the active view"""
    
    panel = cmds.getPanel(wf=True)
    camera = cmds.modelEditor(panel, q=1, camera=1)
    return parse_view(panel, camera)

        
def parse_view(panel, camera):
    """Parse the scene, panel and camera for their current settings"""

    # Display options
    display_options = {}
    for key in DisplayOptions.keys():
        if key in _DisplayOptionsRGB:
            display_options[key] = cmds.displayRGBColor(key, query=True)
        else:
            display_options[key] = cmds.displayPref(query=True, **{key: True})
            
    # Viewport options
    viewport_options = {}
    for key in ViewportOptions.keys():
        viewport_options[key] = cmds.modelEditor(panel, query=True, **{key: True})

    # Camera options
    camera_options = {}
    for key in CameraOptions.keys():
        camera_options[key] = cmds.getAttr("{0}.{1}".format(camera, key))
    
    return {
        "viewport_options": viewport_options,
        "display_options": display_options,
        "camera_options": camera_options
    }

    
def apply_options(panel, camera,
                  camera_options=None,
                  viewport_options=None,
                  display_options=None):
    """Apply the options to the scene, panel and camera"""

    # Display options
    if display_options:
        for key, value in display_options.iteritems():
            if key in _DisplayOptionsRGB:
                cmds.displayRGBColor(key, *value)
            else:
                cmds.displayPref(**{key: value})
      
    # Viewport options
    if viewport_options:
        for key, value in viewport_options.iteritems():
            cmds.modelEditor(panel, edit=True, **{key: value})
            
    # Camera options
    if camera_options:
        for key, value in camera_options.iteritems():
            cmds.setAttr("{0}.{1}".format(camera, key), value)
    
    
@contextlib.contextmanager
def applied_options(panel, 
                    camera, 
                    camera_options=None,
                    viewport_options=None,
                    display_options=None):
    """Context manager to apply options to scene, panel and camera"""

    original = parse_view(panel, camera)
    try:
        apply_options(panel, camera, 
                      camera_options,
                      viewport_options,
                      display_options)
        yield
    finally:
        apply_options(panel, camera, **original)


@contextlib.contextmanager
def _isolated_nodes(nodes, panel):
    """Context manager for isolating `nodes` in `panel`"""

    if nodes is not None:
        cmds.isolateSelect(panel, state=True)
        for obj in nodes:
            cmds.isolateSelect(panel, addDagObject=obj)
    yield


@contextlib.contextmanager
def _maintained_time():
    """Context manager for preserving (resetting) the time after the context"""

    current_time = cmds.currentTime(query=1)
    try:
        yield
    finally:
        cmds.currentTime(current_time)


@contextlib.contextmanager
def _maintain_camera(panel, camera):
    state = {}

    if not _in_standalone():
        cmds.lookThru(panel, camera)
    else:
        state = dict((camera, cmds.getAttr(camera + ".rnd"))
                     for camera in cmds.ls(type="camera"))
        cmds.setAttr(camera + ".rnd", True)

    try:
        yield
    finally:
        for camera, renderable in state.iteritems():
            cmds.setAttr(camera + ".rnd", renderable)


def _image_to_clipboard(path):
    """Copies the image at path to the system's global clipboard."""
    if _in_standalone():
        raise Exception("Cannot copy to clipboard from Maya Standalone")

    import PySide.QtGui
    image = PySide.QtGui.QImage(path)
    clipboard = PySide.QtGui.QApplication.clipboard()
    clipboard.setImage(image, mode=PySide.QtGui.QClipboard.Clipboard)


def _get_screen_size():
    """Return available screen size without space occupied by taskbar"""
    if _in_standalone():
        return [0, 0]

    import PySide.QtGui
    rect = PySide.QtGui.QDesktopWidget().screenGeometry(-1)
    return [rect.width(), rect.height()]


def _in_standalone():
    return not hasattr(cmds, "about") or cmds.about(batch=True)
