import cv2
import keyboard as kb
import numpy as np
import pyautogui as pag
import pytesseract
import os
from time import sleep, time
from threading import Event, Thread
import utils.keysim as tc


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
pag.FAILSAFE = False

class ImageProcessing:
	def __init__(self) -> None:
		self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
		self.inside_img = None

	def draw_on_img(self, coords, img, name):
		img_func =np.array([[list(i) for i in line] for line in img])
		topy,    leftx,  bottomy, rightx = coords
		img_func[topy, leftx] = [255, 0, 0]
		img_func[topy, rightx] = [255, 0, 0]
		img_func[bottomy, leftx] = [255, 0, 0]
		img_func[bottomy, rightx] = [255, 0, 0]
		tc.show_img(img_func)
		tc.save_img(img_func)

	def draw_contours_show(self, img, contours):
		test_img = np.array([[list(i) for i in line] for line in img])
		cv2.drawContours(test_img, contours, contourIdx=-1, color=(255, 0, 0), thickness=1, lineType=cv2.LINE_AA)
		tc.show_img(test_img)

	def draw_rect_show(self, img, contour):
		x,y,w,h = contour
		test_img = np.array([[list(i) for i in line] for line in img])
		cv2.rectangle(test_img, (x, y), (x+w, y+h), (0, 0, 255), 1)
		tc.show_img(test_img)

	def get_image(self, img_path):
		self.inside_img = None
 
		self.cur_img = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
		self.HEIGHT, self.WIDTH, _ = self.cur_img.shape

		self.cur_qn = self.cur_img[170:]
		self.cur_qn = self.cur_qn[:self.get_qn_end()]

		self.detect_picture()

		if (self.inside_img is None):
			print("inside_img not found")
	def get_qn_end(self):
		"""Finds the beginning of white area.
		"""
		for y in range(0, len(self.cur_qn), 10):
			num = np.count_nonzero([np.all(i) for i in (self.cur_qn[y] > [235, -1, 235])])
			if (num > self.WIDTH * 0.95): # if num / 440 > 0.95:
				return (y - 20)

	def detect_picture(self):
		img = cv2.cvtColor(self.cur_qn, cv2.COLOR_RGB2GRAY)

		# img = cv2.bilateralFilter(src=self.cur_qn, d=9, sigmaColor=75, sigmaSpace=75)
		img = cv2.GaussianBlur(img, (3, 3), 0)
		img = cv2.Canny(img, 25, 40)
		img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, self.kernel)

		tc.show_img(img)

		contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]

		if (contours is None):
			return None

		cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0]
		self.draw_contours_show(self.cur_qn, [cnt])

		epsilon = 0.04 * cv2.arcLength(cnt, True)
		approx_corners = cv2.approxPolyDP(cnt, epsilon, True)
		print("approx_area:", cv2.contourArea(approx_corners))
		
		self.draw_contours_show(self.cur_qn, [approx_corners])
		self.draw_rect_show(self.cur_qn, cv2.boundingRect(cnt))
		x, y, w, h = cv2.boundingRect(cnt)
		print("rect_area:", w * h)

		if (cv2.contourArea(cnt) < 10000):
			print(f"It is not a picture because: cv2.contourArea(cnt) < 1000 => ({cv2.contourArea(cnt)})")
			return None
		
		if (len(approx_corners) < 4):
			print(f"It is not a picture because: len(approx_corners) < 4 => ({len(approx_corners)})")
			return None

		approx_corners = np.concatenate(approx_corners)
		xs, ys = zip(*approx_corners)

		if (abs(ys[0] - ys[1]) < 30):
			print(f"It is not a picture because: abs(ys[0] - ys[1]) < 30 => ({ys[0] - ys[1]}) ")
			return None

		#                 ( topy,    leftx,  bottomy, rightx )
		self.inside_img = (min(ys), min(xs), max(ys), max(xs))
		print("inside_img:", self.inside_img)
		self.draw_on_img(self.inside_img, self.cur_qn, "corners")


folder_path = "C:\\Users\\Admin\\Desktop\\Mine\\PROGRAMMING\\projects\\Press_immitation\\quiz\\resources\\debug_pictures\\"
pictures = [("1.jpg", True),
			("10.jpg", False),
			("13.jpg", False),
			("14.jpg", False),
			("16.jpg", False),
			("17.jpg", False),
			("2.jpg", False),
			("20210714_190245.jpg", True),
			("21.jpg", True),
			("3.jpg", True),
			("36.jpg", False),
			("4.jpg", True),
			("44.jpg", True),
			("45.jpg", False),
			("5.jpg", True),
			("6.jpg", True),
			("61.jpg", False),
			("62.jpg", False),
			("68.jpg", False),
			("7.jpg", True),
			("8.jpg", False),
			# ("9.jpg", True),
			]

"""
cv2.imshow("Cropped Image", image) - implemented in toolscollection but not used by default
"""

if "__main__" == __name__:
	img_proc = ImageProcessing()

	# "get_image" finds "question end", crops image and runs "detect_picture" (to detect inside picture if it exists)
	for name, contain_pic in pictures:
		# if (not contain_pic): continue
		full_path = folder_path + name
		img_proc.get_image(full_path)
		print('\n')
		kb.wait("space")