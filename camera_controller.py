from time import sleep
from picamera import PiCamera
from datetime import datetime
from settings import IMAGES_FOLDER

def take_picture():
    current_td = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")


    camera = PiCamera(resolution=(1280, 720), framerate=30)
    # Set ISO to the desired value
    camera.iso = 600
    # Wait for the automatic gain control to settle
    sleep(2)
    # Now fix the values
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
    # Finally, take a photo with the fixed settings
    image_name = f'{IMAGES_FOLDER}/image_{current_td}.jpg'
    camera.capture(image_name)
    camera.close()
