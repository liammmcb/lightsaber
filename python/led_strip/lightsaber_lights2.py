"""
--------------------------------------------------------------------------
Lightsaber Lights
--------------------------------------------------------------------------
License:   
Copyright 2024 - Mustafa Latif

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
may be used to endorse or promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF 
THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------

Script that will code for functionality of LED strips implemented into a 
lightsaber project. The code will:

- turn the LED strips on when the button is pressed
- switch through a set color list upon pressing the button
- turn the LED strips off when the button is held

Notes:
- ACTIVATION_DELAY will alter how fast the LEDs ignite and deactivate
- COLOR_LIST contains RGB values of the colors that the blade will cycle
through
- LEDs were indexed based on two strips connected in sequence running in
opposite directions based on physical implementation. The blade will turn
on and off directionally to mimic lightsaber function.

--------------------------------------------------------------------------
"""

import time
import Adafruit_BBIO.GPIO as GPIO
from opc import Client

# Configuration
BUTTON_PIN = "P2_4"
OPC_SERVER_ADDRESS = "localhost:7890"
LED_COUNT = 60
ACTIVATION_DELAY = 0.01  # Faster ignition and deactivation

# Global state variables
led_on = False
button_pressed = False  # Tracks if the button is currently being pressed
current_color = (255, 0, 0)  # Default color (red)

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
        time.sleep(1)  # Keep the script running
except KeyboardInterrupt:
    print("Exiting program...")
    GPIO.cleanup()
    opc_client.put_pixels([(0, 0, 0)] * LED_COUNT)  # Turn off all LEDs
