from opc import Client

# Configuration
OPC_SERVER_ADDRESS = "localhost:7890"
LED_COUNT = 60  # Total LEDs (both strips)

# Connect to OPC server
opc_client = Client(OPC_SERVER_ADDRESS)
if not opc_client.can_connect():
    print("Error: Could not connect to OPC server.")
else:
    print("Connected to OPC server.")

# Test with a single color
leds = [(255, 0, 0)] * LED_COUNT  # Red for testing
opc_client.put_pixels(leds)
opc_client.put_pixels(leds)
print("Sent test color (red) to all LEDs.")
