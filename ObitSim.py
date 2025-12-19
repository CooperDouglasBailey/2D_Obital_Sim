import matplotlib
matplotlib.use('Qt5Agg')
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch

# Constants
G = 6.67430e-11         # gravitational constant (m^3 kg^-1 s^-2)
M_earth = 5.972e24      # mass of Earth (kg)
R_earth = 6.371e6       # radius of Earth (m)

# Drag and satellite parameters
C_d = 2.2  # Drag coefficient
A = 4.0    # Cross-sectional area (m^2)
m = 1000.0 # Satellite mass (kg)
# Atmospheric density model
rho_0 = 1.225  # kg/m^3 at sea level
H = 8500.0     # scale height (m)

# Function to compute acceleration due to gravity
def gravity_accel(t, state):
    x, y, vx, vy = state
    r = np.sqrt(x**2 + y**2)
    h = r - R_earth  # altitude above Earth's surface
    # Gravitational acceleration
    a = -G * M_earth / r**3
    ax = a * x
    ay = a * y
    # Atmospheric drag
    if h > 0:
        v = np.sqrt(vx**2 + vy**2)
        rho = rho_0 * np.exp(-h / H)
        F_drag = 0.5 * C_d * rho * A * v**2
        # Drag acceleration components (opposite to velocity)
        if v != 0:
            ax += -F_drag * vx / (m * v)
            ay += -F_drag * vy / (m * v)
    return [vx, vy, ax, ay]

# Prompt user for initial conditions
try:
    user_altitude = input("Enter initial altitude above Earth's surface in km (default 400): ")
    if user_altitude.strip() == "":
        altitude = 400e3
    else:
        altitude = float(user_altitude) * 1e3
except Exception:
    altitude = 400e3

# Calculate default circular velocity for the given altitude
r0 = R_earth + altitude
v0_circular = np.sqrt(G * M_earth / r0)

try:
    user_velocity = input(f"Enter initial velocity in m/s (default {v0_circular:.2f}): ")
    if user_velocity.strip() == "":
        v0 = v0_circular
    else:
        v0 = float(user_velocity)
except Exception:
    v0 = v0_circular

state0 = [r0, 0, 0, v0]  # Start on x-axis, moving in y direction

t_span = (0, 20000)  # 20,000 seconds (~5.5 hours)
t_eval = np.linspace(*t_span, 10000)

solution = solve_ivp(gravity_accel, t_span, state0, t_eval=t_eval, rtol=1e-8)

x = solution.y[0]
y = solution.y[1]
vx = solution.y[2]
vy = solution.y[3]

# Calculate altitude, velocity, and period
r = np.sqrt(x**2 + y**2)
altitudes = r - R_earth
velocities = np.sqrt(vx**2 + vy**2)

# Estimate period (time to complete one orbit)
def find_orbital_period(t, x, y):
    crossings = np.where((y[:-1] < 0) & (y[1:] >= 0))[0]
    print("Crossings found at indices:", crossings)
    print("Crossing times:", t[crossings])
    if len(crossings) > 1:
        period = t[crossings[1]] - t[crossings[0]]
        return period
    return None

period = find_orbital_period(solution.t, x, y)

print(f"Initial altitude: {altitude/1e3:.1f} km")
print(f"Initial velocity: {v0/1e3:.2f} km/s")
if period:
    print(f"Estimated orbital period: {period/60:.2f} minutes")
else:
    print("Could not determine orbital period from simulation.")

# Animate the satellite's motion
fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(x, y, label="Orbit", color='blue', alpha=0.5)
ax.plot(0, 0, 'ro', label="Earth")
satellite_dot, = ax.plot([], [], 'bo', markersize=8, label="Satellite")
trail_line, = ax.plot([], [], 'g-', linewidth=2, alpha=0.7, label="Trail")

# Create a persistent velocity vector (FancyArrowPatch)
arrow_scale = 500  # Adjust for visibility
velocity_vec = FancyArrowPatch((0, 0), (0, 0), color='magenta', arrowstyle='->', mutation_scale=20, linewidth=2)
ax.add_patch(velocity_vec)

ax.set_xlabel("x position (m)")
ax.set_ylabel("y position (m)")
ax.set_title("Satellite Orbit Animation")
ax.axis("equal")
ax.grid(True)
ax.legend(loc='upper left')

# Set axis limits for better view
buffer = R_earth * 0.2
ax.set_xlim(x.min() - buffer, x.max() + buffer)
ax.set_ylim(y.min() - buffer, y.max() + buffer)

# Initialization function for animation
def init():
    satellite_dot.set_data([], [])
    trail_line.set_data([], [])
    velocity_vec.set_positions((0, 0), (0, 0))
    return satellite_dot, trail_line, velocity_vec

# Animation function
def animate(i):
    if i >= len(x):
        i = len(x) - 1
    # Update satellite position
    satellite_dot.set_data([x[i]], [y[i]])
    # Update trail
    trail_line.set_data(x[:i+1], y[:i+1])
    # Update velocity vector
    dx = vx[i] * arrow_scale
    dy = vy[i] * arrow_scale
    velocity_vec.set_positions((x[i], y[i]), (x[i] + dx, y[i] + dy))
    return satellite_dot, trail_line, velocity_vec

ani = animation.FuncAnimation(fig, animate, frames=len(x), init_func=init,
                              interval=20, blit=True, repeat=True)

plt.show() 

# Subsample for the GIF to prevent freezing (e.g., every 50th frame)
step = 50 
x_gif = x[::step]
y_gif = y[::step]
vx_gif = vx[::step]
vy_gif = vy[::step]

# Update the animation function to use the subsampled data
def animate(i):
    satellite_dot.set_data([x_gif[i]], [y_gif[i]])
    trail_line.set_data(x_gif[:i+1], y_gif[:i+1])
    
    # Update velocity vector using subsampled data
    dx = vx_gif[i] * arrow_scale
    dy = vy_gif[i] * arrow_scale
    velocity_vec.set_positions((x_gif[i], y_gif[i]), (x_gif[i] + dx, y_gif[i] + dy))
    return satellite_dot, trail_line, velocity_vec

# Create animation with fewer frames
ani = animation.FuncAnimation(fig, animate, frames=len(x_gif), init_func=init,
                              interval=40, blit=True, repeat=True)

# Use a lower DPI and fewer FPS to save memory
print("Saving optimized animation...")
ani.save('orbit_simulation.gif', writer='pillow', fps=20, dpi=50)
print("Animation saved successfully.")