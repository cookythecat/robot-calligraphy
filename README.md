# robot-calligraphy

The robot-calligraphy application repo

Use cv.cv to exract and store the writing paths of 3000+ commonly use Chinese characters.
Use calligrapht.robot_writing_logics to let UR5 write.


Path and stroke width extraction:
By chronologically parsing the GIFs, the stroke order information can be obtained.


Procedure:
Transfer the GIF of a given character to an array of JPGs
Only keep the JPGs that contain a whole stroke
Apply gaussian blur to eliminate noises
Apply  CV2 inrange method to separate the red stroke
Apply Zhang-Suen thinning to get the thinned image
Apply BFS on each pixel to get the width of the stoke at that location



No unit tests contained in this application, since tests are done by real robot experiments.
