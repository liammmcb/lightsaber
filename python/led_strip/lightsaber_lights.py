import time
import Adafruit_BBIO.GPIO as GPIO
from opc import Client
import smbus2
import math

MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_XOUT_L = 0x3C
ACCEL_YOUT_H = 0x3D
ACCEL_YOUT_L = 0x3E
ACCEL_ZOUT_H = 0x3F
ACCEL_ZOUT_L = 0x40
GYRO_XOUT_H = 0x43
GYRO_XOUT_L = 0x44
GYRO_YOUT_H = 0x45
GYRO_YOUT_L = 0x46
GYRO_ZOUT_H = 0x47
GYRO_ZOUT_L = 0x48

prev_tot_accel = None
flash_counter = 0 

# Configuration
BUTTON_PIN = "P2_4"
OPC_SERVER_ADDRESS = "localhost:7890"
LED_COUNT = 60
ACTIVATION_DELAY = 0.01  # Faster ignition and deactivation
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize I2C bus
bus = smbus2.SMBus(2)  # Use I2C bus 2, corresponding to P1_28 and P1_26 on PocketBeagle

# Global state variables
led_on = False
button_pressed = False  # Tracks if the button is currently being pressed
current_color = (255, 0, 0)  # Default color (red)

# Initialize MPU6050
def init_mpu6050():
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)  # Wake up MPU6050

# Read raw data from two bytes and convert to signed integer
def read_raw_data(addr):
    high = bus.read_byte_data(MPU6050_ADDR, addr)
    low = bus.read_byte_data(MPU6050_ADDR, addr + 1)
    value = (high << 8) | low
    if value > 32768:
        value -= 65536
    return value

# Fetch and display accelerometer and gyroscope data
def get_sensor_data():
    # Read accelerometer data
    accel_x = read_raw_data(ACCEL_XOUT_H) -0.07
    accel_y = read_raw_data(ACCEL_YOUT_H) +0.02
    accel_z = read_raw_data(ACCEL_ZOUT_H) +0.04

    # Read gyroscope data
    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_YOUT_H)
    gyro_z = read_raw_data(GYRO_ZOUT_H)

    # Convert raw data to "g" and degrees per second
    accel_x_scaled = abs((accel_x / 16384.0)) # Scale for accelerometer
    accel_y_scaled = abs((accel_y / 16384.0))
    accel_z_scaled = abs((accel_z / 16384.0))

    gyro_x_scaled = (gyro_x / 131.0) -3  # Scale for gyroscope
    gyro_y_scaled = (gyro_y / 131.0) +0.2
    gyro_z_scaled = (gyro_z / 131.0) -0.5
    
    tot_accel = abs(math.sqrt(accel_x_scaled*accel_x_scaled + accel_y_scaled*accel_y_scaled + accel_z_scaled*accel_z_scaled) -1)
    tot_gyro = gyro_x_scaled + gyro_y_scaled + gyro_z_scaled 
    comb_accel_gyro = abs(tot_accel) + abs(tot_gyro/100)
   
    global prev_tot_accel, flash_counter
    
    if prev_tot_accel is None:
        difference = 0  # Initialize difference for the first iteration
    else:
        difference = prev_tot_accel - tot_accel

    # Update prev_tot_accel
    prev_tot_accel = tot_accel
    
    if difference >= 1:
        flash_counter = 6  # Set flash for 6 iterations
    elif flash_counter > 0:
        flash_counter -= 1  # Decrement flash counter

    flash = flash_counter > 0  # Flash is True if counter is positive
    
    if flash:
        speaker_vol = 100  # Set to maximum volume during a flash
    else:
        speaker_vol = min(comb_accel_gyro * 10, 100)
    
    return {
        "accel_x": accel_x_scaled,
        "accel_y": accel_y_scaled,
        "accel_z": accel_z_scaled,
        "gyro_x": gyro_x_scaled,
        "gyro_y": gyro_y_scaled,
        "gyro_z": gyro_z_scaled,
        "tot_accel": tot_accel,
        "tot_gyro": tot_gyro,
        "comb_accel_gyro": comb_accel_gyro,
        "speaker_vol": speaker_vol,
        "difference": difference,
        "flash": flash,
    }


# OPC client setup
opc_client = Client(OPC_SERVER_ADDRESS)
if not opc_client.can_connect():
    print("Warning: Could not connect to OPC server.")
else:
    print("Connected to OPC server.")

