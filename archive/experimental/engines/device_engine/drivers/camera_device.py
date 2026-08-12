import cv2

class Driver:

    def capture(self):

        cam = cv2.VideoCapture(0)

        ret, frame = cam.read()

        cam.release()

        return frame
