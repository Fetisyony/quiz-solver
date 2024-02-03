import main as mn

import collections
import cv2
import ctypes, ctypes.wintypes
from io import BytesIO
import keyboard as kb
import numpy as np
from PIL import Image
import pyautogui as pag
import pytesseract
from re import sub
import os
import subprocess
from time import sleep, time, localtime
import win32clipboard
from win32con import VK_SPACE
import winsound
from threading import Event, Thread
import utils.keysim as tc


CUR_DIR = os.path.dirname(os.path.realpath(__file__))
Box = collections.namedtuple('Box', 'left top width height')


class ImageProcessing(mn.ImageProcessing):
	def get_imageDEBUG(self, path):
		self.cur_img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
		self.HEIGHT, self.WIDTH, _ = self.cur_img.shape
		self.all_crds["cur_img_H_W"] = [self.HEIGHT, self.WIDTH]
		# print(self.cur_img.shape)

		self.run_thread(self.check_inside_img, "CHECK_INSIDE_IMG") # process self.cur_img and check image inside

		self.LOCK_get_img.set() # now we have an image matrix in "self.cur_img"

	def get_image(self):
		last = win32clipboard.GetClipboardSequenceNumber()

		tc.run_press("screen")

		while (last + 4 != win32clipboard.GetClipboardSequenceNumber()):
			sleep(0.001)
		sleep(0.004)

		try:
			win32clipboard.OpenClipboard()
		except:
			self.print_log("Trying to open keyboard again (self.qn_num) [get_image]", print_msg=True)
			sleep(0.01)
			win32clipboard.OpenClipboard()

		img_bit = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
		win32clipboard.CloseClipboard()

		im = Image.open(BytesIO(img_bit))
		self.cur_img = np.asarray(im)
		self.HEIGHT, self.WIDTH, _ = self.cur_img.shape
		self.all_crds["cur_img_H_W"] = [self.HEIGHT, self.WIDTH]

		self.run_thread(self.check_inside_img, "CHECK_INSIDE_IMG") # process self.cur_img and check image inside

		self.LOCK_get_img.set() # now we have an image matrix in "self.cur_img"

		self.qn_num += 1
		cv2.imwrite(os.path.join(CUR_DIR, 'questions_saved', str(self.qn_num) + '.jpg'), cv2.cvtColor(self.cur_img, cv2.COLOR_RGB2BGR))

		self.qn_count_file = open(os.path.join(CUR_DIR, 'resources\\pictures_number.txt'), 'w')
		self.qn_count_file.truncate()
		self.qn_count_file.write(str(self.qn_num))
		self.qn_count_file.close()

	def check_inside_img(self):
		self.all_crds["cur_imgTC"] = [200, self.HEIGHT - 200] # -> relative to cur_img
		self.cur_imgTC = self.cur_img[200:]

		self.all_crds["cur_qn_ans"] = [200] # -> relative to cur_img
		self.cur_qn_ans = self.cur_imgTC[:self.till_ans()]

		self.run_thread(self.get_avail_anssDEBUG, "GET_AVAIL_ANS")

		self.all_crds["cur_qn"] = [0] # -> relative to cur_qn_ans
		self.cur_qn = self.cur_imgTC[:self.get_qn_end()]

		self.detect_picture()

		if (self.inside_img is None):
			# we didn't find a picture in the question, so, we definitely consider only text search, not reverse photo search
			self.LOCK_get_key.set()

		self.LOCK_chq_inner_img.set()

	def till_ans(self):
		"""Finds the 'Отправить ответ' button.
		"""
		for y in range(len(self.cur_imgTC) - 5, 0, -10):
			num = np.count_nonzero([np.all(i) for i in (self.cur_imgTC[y] > [235, -1, 235])])
			if (num < self.WIDTH * 0.9):
				self.all_crds["cur_qn_ans"].append(y - 40)
				return (y - 40)

	def get_qn_end(self):
		"""Finds the beginning of white area.
		"""
		for y in range(0, len(self.cur_imgTC), 10):
			num = np.count_nonzero([np.all(i) for i in (self.cur_imgTC[y] > [235, -1, 235])])
			if (num > self.WIDTH * 0.95):
				self.all_crds["cur_qn"].append(y - 20)
				return (y - 20)

	def detect_picture(self):
		img = cv2.cvtColor(self.cur_qn, cv2.COLOR_RGB2GRAY)

		# img = cv2.GaussianBlur(img, (3, 3), 0)
		img = cv2.Canny(img, 25, 40)
		img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, self.kernel)

		contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]

		if (contours is None):
			self.inside_img = None
			return None

		cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0]
		epsilon = 0.04 * cv2.arcLength(cnt, True)
		approx_corners = cv2.approxPolyDP(cnt, epsilon, True)

		if (cv2.contourArea(cnt) < 8000 or len(approx_corners) != 4):
			self.inside_img = None
			return None

		approx_corners = np.concatenate(approx_corners)
		xs, ys = zip(*approx_corners)

		#                 ( topy,    leftx,  bottomy, rightx )
		self.inside_img = (min(ys), min(xs), max(ys), max(xs))
		self.all_crds["inside_img"] = self.inside_img
		print(self.inside_img)

	def crop_imgs(self, i, ans_area):
		self.ans_imgs[i] = self.cur_qn_ans[ans_area[0]:ans_area[1], ans_area[2]:ans_area[3]]

	def img2text(self, i, arr, ans_img):
		arr[i] = pytesseract.image_to_string(cv2.threshold(cv2.cvtColor(ans_img, cv2.COLOR_RGB2GRAY), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1], lang='rus', config='--psm 6')

	def get_avail_anss(self):
		radio_crds = locateAll_opencv(self.ans_circle,
									  self.cur_qn_ans,
									  region=None,
									  step=1,
									  confidence=0.91
									  )

		if (len(radio_crds) < 4):
			print(f"Found less than 4 answers ticks! ({len(radio_crds)})")

			radio_crds = locateAll_opencv(self.ans_circle,
										  self.cur_qn_ans,
										  region=None,
										  step=1,
										  confidence=0.85
										  )
			if (len(radio_crds) < 4):
				print("I think here is no answers to choose.")
				self.cur_answers = []
				self.LOCK_get_ans.set()
				return

		if (len(radio_crds) > 4):
			print(f"Found more than 4 answers ticks! ({len(radio_crds)})")

			radio_tmp = [radio_crds[0]]

			for i in range(1, len(radio_crds)):
				already = False
				for addedC in radio_tmp:
					if (abs(radio_crds[i].left - addedC.left) < 5 and abs(radio_crds[i].top - addedC.top) < 5):
						already = True
						break
				if (not already):
					radio_tmp.append(radio_crds[i])
			radio_crds = radio_tmp

			if (len(radio_crds) != 4):
				print("ALARM")
				print(f"Found repeatedly more than 4 answers ticks! ({len(radio_crds)})")
				return

		ans_areas = []
		for i in range(len(radio_crds)):
			if (len(radio_crds) != i + 1):
				ans_areas.append([radio_crds[i].top - 5,      radio_crds[i + 1].top - 5,       radio_crds[i].left + radio_crds[i].width, self.WIDTH - 5]) # top, bottom, left, right
			else:
				ans_areas.append([radio_crds[i].top - 5, self.all_crds["cur_qn_ans"][1] - 5, radio_crds[i].left + radio_crds[i].width, self.WIDTH - 5]) # top, bottom, left, right

		self.ans_imgs = [0, 0, 0, 0]
		threads = []

		for i in range(4):
			threads.append(Thread(target=self.crop_imgs, args=(i, ans_areas[i])))
			threads[i].start()
		for i in range(4):
			threads[i].join()

		ans_text = [0, 0, 0, 0]
		threads = []

		for i in range(4):
			threads.append(Thread(target=self.img2text, args=(i, ans_text, self.ans_imgs[i])))
			threads[i].start()
		for i in range(4):
			threads[i].join()

		self.cur_answers = [i[:i.find('\n')] for i in ans_text]

		self.LOCK_get_ans.set()

	def get_avail_anssDEBUG(self):
		tc.show_img(self.cur_qn_ans)

		m = time()

		radio_crds = locateAll_opencv(self.ans_circle,
								self.cur_qn_ans,
								region=None,
								step=1,
								confidence=0.91
								)
		print("Found coords -", len(radio_crds))

		if (len(radio_crds) < 4):
			print(f"Found less than 4 answers ticks! ({len(radio_crds)})")

			radio_crds = locateAll_opencv(self.ans_circle,
										  self.cur_qn_ans,
										  region=None,
										  step=1,
										  confidence=0.85
										  )
			if (len(radio_crds) < 4):
				print("I think here is no answers to choose.")
				self.cur_answers = []
				self.LOCK_get_ans.set()
				return

		if (len(radio_crds) > 4):
			print(f"Found more than 4 answers ticks! ({len(radio_crds)})")

			radio_tmp = [radio_crds[0]]

			for i in range(1, len(radio_crds)):
				already = False
				for addedC in radio_tmp:
					if (abs(radio_crds[i].left - addedC.left) < 5 and abs(radio_crds[i].top - addedC.top) < 5):
						already = True
						break
				if (not already):
					radio_tmp.append(radio_crds[i])
			radio_crds = radio_tmp

			if (len(radio_crds) != 4):
				print("ALARM")
				print(f"Found repeatedly more than 4 answers ticks! ({len(radio_crds)})")
				return


		print("Found coords -", len(radio_crds))
		ans_areas = []
		for i in range(len(radio_crds)):
			if (len(radio_crds) != i + 1):
				ans_areas.append([radio_crds[i].top - 5,      radio_crds[i + 1].top - 5,       radio_crds[i].left + radio_crds[i].width, self.WIDTH - 5]) # top, bottom, left, right
			else:
				ans_areas.append([radio_crds[i].top - 5, self.all_crds["cur_qn_ans"][1] - 5, radio_crds[i].left + radio_crds[i].width, self.WIDTH - 5]) # top, bottom, left, right

			# self.cur_qn_ans[int(radio_crds[i].top + radio_crds[i].height / 2)][int(radio_crds[i].left + radio_crds[i].width / 2)] = [255, 0, 0]
		# tc.show_img(self.cur_qn_ans)

		# <<===== test start =====>>
		self.ans_imgs = [0, 0, 0, 0]
		threads = []

		for i in range(4):
			threads.append(Thread(target=self.crop_imgs, args=(i, ans_areas[i])))
			threads[i].start()

		for i in range(4):
			threads[i].join()
		# <<=====  test end  =====>>

		# for ans_img in self.ans_imgs:
		# 	tc.show_img(ans_img)

		# <<===== test start =====>>
		ans_text = [0, 0, 0, 0]
		threads = []

		for i in range(4):
			threads.append(Thread(target=self.img2text, args=(i, ans_text, self.ans_imgs[i])))
			threads[i].start()

		for i in range(4):
			threads[i].join()
		# <<=====  test end  =====>>

		self.cur_answers = [i[:i.find('\n')] for i in ans_text]
		print("\nTime:", time() - m)

		print()
		print_list(self.cur_answers)

		self.LOCK_get_ans.set()



