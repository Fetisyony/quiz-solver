import ctypes, ctypes.wintypes, cv2
from io import BytesIO
import keyboard as kb
import numpy as np
from PIL import Image
from time import sleep, time
import win32clipboard
import utils.keysim as keysim



def get_img():
	last = win32clipboard.GetClipboardSequenceNumber()

	keysim.take_screen()

	while (last + 4 != win32clipboard.GetClipboardSequenceNumber()):
		sleep(0.001)
	sleep(0.004)

	try:
		win32clipboard.OpenClipboard()
	except:
		print("Trying to open keyboard again")
		sleep(0.01)
		win32clipboard.OpenClipboard()

	img_b = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
	win32clipboard.CloseClipboard()

	im = Image.open(BytesIO(img_b))
	cur_img = np.asarray(im)


kb.add_hotkey("space", get_img)

kb.wait()