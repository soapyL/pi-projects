import board
import digitalio
import usb_hid
import time
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

print("Started")

time.sleep(5)

button1 = digitalio.DigitalInOut(board.GP4)
button1.direction = digitalio.Direction.INPUT
button1.pull = digitalio.Pull.DOWN

button2 = digitalio.DigitalInOut(board.GP5)
button2.direction = digitalio.Direction.INPUT
button2.pull = digitalio.Pull.DOWN

button3 = digitalio.DigitalInOut(board.GP6)
button3.direction = digitalio.Direction.INPUT
button3.pull = digitalio.Pull.DOWN

led1 = digitalio.DigitalInOut(board.GP2)
led1.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.GP3)
led2.direction = digitalio.Direction.OUTPUT

kbd = Keyboard(usb_hid.devices)

button1_last_state = False
button2_last_state = False
button3_last_state = False

while True:
    button1_state = button1.value
    button2_state = button2.value
    button3_state = button3.value

    if button1_state and not button1_last_state:
        led1.value = True
        kbd.send(Keycode.A)
        print("LED 1: ON\nButton 1: ON")
    elif not button1_state:
        led1.value = False

    if button2_state and not button2_last_state:
        led2.value = True
        kbd.send(Keycode.B)
        print("LED 2: ON\nButton 2: ON")
    elif not button2_state:
        led2.value = False

    if button3_last_state and not button3_state:
        kbd.send(Keycode.D)
        print("Toggle went OFF")

    if not button3_last_state and button3_state:
        kbd.send(Keycode.C)
        print("Toggle went ON")

    button1_last_state = button1_state
    button2_last_state = button2_state
    button3_last_state = button3_state

    time.sleep(0.05)
