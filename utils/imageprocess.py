"""Tools for working with images.
Objects recognition, cropping, text extraction and so on.
"""


import collections
import cv2
from io import BytesIO
import numpy as np
from PIL import Image
import os
from time import sleep
import win32clipboard
import utils.keysim as tc

import pathlib
CUR_DIR = pathlib.Path.cwd()


Box = collections.namedtuple('Box', 'left top width height')


class ImageProcessing:
	def __init__(self) -> None:
		self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

		# self.TOP_CROP = 210
		self.qn_count_file = open(os.path.join(CUR_DIR, 'resources\\pictures_number.txt'), 'r')
		self.qn_num = int(self.qn_count_file.read())
		self.qn_count_file.close()

	def get_imageDEBUG(self, path):
		"""Takes input screen from file, not from scrcpy.
		"""
		self.cur_img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
		self.HEIGHT, self.WIDTH, _ = self.cur_img.shape
		self.all_crds["cur_img_H_W"] = [self.HEIGHT, self.WIDTH]

		# process self.cur_img and check image inside
		self.run_thread(self.check_inside_img, "CHECK_INSIDE_IMG")

		# now we have an image matrix in "self.cur_img"
		self.LOCK_get_img.set()

	def get_image(self):
		"""Getting image from clipboard.
		:returns: None
		"""
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

		# saving
		self.qn_num += 1
		cv2.imwrite(os.path.join(CUR_DIR, 'questions_saved', str(self.qn_num) + '.jpg'), cv2.cvtColor(self.cur_img, cv2.COLOR_RGB2BGR)[38:]) # save without white header

		# increasing counter
		self.qn_count_file = open(os.path.join(CUR_DIR, 'resources\\pictures_number.txt'), 'w')
		self.qn_count_file.truncate()
		self.qn_count_file.write(str(self.qn_num))
		self.qn_count_file.close()

	def check_inside_img(self):
		self.all_crds["cur_imgTC"] = [200, self.HEIGHT - 200] # -> relative to cur_img
		self.cur_imgTC = self.cur_img[200:]

		self.all_crds["cur_qn_ans"] = [200] # -> relative to cur_img
		self.cur_qn_ans = self.cur_imgTC[:self.till_ans()]

		self.all_crds["cur_qn"] = [0] # -> relative to cur_qn_ans
		self.cur_qn = self.cur_imgTC[:self.get_qn_end()]

		self.detect_picture()

		if (self.inside_img is None):
			# we didn't find a picture in the question, so, we definitely consider only text search, not reverse photo search
			self.LOCK_get_key.set()

		self.LOCK_chq_inner_img.set()

	def till_ans(self):
		"""Finds the 'answer' button.
		"""
		for y in range(len(self.cur_imgTC) - 5, 0, -10):
			num = np.count_nonzero([np.all(i) for i in (self.cur_imgTC[y] > [235, -1, 235])])
			if (num < self.WIDTH * 0.9):
				self.all_crds["cur_qn_ans"].append(y - 40)
				return (y - 40)

	def get_qn_end(self):
		"""Finds the edge between green and white areas.
		"""
		for y in range(0, len(self.cur_imgTC), 10):
			num = np.count_nonzero([np.all(i) for i in (self.cur_imgTC[y] > [235, -1, 235])])
			if (num > self.WIDTH * 0.95):
				self.all_crds["cur_qn"].append(y - 20)
				return (y - 20)

	def detect_picture(self):
		"""Check picture presence on screen.
		"""
		# some preprocess
		img = cv2.cvtColor(self.cur_qn, cv2.COLOR_RGB2GRAY)

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

	def crop_imgs(self, i, ans_area):
		"""Extracting answers.
		:i: index
		:ans_area: area to be cropped
		:returns: None
		"""
		self.ans_imgs[i] = self.cur_qn_ans[ans_area[0]:ans_area[1], ans_area[2]:ans_area[3]]


def locateAll_opencv(needleImage,
					 haystackImage,
					 region=None,
					 step=1,
					 confidence=0.999
					):
	"""Locates all needleImage's in haystackImage.
	:returns: info about all occurences.
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
