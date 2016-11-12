#! /usr/bin/python
#
# http://blog.ayoungprogrammer.com/2013/03/tutorial-creating-multiple-choice.html/
#
import cv2

import sys
#img = cv2.imread(sys.argv[1], cv2.IMREAD_COLOR)	# cv2.IMREAD_UNCHANGED
img = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)

img = cv2.GaussianBlur(img, (9,9), 0)

# ADAPTIVE_THRESH_MEAN_C or ADAPTIVE_THRESH_GAUSSIAN_C 
# THRESH_BINARY or THRESH_BINARY_INV
img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 0)


cv2.imshow('image',img)
cv2.waitKey(0)
cv2.destroyAllWindows()


# cv2.adaptiveThreshold(src, maxValue, adaptiveMethod, thresholdType, blockSize, C[, dst]) -> dst

# adaptiveThreshold(img, img,255,CV_ADAPTIVE_THRESH_MEAN_C, CV_THRESH_BINARY,75,10);  
# cv::bitwise_not(img, img);
