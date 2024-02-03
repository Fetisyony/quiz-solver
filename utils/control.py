import pytesseract
pytesseract.pytesseract.tesseract_cmd = r''

if not (pytesseract.pytesseract.tesseract_cmd):
	print("[ERROR] Configure `tesseract_cmd` path in control.py")
	exit(1)

import cv2
from io import BytesIO
import keyboard as kb
import numpy as np
from PIL import Image
import pyautogui as pag

from re import sub
from time import sleep
import winsound
from threading import Event, Thread

import utils.keysim as ks
from utils.tools import Tools



class SearchSystem(Tools):
	"""Launches search system. Defines hotkeys.
	Waits for new question.
    """
	def __init__(self) -> None:
		super().__init__()

        # see doc folder for more details
		self.cur_img = None
		self.cur_imgTC = None
		self.cur_qn = None
		self.cur_answersRUS = []
		self.cur_answersENG = []
		self.inside_img = None

		self.LOCK_get_img = Event()
		self.LOCK_chq_inner_img = Event()
		self.LOCK_get_key = Event()
		self.LOCK_get_ans = Event()

		self.LOCK_shut_down = Event()

		self.all_crds = {} # description : [start, length]
		self.threads_dict = {"GET_IMG": None,
							 "LOC_ENTRIES_G": None,
							 "LOC_ENTRIES_Y": None,
							 "LOC_TECH_PICS": None,
							 "DETECT_PICTURE": None,
							 "GET_KEY": None,
							 "UNREG_KEYS": None,
							 "CHECK_INSIDE_IMG": None,
							 }

	def add_quot_marks(self):
		"""Adds quotes to peform precise search in google.
		"""
		# wait for release
		while (kb.is_pressed('ctrl')): sleep(0.001)
		if (not self.third_search_G):
			self.locate_entry_G()

        # search entry was not found
		if (self.entry_coords_G is None):
			print("Didn't manage to find entry to insert quotes.")
			return None

		ks.text_to_clipboard(f'"{self.text}"')

		pag.click(self.entry_coords_G)
		sleep(0.001)
		ks.run_press("select_and_paste") # 'ctrl+a', '+v', 'enter'

	def get_answers(self, switch_lang=False):
		"""Extracts answer choices from received image.
		"""
		lock = Event()
		self.run_thread(self.loc_tech_pics, "LOC_TECH_PICS", args=(lock, True))

		self.LOCK_get_ans.wait()

		if (switch_lang):
			ans_text = [0, 0, 0, 0]
			threads = []

			for i in range(4):
				threads.append(Thread(target=self.img2text, args=(i, ans_text, self.ans_imgs[i], "eng")))
				threads[i].start()
			for i in range(4):
				threads[i].join()

			self.cur_answersENG = [i[:i.find('\n')] for i in ans_text]
			text_ans = self.text + ' ' + " ".join(self.cur_answersENG)
		else:
			text_ans = self.text + ' ' + " ".join(self.cur_answersRUS)

		ks.text_to_clipboard(text_ans)

		while (kb.is_pressed('alt')): sleep(0.001)

		lock.wait()
		# Google
		if (self.entry_coords_G):
			pag.click(self.entry_coords_G)
			sleep(0.001)
			ks.run_press("select_and_paste")
		# Yandex
		if (self.entry_coords_Y):
			pag.click(self.entry_coords_Y)
			sleep(0.05)
			ks.run_press("select_and_paste")

		print(f"{' '*len(f'Done! -> {self.qn_num}: ')}{text_ans}")

	def read_text(self):
		"""Recognizes text of question and run websearch.
		"""
		lock = Event()

		self.run_thread(self.loc_tech_pics, "LOC_TECH_PICS", args=(lock,))

		self.LOCK_chq_inner_img.wait()
		if (self.inside_img is not None): # in case we have an unnecessary img inside our qn
			cur_qn = self.cur_qn[:self.inside_img[0]] # crop till the [topy]
		else:
			cur_qn = np.array(self.cur_qn)

		# to GRAY scale -> to BINARY_INV
		cur_qn = cv2.threshold(cv2.cvtColor(cur_qn, cv2.COLOR_RGB2GRAY)[:, 5:-2], 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
		#                                           pytesseract algorithm may see some strange symbols next to the edges
		text = sub("\n", " ", pytesseract.image_to_string(cur_qn, lang='rus', config='--psm 6'))

		self.text = text[:-3].replace("\"", "")
		ks.text_to_clipboard(self.text)

		lock.wait() # entries

		while (kb.is_pressed('ctrl')): sleep(0.001)

		# Google
		if (self.entry_coords_G):
			pag.click(self.entry_coords_G)
			sleep(0.001)
			ks.run_press("select_and_paste")
		# Yandex
		if (self.entry_coords_Y):
			pag.click(self.entry_coords_Y)
			sleep(0.05)
			ks.run_press("select_and_paste")

		print(f"Done! -> {self.qn_num}: {self.text}")

	def search_picture(self):
		"""Peforms reverse image search of self.cur_qn.
		"""
		lock = Event()

		self.run_thread(self.loc_tech_pics, "LOC_TECH_PICS", args=(lock, True))

		self.LOCK_chq_inner_img.wait()

		if (self.inside_img is None):
			self.print_log("Redirected to the 'read_text' function. Inside img was not found. [search_picture]")
			self.read_text()
			return None

		# topy, leftx, bottomy, rightx = self.inside_img
		picture = self.cur_qn[self.inside_img[0]+2:self.inside_img[2]+1, self.inside_img[1]:self.inside_img[3]]

		# put image to clipboard
		output = BytesIO()
		Image.fromarray(picture).save(output, "BMP")
		data = output.getvalue()[14:]
		output.close()
		ks.img_to_clipboard(data)

		while (kb.is_pressed('ctrl')): sleep(0.001)

		lock.wait()
		# search the image in Yandex reverse images search
		if (self.photo_search):
			pag.click([self.photo_search[0], self.photo_search[1] - 5])
			ks.run_press("paste")

		print(f"Done! -> {self.qn_num}: Picture loaded!")

	def turn_on_mics(self):
		if (self.entry_coords_G is None):
			google_mic_coords = self.locate_entry_G(shift=0, update_attributes=False)
		else:
			google_mic_coords = [self.entry_coords_G[0] + 200, self.entry_coords_G[1]]
		if (self.entry_coords_Y is None):
			yandex_mic_coords = self.locate_entry_Y(shift=0, update_attributes=False)
		else:
			yandex_mic_coords = [self.entry_coords_Y[0] + 200, self.entry_coords_Y[1]]

		# Google
		if (google_mic_coords):
			pag.click(google_mic_coords)
		# Yandex
		if (yandex_mic_coords):
			pag.click(yandex_mic_coords)

	def proc_data(self):
		# set to default some settings:
		self.cur_img = None # a raw image straight from the phone screen
		self.cur_imgTC = None # self.cur_img img cropped till the place under timer and above the beginning of the question
		self.cur_qn = None # self.cur_imgTC cropped till the edge between green and white areas
		self.cur_answersRUS = []
		self.cur_answersENG = []
		self.inside_img = None

		self.key = None

		self.LOCK_chq_inner_img.clear()
		self.LOCK_get_img.clear()
		self.LOCK_get_key.clear()

		self.run_thread(self.get_image, "GET_IMG")
		self.run_thread(self.get_key, "GET_KEY")

		self.LOCK_get_key.wait()

		self.run_thread(self.unreg_keys, "UNREG_KEY")

		winsound.Beep(800, 200)

		if (self.key == 's'):
			self.search_picture()
		elif (self.key == 'm'):
			self.turn_on_mics()
		else:
			self.read_text() # here self.key == 'space'

	def main(self):
		kb.add_hotkey('ctrl+q',       self.proc_data,        suppress=False, trigger_on_release=False)
		kb.add_hotkey('ctrl+b',       self.add_quot_marks,   suppress=False, trigger_on_release=False)
		kb.add_hotkey('ctrl+alt+e', self.exit_program,     suppress=False, trigger_on_release=False)
		kb.add_hotkey('ctrl+m',       self.turn_on_mics,     suppress=False, trigger_on_release=False)
		kb.add_hotkey('alt+x',        self.get_answers,      suppress=False, trigger_on_release=False)
		kb.add_hotkey('alt+s',        self.get_answers, args=(True,), suppress=False, trigger_on_release=False)

		kb.add_hotkey('alt+h',        self.hide_kb,          suppress=False, trigger_on_release=False)

		winsound.Beep(2000, 700)
		print("Ready")

		self.LOCK_shut_down.wait()

