import smbus2

MPU6050_ADDR = 0x68  # Default I2C address
PWR_MGMT_1 = 0x6B    # Power management register

bus = smbus2.SMBus(2)  # Replace with the correct I2C bus number
try:
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)  # Wake up the sensor
    print("MPU6050 communication successful!")
except Exception as e:
    print(f"Error communicating with MPU6050: {e}")
