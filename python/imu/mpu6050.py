import smbus2
import time
import math

# MPU6050 Registers and Addresses
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


# Initialize I2C bus
bus = smbus2.SMBus(2)  # Use I2C bus 2, corresponding to P1_28 and P1_26 on PocketBeagle

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

# Main function to fetch and display sensor data at 60Hz
def main():
    init_mpu6050()
    print("MPU6050 Initialized. Reading data at 60Hz...\n")
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
            time.sleep(1 / 60.0)  # Wait to achieve 60 Hz updates
    except KeyboardInterrupt:
        print("\nExiting program.")

if __name__ == "__main__":
    main()




