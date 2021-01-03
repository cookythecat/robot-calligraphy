# Robot Calligraphy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


![](https://drive.google.com/uc?export=view&id=15ytBxWexWYtei5TXEhPRHRf097GL4-JO)

# Introduction:
The Robot Calligraphy is an App for enabling UR5 to perform traditional Chinese calligraphy. It includes the writing paths extracting module and writing controlling module. The stroke order information and writing paths are obtained from Chinese character teaching GIFs (https://www.hanzi5.com/). 


### Extraction Procedure: 
The extraction module transfers each GIF of its corresponding target Chinese character to an array of JPGs; then it discards JPGs that contain incomplete stroke. Then it would apply gaussian blur to eliminate noises and call the `CV2` `inrange` method to separate stokes with red coloring. It would then use Zhang-Suen thinning to get the thinned image and apply BFS on each pixel to get the stoke's width at that location. The stroke order and writing direction information contained in these GIFs would also be extracted.


### Control:
Control: `calligraphy.robot_writing_logics` would create control points of UR5 tool trajectory for the real world `calligraphy.robot_writing_logics` would call `easy_ur5.py` as API to control the real robot The velocity of tool trajectory is calculated in `easy_ur5.py`

# Setup:
step 1: Download this repository to your PC
  ```shell
  git clone https://github.com/cookythecat/robot-calligraphy.git
  ```
step 2: Download `data` folder from https://drive.google.com/file/d/1EykHtbVGWC1fR7g0C8apqqDcy9ovpkrc/view?usp=sharing. You can directly use `data.json` as the writing path library for robot calligraphy performance. If you want to try the extraction algorithm or want bigger writing paths lib, You can do it by using `cv.py` (you can find a GIFs library with 20000+ GIFs from the data folder). Unzip the `data.zip` file and put the data folder directly under the root of the project.

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
Run `<your workspace>\cv\cv.py`
If you want to see thinned image, input 'yes' 
```shell
show image? 
Please enter yes or no: yes  
```
If you don't want to see thinned image, input 'no' 
```shell
show image? 
Please enter yes or no: no  
```
NOTICE: `data.json` would be rewritten once you run `cv.py`; So if you want to use the default `data.json` provided by us, you need to copy `data.json` from your downloaded `data` folder to `<your workspace>\data\`.  
### Performance:
Run `<your workspace>\calligrahpy\robot_writing_logics.py`, input the size of the character you would like your UR5 to write; Also input the scale factor (a float value, you can try 0.0004 first and then fine-tune this value)

```shell
C:\Users\cooky\Anaconda3\python.exe C:/Users/cooky/PycharmProjects/robotCalligraphy/calligraphy/robot_writing_logics.py
input a string you want to write: 测试
input scale (you can try 0.0004 first): 0.0004
```
 If the local machine cannot connect to your UR5, Please make sure the HOST constant variable in `<your workspace>\calligraphy\easy_ur5.py` matches your robot's HOST.
 
# License

MIT
