# .. -*- coding: utf-8 -*-
#
# **********************************************************
# cv_video.py - Image processing using a webcam with OpenCV.
# **********************************************************
import cv2
import numpy as np

def main():
    # Open a webcam.
    cap = cv2.VideoCapture(0)
    assert cap.isOpened()

    # Using `waitKey <http://docs.opencv.org/modules/highgui/doc/user_interface.html#waitkey>`_, grab a frame then process it.
    isDone = False
    while not isDone:
        # Wait the minimum amount of time (1 ms) for the user to press a key. This also updates the window contents.
        key = cv2.waitKey(1)

        # Quit if the user presses the Esc key.
        isDone = key == 27

        # Get a frame from the webcam.
        success_flag, image = cap.read()
        assert success_flag

        # Resize it to half size.
        sz = image.shape
        image = cv2.resize(image, (sz[1]/2, sz[0]/2))

        cv2.imshow("Direct from webcam", image)

        # Convert the image to 32-bit floating point: divide by 255, since the range is between 0 and 1, not 0 and 255.
        float_image = image/np.float32(255.0)

        # Reduce the gamma of the image by 1 stop (a factor of 1/2^1).
        diff_image = float_image*np.float32((0.5, 0.5, 0.5))
        cv2.imshow("Diff image", diff_image)

    # Free resources.
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
