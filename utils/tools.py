import cv2
import ctypes, ctypes.wintypes
import keyboard as kb
import pyautogui as pag
import os
from time import time, localtime
from win32con import VK_SPACE
import winsound
from threading import Thread
from utils.imageprocess import ImageProcessing, CUR_DIR


pag.FAILSAFE = False


class Tools(ImageProcessing):
	def __init__(self) -> None:
		super().__init__()

		self.mic_img_G1 = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\mic_G_1.png'))
		self.mic_img_G2 = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\mic_G_2.png'))
		self.third_search_G = False

		self.mic_img_Y1 = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\mic_Y_1.png'))
		self.mic_img_Y2 = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\mic_Y_2.png'))
		self.third_search_Y = False

		self.photo_search_Y = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\photo_search_Y.png'))
		self.maybe_you_mean = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\maybe_you_mean_google.png'))
		self.show_res4request_google = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\show_res4request_google.png'))

		self.ans_circle = cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\ans_circle.png'))

		self.entry_coords_G = None
		self.entry_coords_Y = None

	def run_thread(self, func, name, args=tuple()):
		th = Thread(target=func, args=args)
		th.start()
		self.threads_dict[name] = th

	def place_on_screen(self, img, shift=0, pic_center=True, conf=0.85, region=[]):
		if (pic_center):
			"""
			haystackImage = haystackImage[region[1]:region[1]+region[3],
			    						  region[0]:region[0]+region[2]]
			region = [x, y, w, h]
			"""
			coord = pag.locateCenterOnScreen(img, limit=700, confidence=conf, region=region)
			if (coord):
				coord = [coord[0] + shift, coord[1]]
		else:
			coord = pag.locateOnScreen(img, limit=700, confidence=conf)
		return coord

	def locate_entry_G(self, shift=-200, update_attributes=True):
		"""Update attributes is created to flag
		 that this moment (when it is True)
		 I intend to update the coordinates in attributes
		 (exact variables: self.entry_coords_G),
		 without returning something informative.
		"""
		if (update_attributes):
			if (self.entry_coords_G is not None):
				region = []
				if (self.third_search_G):
					h, w, _ = self.mic_img_G2.shape
					x, y = self.entry_coords_G
					x -= w / 2
					y -= h / 2
					region = [int(x) + 200, int(y), w + 10, h + 10]

				self.entry_coords_G = self.place_on_screen(self.mic_img_G2, shift=shift, region=region)

				if (not self.entry_coords_G):
					self.entry_coords_G = self.place_on_screen(self.mic_img_G1, shift=shift)
				self.third_search_G = True
			else:
				self.entry_coords_G = self.place_on_screen(self.mic_img_G1, shift=shift)
				if (not self.entry_coords_G):
					self.entry_coords_G = self.place_on_screen(self.mic_img_G2, shift=shift)
			return 0
		else:
			google_coords = self.place_on_screen(self.mic_img_G2, shift=shift)
			if (not google_coords):
				google_coords = self.place_on_screen(self.mic_img_G1, shift=shift)
			return google_coords

	def locate_entry_Y(self, shift=-190, update_attributes=True):
		"""Update attributes is created to flag
		 that this moment (when it is True)
		 I intend to update the coordinates in attributes
		 (exact variables: self.entry_coords_Y),
		 without returning something informative.
		"""
		if (update_attributes):
			if (self.entry_coords_Y is not None):
				region = []
				if (self.third_search_Y):
					h, w, _ = self.mic_img_Y2.shape
					x, y = self.entry_coords_Y
					x -= w / 2
					y -= h / 2
					region = [int(x) + 190, int(y), w + 10, h + 10]

				self.entry_coords_Y = self.place_on_screen(self.mic_img_Y2, shift=shift, region=region)
				# print(self.entry_coords_Y)
				if (not self.entry_coords_Y):
					self.entry_coords_Y = self.place_on_screen(self.mic_img_Y1, shift=shift)
					if (not self.entry_coords_Y):
						self.entry_coords_Y = self.place_on_screen(self.mic_img_Y2, shift=shift)
				self.third_search_Y = True
			else:
				self.entry_coords_Y = self.place_on_screen(self.mic_img_Y1, shift=shift)
				if (not self.entry_coords_Y):
					self.entry_coords_Y = self.place_on_screen(self.mic_img_Y2, shift=shift)
			return 0
		else:
			yandex_coords = self.place_on_screen(self.mic_img_Y2, shift=shift)
			if (not yandex_coords):
				yandex_coords = self.place_on_screen(self.mic_img_Y1, shift=shift)
			return yandex_coords

	def loc_tech_pics(self, lock, yandexPS=False):
		"""Univesal function to find an input image on the screen.
		yandexPS -- yandex photo search.
		"""
		if (yandexPS):
			self.photo_search = self.place_on_screen(self.photo_search_Y, conf=0.9)
		else:
			self.run_thread(self.locate_entry_G, "LOC_ENTRIES_G")
			self.locate_entry_Y()
			self.threads_dict["LOC_ENTRIES_G"].join()
		lock.set()

	def get_key(self):
		ctypes.windll.user32.RegisterHotKey(None, 1, 0, 0x53) # 's'
		ctypes.windll.user32.RegisterHotKey(None, 1, 0, 0x4D) # 'm'
		ctypes.windll.user32.RegisterHotKey(None, 1, 0, VK_SPACE)
		msg = ctypes.wintypes.MSG()
		if ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0): # it can only get registrated keys: 's', 'm', 'space'
			key_index = [bool(ctypes.windll.user32.GetKeyState(0x53)), bool(ctypes.windll.user32.GetKeyState(0x4D)), bool(ctypes.windll.user32.GetKeyState(VK_SPACE))].index(True)
		self.key = {0: 's', 1: 'm', 2: 'space'}.get(key_index)

		self.LOCK_get_key.set()

	def unreg_keys(self):
		ctypes.windll.user32.UnregisterHotKey(None, 1)

	def hide_kb(self):
		os.system("start C:\\Users\\Admin\\Desktop\\Mine\\PROGRAMMING\\Projects\\Press_immitation\\quiz\\utils\\hide_kb.bat")

	def print_log(self, message, msg_to_print='', print_msg=True):
		if (print_msg):
			if (msg_to_print):
				print(msg_to_print)
			else:
				print(message)
		y, m, d, hh, mm, ss, *_ = localtime(time())
		self.qn_count_file = open(os.path.join(CUR_DIR, 'resources\\log.txt'), 'w')
		self.qn_count_file.write(message + f" [{self.qn_num}]" + f" [{y}-{m:02}-{d:02} {hh:02}:{mm:02}:{ss:02}]")
		self.qn_count_file.close()

	def exit_program(self):
		print("Questions number:", self.qn_num)

		self.qn_count_file = open(os.path.join(CUR_DIR, 'resources\\pictures_number.txt'), 'w')
		self.qn_count_file.truncate()
		self.qn_count_file.write("0")
		self.qn_count_file.close()

		kb.remove_all_hotkeys()

		winsound.Beep(2000, 700)
		winsound.Beep(800, 800)
		print("Exit")
		self.LOCK_shut_down.set()