class Tools(mn.Tools, ImageProcessing):
	def __init__(self) -> None:
		super().__init__()

		# 				  cv2.imread(os.path.join(CUR_DIR, 'resources\\tech_pics\\ans_circle.png'))
		self.ans_circle = cv2.imread('C:\\Users\\Admin\\Desktop\\Mine\\PROGRAMMING\\projects\\Press_immitation\\quiz\\resources\\tech_pics\\ans_circle.png')

class SearchSystem(mn.SearchSystem, Tools):
	def __init__(self) -> None:
		super().__init__()

		self.all_crds = {} # decription : [start, length]
		self.cur_img = None
		self.cur_imgTC = None
		self.cur_qn = None
		self.cur_answers = []

		self.LOCK_get_ans = Event()

	def get_answers(self):
		self.LOCK_get_ans.wait()

		print_list(self.cur_answers)



def print_list(lst):
	for i in lst:
		print(i)

def print_dict(dct):
	for i in dct:
		print(i, ':', dct[i])


def locateAll_opencv(needleImage,
					 haystackImage,
					 region=None,
					 step=1,
					 confidence=0.999
					):
	"""
	TODO - rewrite this
		faster but more memory-intensive than pure python
		step 2 skips every other row and column = ~3x faster but prone to miss;
			to compensate, the algorithm automatically reduces the confidence
			threshold by 5% (which helps but will not avoid all misses).
		limitations:
		  - OpenCV 3.x & python 3.x not tested
		  - RGBA images are treated as RBG (ignores alpha channel)
	"""

	needleHeight, needleWidth = needleImage.shape[:2]

	if region:
		haystackImage = haystackImage[region[1]:region[1]+region[3],
									  region[0]:region[0]+region[2]]
	else:
		region = (0, 0)  # full image; these values used in the yield statement
	if (haystackImage.shape[0] < needleHeight or
		haystackImage.shape[1] < needleWidth):
		# avoid semi-cryptic OpenCV error below if bad size
		raise ValueError('needle dimension(s) exceed the haystack image or region dimensions')

	if step == 2:
		confidence *= 0.95
		needleImage = needleImage[::step, ::step]
		haystackImage = haystackImage[::step, ::step]
	else:
		step = 1

	# get all matches at once, credit: https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-np-image/9253805#9253805
	result = cv2.matchTemplate(haystackImage, needleImage, cv2.TM_CCOEFF_NORMED)
	match_indices = np.arange(result.size)[(result > confidence).flatten()]
	matches = np.unravel_index(match_indices, result.shape)

	if len(matches[0]) == 0:
		return []

	# use a generator for API consistency:
	matchx = matches[1] * step + region[0]  # vectorized
	matchy = matches[0] * step + region[1]

	return [Box(x, y, needleWidth, needleHeight) for x, y in zip(matchx, matchy)]



def main(img_name):
	search_sys = SearchSystem()
	search_sys.get_imageDEBUG(CUR_DIR + f'\\questions\\{img_name}')

	search_sys.LOCK_chq_inner_img.clear()
	search_sys.LOCK_get_img.clear()

	search_sys.LOCK_chq_inner_img.wait()

	# tc.show_img(search_sys.cur_qn)
	# tc.show_img(search_sys.cur_img)
	# tc.show_img(search_sys.cur_qn_ans)

	search_sys.LOCK_get_ans.wait()

	# <==== works correctly ====>
	return


if __name__ == "__main__":
	# main("36.jpg")

	# kb.wait('n')

	for img_name in os.listdir("questions")[os.listdir("questions").index("36.jpg"):]:
		print("=====", img_name, "=====")
		main(img_name)
		kb.wait('n')
		print('\n')