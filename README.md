### Maya playblast done right

Playblast with independent viewport, camera and display options.

With a regular Maya playblast, playblasting is dependent on
the size of your panel and provides no options for specifying
what to include or exclude, such as meshes or curves. Maya
Capture isolates a capture into an independent window in which
settings may be applied without affecting your current scene or
workspace. It also playblasts the given camera, without regard
to which panel is currently in focus.

### Usage

###### Capture perspective camera and display results

```python
capture()
```

###### Capture multiple cameras

```python
capture(camera='Camera1')
capture(camera='Camera2')
capture(camera='Camera3')
```

###### Capture with custom resolution

```python
capture(width=400, height=200)
```

### Structs

Rather than providing individual flags for the large amount
of options provided by the viewport, camera and display,
they are instead provided via an individual object, a.k.a.
"struct". To use, instantiate an option-object, set some
attributes, and pass the object as an argument to :func:`capture`.

###### Launch capture with custom viewport settings

```python
view_opts = ViewportOptions()
view_opts.grid = False
view_opts.polymeshes = True
view_opts.displayAppearance = "wireframe"

cam_opts = CameraOptions()
cam_opts.displayResolution = True

capture('myCamera', 800, 600,
        viewport_options=view_opts,
        camera_options=cam_opts)
```
