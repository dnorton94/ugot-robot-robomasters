# A beginner's guide to the robot simulator

The window titled **MuJoCo : UGOT mecanum car** is where you watch and test the
virtual robot. MuJoCo works out how the robot moves, turns, bumps into things,
and falls.

This window is **not** where you write the robot's instructions.

## Where do I program the robot?

Open this file in VS Code, Notepad, or another text editor:

```text
sketches/user_sketch.py
```

The file contains two important parts:

```python
def setup(robot):
    # This runs once when the robot starts.
    robot.stop()


def loop(robot):
    # This runs again and again while the robot is active.
    robot.drive(forward=0.20, left=0.0, turn=0.45)
```

After changing the file:

1. Save it.
2. Close the MuJoCo window.
3. Run `python tools/run_sketch.py` again.
4. Watch the robot follow your new instructions.

## What do the numbers mean?

In this example:

```python
robot.drive(forward=0.20, left=0.0, turn=0.45)
```

- `forward=0.20` tells the robot to move forwards.
- `left=0.0` means it should not move sideways.
- `turn=0.45` tells it to turn while moving, making a curved path.

Try changing one value at a time. Use small numbers while learning.

## The panels on the left

Click a red heading to open or close that group of controls.

### File

Use this section to save information or close the simulator.

- **Save xml** saves a readable copy of the robot model.
- **Save mjb** saves a faster-loading MuJoCo copy.
- **Print model** creates a technical report about the robot.
- **Print data** creates a report about what the robot is doing right now.
- **Screenshot** saves a picture of the simulation.
- **Quit** closes MuJoCo.

### Option

Use this section to change how the simulator looks and what information it
shows.

- **Help** shows the controls.
- **Info** shows basic information about the simulation.
- **Profiler** shows how hard the computer is working.
- **Sensor** shows information coming from virtual sensors.
- **Fullscreen** fills the screen.
- **Color**, **Font**, and **Spacing** change the appearance.

The other settings in this section are mainly useful when investigating display
or performance problems.

### Simulation

This is the main section for starting and stopping an experiment.

- **Pause / Run** pauses or continues the robot.
- **Reset** places the robot back at its starting position.
- **Reload** reloads the robot model. It does not reload your Python program.
- **Key**, **Load key**, and **Save key** work with saved model positions.
- **Noise scale** and **Noise rate** can make the motors less perfect, which is
  useful for more realistic experiments.
- **History** lets you look back through recorded simulation moments when that
  information is available.

For most beginner activities, **Pause**, **Run**, and **Reset** are the important
buttons.

### Watch

This section lets advanced users watch one number inside the simulation, such
as a wheel position or speed. Beginners can safely leave it closed.

### Physics

This section controls the rules and calculations used by the simulator. It
includes gravity, time steps, contacts, and calculation methods.

**Change these settings carefully.** The robot may move strangely or the
simulation may become unstable if they are set incorrectly.

### Rendering

This section chooses what you can see in the 3D view. For example, it can show
labels, contact points, forces, shadows, and coordinate frames. These options
usually change the picture rather than the robot's behaviour.

### Visualisation

This section changes the appearance of the scene, including lighting, fog,
shadows, transparency, and camera settings. It is generally safe to explore.

### Group enable

Robot parts can be placed into numbered groups. This section lets you show or
hide those groups, which can make it easier to inspect parts hidden inside the
robot.

### Logging

This section records technical information about the simulation. It is useful
when investigating a problem. It does not contain the robot's program.

## The panels on the right

### Joint

A joint is a place where one robot part can move relative to another. This
section shows and changes joint positions.

### Control

This section shows the commands being sent to the virtual motors. This robot has
four main drive controls: front-left, front-right, rear-left, and rear-right.

### Equality

This is an advanced section for special rules that hold model parts together or
make them move in a linked way. Beginners can leave it closed.

## Moving around the 3D view

- Drag with the **left mouse button** to rotate the view.
- Drag with the **right mouse button** to move the view sideways or vertically.
- Use the **mouse wheel** to zoom.
- Double-click a robot part to select it.
- Press **Space** to pause or continue.
- Press **Backspace** to reset the robot.
- Press **Tab** or **Shift+Tab** to hide or show the side panels.

## Which program should I open?

| What you want to do | What to open |
|---|---|
| Run your program in the official MuJoCo window | `python tools/run_sketch.py` |
| Edit and run using the optional beginner-friendly editor | `launch_sketch_editor.bat` |
| Look at the robot without running your program | `python tools/view_model.py` |

Remember: your Python sketch tells the car **what to do**. MuJoCo shows **what
happens when it does it**.
