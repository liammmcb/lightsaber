#Replica Lightsaber
##EDES 301 Replica Lightsaber Project
This is the repository for my EDES 301 final project; a replica lightsaber. Here is the link to my Hackster page with more detail: 
I, along with user mlatif21, combined to make a replica lightsaber from scratch. While he focused on the LEDs and button, I focused on the speakers and IMU.
Currently, lightsaber_lights.py runs an integrated script combining the IMU and the LEDs, although there are still some kinks in getting the two to fully integrate.
To utilize the lightsaber properly at the moment, instead run lightsaber_lights2.py
##IMU
There currently exists a python file mpu6050.py used solely for tracking IMU inputs and outputs. It gives accelerometer and gyroscopic data on the movement of the lightsaber.
##LED_strip
To get the lights to run, you must first run run-opc-server in one terminal, and then run lightsaber_lights2.py in another terminal. The reason that there are several version of lightsaber_lights are to test for integrated functionality with the IMU. As of now, only lightsaber_lights2.py works, as it is the most bare bones of the files. 
Other files in the led_strip folder are predominantly for testing purposes.
##Button
The files inside of the button folder are predominantly for testing purposes. The button has otherwise already been integrated into lightsaber_lights.py
##Completing the lightsaber
We plan to first fully integrate the IMU with the lights to properly produce flashes of white light on contact. Then, we plan to solve the I2S issues plaguing us, rendering us incapable of connecting the speaker to the lightsaber at all. Eventually, I also plan on integrating a touch screen to add more variability for the lightsaber.
