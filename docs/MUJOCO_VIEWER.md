# MuJoCo viewer guide

The window titled **MuJoCo : UGOT mecanum car** is MuJoCo's official native
viewer. It runs the physics simulation and provides inspection and debugging
controls. It is not a code editor.

To change the car's program, edit `sketches/user_sketch.py`, save it, close the
viewer, and run `python tools/run_sketch.py` again.

## Left sidebar

Select a red section heading to expand or collapse it.

### File

- **Save xml** saves the currently loaded model as XML.
- **Save mjb** saves MuJoCo's compiled binary model.
- **Print model** writes a detailed model report.
- **Print data** writes the current simulation-state report.
- **Screenshot** captures the viewport.
- **Quit** closes the viewer.

### Option

- **Help** shows the keyboard and mouse controls.
- **Info** displays timing and model statistics.
- **Profiler** displays physics-performance information.
- **Sensor** displays sensor graphs.
- **Pause update** freezes visual updates while simulation state may continue.
- **Fullscreen**, **Vertical Sync**, and **Busy Wait** control window and refresh
  behaviour.
- **Spacing**, **Color**, and **Font** change the viewer interface appearance.

### Simulation

- **Pause / Run** stops or starts physics stepping.
- **Num threads** changes the number of simulation threads where supported.
- **Reset** returns the current model to its initial state.
- **Reload** reloads the model file from disk. It does not reload
  `user_sketch.py`; restart `tools/run_sketch.py` after changing the sketch.
- **Align** aligns the free camera with the selected object.
- **Copy state** copies the current simulation state.
- **Key**, **Load key**, and **Save key** work with model keyframes.
- **Noise scale** and **Noise rate** add actuator-control noise.
- **History** lets the user inspect recorded simulation history when available.

### Watch

Displays a selected numeric model or data field. Enter a field such as `qpos`
and an index to inspect its live value.

### Physics

Controls the numerical simulation settings, including timestep, integrator,
solver, constraint options, gravity, contact overrides, and enable/disable
flags. Changing these values can materially change the robot's behaviour and
simulation stability.

### Rendering

Controls what the 3D viewport draws: camera selection, labels, coordinate
frames, geometry visibility, contacts, forces, shadows, reflections, and other
rendering flags.

### Visualisation

Adjusts scene appearance such as lighting, transparency, geometry rendering,
camera properties, fog, shadows, and related visual parameters. These options
normally affect appearance rather than physics.

### Group enable

Shows or hides numbered model groups. Model elements can be assigned to groups
so related geometry, sites, joints, tendons, or actuators can be inspected
together.

### Logging

Controls MuJoCo's runtime logging and diagnostic output. This section is for
simulation diagnostics; it does not contain the robot's Python program.

## Right sidebar

### Joint

Shows editable joint values. It is useful for posing the model or inspecting
individual joint coordinates.

### Control

Shows actuator control values. The four drive actuators correspond to the
front-left, front-right, rear-left, and rear-right wheels.

### Equality

Enables, disables, or inspects equality constraints defined by the model.

## Useful interaction controls

- **Space** pauses or resumes the simulation.
- **Backspace** resets the model.
- **Left drag** rotates the camera.
- **Right drag** pans the camera.
- **Mouse wheel** zooms.
- **Double-click** selects a body or geometry.
- **Tab / Shift+Tab** toggles the left or right sidebar.
- **Alt + section letter** expands or collapses a viewer section.

## Which program should users open?

| Goal | Command |
|---|---|
| Run the sketch in the official MuJoCo viewer | `python tools/run_sketch.py` |
| Edit and run in the optional UGOT graphical editor | `python tools/sketch_studio.py` |
| Open the model without the user sketch | `python tools/view_model.py` |

The official viewer controls simulation and inspection. The sketch controls the
car's behaviour. They are separate layers.