# Functions for LED control
def map_reverse_led(index):
    """
    Map LEDs in the second strip (31–60) to mirror the first strip (1–30).
    First strip (1–30): Left to right.
    Second strip (31–60): Left to right relative to its reversed orientation.
    """
    if index < 30:
        return index  # First strip (1–30): No change
    else:
        return LED_COUNT - 1 - (index - 30)  # Reverse mapping for second strip (31–60)

def activate_lights():
    """
    Turn on LEDs sequentially from both ends toward the middle.
    - First strip: Left to right (1 → 30).
    - Second strip: Right to left (60 → 31, mirrored).
    """
    global led_on, button_pressed
    if led_on:
        return  # Lights are already on

    led_states = [(0, 0, 0)] * LED_COUNT  # Start with all LEDs off
    for i in range(30):  # Iterate through total LED pairs (30 pairs)
        forward_index = i  # Forward direction for strip 1
        reverse_index = map_reverse_led(30 + i)  # Reverse mapping for strip 2

        led_states[forward_index] = current_color
        led_states[reverse_index] = current_color

        opc_client.put_pixels(led_states)
        time.sleep(ACTIVATION_DELAY)

    led_on = True
    button_pressed = False  # Reset button state
    print("Lightsaber activated!")

def deactivate_lights():
    """
    Turn off LEDs sequentially from the middle outward.
    - First strip: Right to left (30 → 1).
    - Second strip: Left to right relative to its reversed orientation (31 → 60).
    """
    global led_on, button_pressed
    if not led_on:
        return  # Lights are already off

    led_states = [(current_color if led_on else (0, 0, 0)) for _ in range(LED_COUNT)]
    for i in range(30):  # Iterate through total LED pairs (30 pairs)
        forward_index = 29 - i  # Reverse direction for strip 1
        reverse_index = 30 + i  # Proper forward direction for strip 2 (mirrored)

        led_states[forward_index] = (0, 0, 0)
        led_states[reverse_index] = (0, 0, 0)

        opc_client.put_pixels(led_states)
        time.sleep(ACTIVATION_DELAY)

    led_on = False
    button_pressed = False  # Reset button state
    print("Lightsaber deactivated!")

def button_handler(channel):
    """Handle button press and hold actions."""
    global current_color, button_pressed

    if button_pressed:
        return  # Ignore additional presses until the current one is processed

    button_pressed = True
    start_time = time.time()
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Wait while button is held
        elapsed_time = time.time() - start_time
        if elapsed_time >= 1.0:  # Hold time threshold
            deactivate_lights()
            return  # Exit once the lights are turned off

    # Single press to activate lights or change color
    if not led_on:
        activate_lights()
    else:
        # Change color continuously while the lights are on
        current_color = get_next_color(current_color)
        opc_client.put_pixels([current_color] * LED_COUNT)
        print(f"Color changed to: {current_color}")

    button_pressed = False  # Allow the next button press

def get_next_color(current_color):
    """Cycle to the next color in the predefined list."""
    COLOR_LIST = [
        (255, 0, 0),   # Red
        (255, 100, 0), # Orange
        (255, 160, 0), # Yellow
        (0, 255, 0),   # Green
        (0, 255, 255), # Cyan
        (0, 0, 255),   # Blue
        (255, 0, 255), # Magenta
        (255, 255, 255), # White
    ]
    index = COLOR_LIST.index(current_color)
    return COLOR_LIST[(index + 1) % len(COLOR_LIST)]

# GPIO setup for button
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_handler, bouncetime=300)

# Main loop
print("Ready! Use the button to control the lightsaber.")
try:
    while True:
        data = get_sensor_data()
        print(
            f"Accel: X={data['accel_x']:.2f}, Y={data['accel_y']:.2f}, Z={data['accel_z']:.2f} | "
            f"Gyro: X={data['gyro_x']:.2f}, Y={data['gyro_y']:.2f}, Z={data['gyro_z']:.2f} | "
            f"Totals: Accel={data['tot_accel']:.2f}, Gyro={data['tot_gyro']:.2f}, Comb={data['comb_accel_gyro']:.2f} | "
            f"Difference: {data['difference']:.2f}, Peripherals: Volume={data['speaker_vol']:.2f} | "
            f"Contact={'True' if data['difference'] >= 1 else 'False'}, Flash={'True' if data['flash'] else 'False'}"
        )
        time.sleep(1/30)  # Wait to achieve 60 Hz updates
except KeyboardInterrupt:
    print("Exiting program...")
    GPIO.cleanup()
    opc_client.put_pixels([(0, 0, 0)] * LED_COUNT)  # Turn off all LEDs
