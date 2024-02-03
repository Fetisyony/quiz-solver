# Quiz Solver

<p>
<img style="float: right;padding-left: 60px" src="resources\question_example.png" alt="GUI" width="20%">
Quiz solver with the ability of autonomous work.
Uses computer vision algorithms to detect question occurence,
text of question recognition and automatic search on the web.
<br>
It is a wrapper to scrcpy, so the connection is being established via adb and enables constant ability to get picture of screen.

Can process all types of questions:
- question in the form of a test
- questions about given image, peforming reverse image search
- question without answer choices
</p>

## Installation

1. Requires `python3.6` or newer
2. Install dependencies: `pip install -r requirements.txt`
3. Install `tesseract` utility and put path to `tesseract.exe` in `control.py`

## Usage

Run `main.py` and `scrcpy` app preferably no-console. Now access all features with simple control.
Use shortcuts:
- `ctrl+q` to capture screen and run question recognition
- in case program ask you to choose what to do
    - press `space` to search the question itself
    - press `s` to peform reverse image search
- press 
- other features to discover during use
