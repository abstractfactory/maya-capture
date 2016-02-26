![](https://cloud.githubusercontent.com/assets/2152766/13301028/d98a75b0-db3a-11e5-8c07-cad3e0382f96.gif)

### Playblasting in Maya done right

Playblast with independent viewport, camera and display options.

- [Issue tracker][issues]
- [Wiki][]

[issues]: https://github.com/mottosso/maya-capture/issues
[wiki]: https://github.com/mottosso/maya-capture/wiki

### Usage

With a regular Maya playblast, playblasting is dependent on
the size of your panel and provides no options for specifying
what to include or exclude, such as meshes or curves. Maya
Capture isolates a capture into an independent window in which
settings may be applied without affecting your current scene or
workspace. It also playblasts the given camera, without regard
to which panel is currently in focus.

To install, download [capture.py][] and place it in a directory where Maya can find it.

[capture.py]: https://raw.githubusercontent.com/mottosso/maya-capture/master/capture.py

### Examples

Overview

```python
from capture import capture
capture()

# Capture multiple cameras
capture('Camera1')
capture('Camera2')
capture('Camera3')

# Capture with custom resolution
capture(width=400, height=200)

# Launch capture with custom viewport settings
capture('persp', 800, 600,
        viewport_options={
            "displayAppearance": "wireframe",
            "grid": False,
            "polymeshes": True,
        },
        camera_options={
            "displayResolution": True
        }
)
```

Playblast selected cameras

```python
import maya.cmds as cmds
from capture import capture

# Any camera shapes under selection
cameras = cmds.ls(selection=True, dag=True, leaf=True, type="camera")
for cam in cameras:
    capture(cam)
```

Playblast selected time range

```python
import maya.cmds as cmds
import maya.mel as mel
from capture import capture

# Get global mel variable
time_slider = mel.eval("$gPlayBackSlider=$gPlayBackSlider")
start, end = cmds.timeControl(time_slider, query=True, rangeArray=True)
capture(start_frame=start, end_frame=end)
```

Playblast with current settings of a camera and panel

```python
from capture import parse_view, capture

options = parse_view("modelPanel1")
capture(**options)
```

Playblast with current settings of active view

```python
from capture import parse_active_view, capture

options = parse_active_view()
capture(**options)
```

Playblast to file using scene name

```python
from capture import capture
import maya.cmds as cmds
import os

filename = cmds.file(q=1, sceneName=True, shortName=True)
name = os.path.splitext(filename)[0]
capture(filename=name)
```

Taking a snapshot (single frame)

```python
from capture import snap

snap()
```

Taking a snapshot and store in clipboard. This allows you to paste it in other applications like Photoshop.

```python
from capture import snap

snap(clipboard=True)
```


### Advanced Examples

Building your own library of capture presets

```python
import json
import capture

# Utility functions to save and load options

def save_preset(path, preset):
    """Save options to path"""
    with open(path, "w") as f:
        json.dump(preset, f)


def load_preset(path):
    """Load options json from path"""
    with open(path, "r") as f:    
        return json.load(f)


# With this we can start saving presets
preset = capture.parse_active_view()
save_preset("myPreset.json", preset)

# And capturing with the presets
preset = load_preset("myPreset.json")
capture.capture(**preset)
```

### Store and retrieve view options

The following will read the state of the current modelPanel,
let you alter it in some way - such as changing the background
color - and then revert it back.

```python
import capture
from maya import cmds

# Read active panel
panel = cmds.getPanel(withFocus=True)
assert "modelPanel" in panel, "Must select a modelPanel"

# Capture current view
view = capture.parse_view(panel)

# Change your view..

# Apply previous view
capture.apply_view(panel, **view)
```

### Store and retrieve scene options

The following will read relevant settings from your
scene and playblast settings, let you alter it in some way - 
such as altering the frame range - and then revert it back.

```python
import capture

# Capture state of scene
scene = capture.parse_scene()

# Change your scene..

# Apply previous state
capture.apply_scene(**scene)
```
