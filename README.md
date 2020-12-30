# Robot Calligraphy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


![](https://drive.google.com/uc?export=view&id=15ytBxWexWYtei5TXEhPRHRf097GL4-JO)

# Introduction:
The Robot Calligraphy is an App for enabling UR5 perform traditional Chinese calligraphy. It includes writing paths extracting module and writing controlling module. By chronologically parsing the GIFs, the stroke order information can be obtained.


### Extraction Procedure: 
Transfer the GIF of a given character to an array of JPGs Only keep the JPGs that contain a whole stroke Apply gaussian blur to eliminate noises Apply CV2 inrange method to separate the red stroke Apply Zhang-Suen thinning to get the thinned image Apply BFS on each pixel to get the width of the stoke at that location

### Control:
Control: calligraphy.robot_writing_logics would create control points of UR5 tool trajectory for the real world calligraphy.robot_writing_logics would call easy_ur5.py as API to control the real robot The velocity of tool trajectory is calculated in easy_ur5.py

# Setup:
step 1: Download this repository to your PC
  ```shell
  git clone https://github.com/cookythecat/robot-calligraphy.git
  ```
step 2: Download data folder from https://drive.google.com/file/d/1an2gXKffbX_WSDOqu2Fo3RlClhHRknU7/view?usp=sharing. You can directly use data.json as the writing path library for robot calligraphy performance. You can extract paths from 20000+ GIFs library if you want to try exraction algorithrm or you want bigger writing paths lib. Unizip data.zip file and pult data folder directly under the root of the project.

step 3: Dependencies
This implementation requires the following dependencies:
  - numpy~=1.16.5
  - Dopencv-python~=4.4.0.44
  - pillow~=6.2.0

you can try:
  ```shell
  pip install -r requirement.txt
  ```

# Running Guidelines:
 ### Extraction: 
You can run extract_and_save() in cv/cv.py once you have data folder under the root of the project. The result file data.json would be stored in data/ folder. Please comment the following two lines of code under parse_gif() if you to get a new library of writing paths.

    cv2.imshow('union', union_map)
    cv2.waitKey()

### Performance:
Run calligrahpy/robot_writing_logics.py to let UR5 do robot calligraphy. Set your UR5 to the remote control model, and uncomment this line.
  ```shell
  #MACHINE = easy_ur5.EasyUr5()
  ```
 Please make sure the HOST constant variable in calligraphy/easy_ur5.py match your robot's HOST.
 
License
----

MIT
