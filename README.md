# Quiz Solver

<p>
<img style="padding-left: 50px;" align="right" src="resources\question_example.png" alt="GUI" width="20%" hspace=15>
<br>Quiz solver with the ability of autonomous work. <br>Uses computer vision algorithms to detect question occurence,
text recognition and automatic search on the web.
<br><br>
&emsp;It is a wrapper to scrcpy, so the connection is being established via adb and enables constant ability to get picture of screen.

Can process all types of questions:
- question in the form of a test
- questions about given image, performing reverse image search
- question without answer choices
</p>
<br>

## Installation

1. Requires `python3.6` or newer
2. Install dependencies: `pip install -r requirements.txt`
3. Install `tesseract` utility and put path to `tesseract.exe` in `control.py`

## Usage

Run `main.py` and `scrcpy` app preferably no-console. Now access all features with simple control.
Use shortcuts:
- `ctrl+q` to capture screen, run question recognition and answer search
- in case program asks you to choose what to do
    - press `space` to search the question itself
    - press `s` to perform reverse image search
- `ctrl+b` to perform a precise search
- other features to discover during use

