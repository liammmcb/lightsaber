from opc import Client

# Configuration
OPC_SERVER_ADDRESS = "localhost:7890"
LED_COUNT = 60  # Total number of LEDs (both strips)

# Connect to OPC server
opc_client = Client(OPC_SERVER_ADDRESS)

if not opc_client.can_connect():
    print("Error: Could not connect to OPC server.")
else:
    print("Connected to OPC server.")

def reset_leds():
    """Turn off all LEDs to reset their state."""
    leds = [(0, 0, 0)] * LED_COUNT  # Set all LEDs to black (off)
    opc_client.put_pixels(leds)
    opc_client.put_pixels(leds)  # Send twice for reliability
    print("All LEDs turned off (reset).")

def test_leds():
    """Turn all LEDs on with a test color."""
    leds = [(255, 0, 0)] * LED_COUNT  # Red for testing
    opc_client.put_pixels(leds)
    opc_client.put_pixels(leds)
    print("All LEDs set to red for testing.")

# Run reset and test
try:
    reset_leds()
    input("Press Enter to test LEDs with red...")
    test_leds()
    input("Press Enter to turn LEDs off...")
    reset_leds()
except KeyboardInterrupt:
    reset_leds()  # Ensure LEDs are off on exit
