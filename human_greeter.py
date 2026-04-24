# -*- encoding: UTF-8 -*-

import sys
import time
import datetime

from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule

from optparse import OptionParser
from threading import Thread

from PIL import Image


NAO_IP = "nao.local" # "10.0.7.13"
NAO_PORT = 9559

# Global variable to store the HumanGreeter module instance
HumanGreeter = None
# memory = None
personDetectionData = None
motion = None
posture = None
cam = None

class HumanGreeterModule(ALModule):
    """ A simple module able to react
    to facedetection events

    """
    def __init__(self, name):
        self.fd = False
        ALModule.__init__(self, name)

        # Create a proxy to ALTextToSpeech for later use
        global tts
        tts = ALProxy("ALTextToSpeech")

        global motion
        motion = ALProxy("ALMotion")
        global posture
        posture = ALProxy("ALRobotPosture")
        global cam
        cam = ALProxy("ALVideoDevice")

        global memory
        memory = ALProxy("ALMemory")
        memory.subscribeToEvent("FaceDetected", "HumanGreeter", "setPersonDetection")

        motion.wakeUp()
        posture.goToPosture("StandInit", 0.8)

        motion.angleInterpolation("HeadPitch", -0.5, 1, True)

        self.stop = False

    def setPersonDetection(self):
        memory.unsubscribeToEvent("FaceDetected", "HumanGreeter")
        global personDetectionData
        personDetectionData = True
        print("set person detection")
        motion.stopMove()

    def turn(self):
        time.sleep(1)
        motion.move(0.005, 0, 0.1*3.141)
        print("Turn around.")

    def walkToPerson(self):
        motion.move(1, 0, 0)
        print("Walk to person.")

    def greetPerson(self):
        time.sleep(1)
        tts.say("Hello Human. Nice to meet you. I'm Nao. \
                    Let me take a picture of you.")
        self.takePicture()
        tts.say("Awesome, that looks great. See you next time.")
        print("Greet person.")

    def takePicture(self):
        resolution = 2    # VGA
        colorSpace = 11   # RGB

        videoClient = cam.subscribe("python_client", resolution, colorSpace, 5)

        t0 = time.time()

        # Get a camera image.
        # image[6] contains the image data passed as an array of ASCII chars.
        naoImage = cam.getImageRemote(videoClient)

        t1 = time.time()

        # Time the image transfer.
        print("acquisition delay ", t1 - t0)

        cam.unsubscribe(videoClient)

        # Get the image size and pixel array.
        imageWidth = naoImage[0]
        imageHeight = naoImage[1]
        print(imageHeight)
        array = naoImage[6]

        # Create a PIL Image from our pixel array.
        im = Image.frombytes("RGB", (imageWidth, imageHeight), array)

        # Save the image.
        im.save("images/camImage_"+str(datetime.datetime.now())+".png", "PNG")

        print("Image is saved")
        time.sleep(1)

    def saveImg(self):
        print("save Image")
        while not self.stop:
            self.takePicture()
            time.sleep(5)


    def phasing(self):
        # global photograph
        # photograph = Thread(target=self.saveImg)
        # photograph.start()

        # global personDetecter
        # personDetecter = Thread(target=self.setPersonDetection)
        # personDetecter.start()
        # print("Started setPersonDetection Thread")

        while personDetectionData is None:
            turnThread = Thread(target=self.turn)
            turnThread.start()
            turnThread.join()

        walkToPersonThread = Thread(target=self.walkToPerson)
        walkToPersonThread.start()
        walkToPersonThread.join()

        greetThread = Thread(target=self.greetPerson)
        greetThread.start()
        greetThread.join()

        motion.stopMove()
        print("Phasing done")
        motion.rest()
        # self.stop = True


def main():
    """ Main entry point

    """
    parser = OptionParser()
    parser.add_option("--pip",
        help="Parent broker port. The IP address or your robot",
        dest="pip")
    parser.add_option("--pport",
        help="Parent broker port. The port NAOqi is listening to",
        dest="pport",
        type="int")
    parser.set_defaults(
        pip=NAO_IP,
        pport=NAO_PORT)

    (opts, args_) = parser.parse_args()
    pip   = opts.pip
    pport = opts.pport

    # We need this broker to be able to construct
    # NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = ALBroker("myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       pip,         # parent broker IP
       pport)       # parent broker port


    # Warning: HumanGreeter must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global HumanGreeter
    HumanGreeter = HumanGreeterModule("HumanGreeter")

    global personDetectionData
    HumanGreeter.phasing()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("Interrupted by user, shutting down")
        myBroker.shutdown()
        sys.exit(0)



if __name__ == "__main__":
    main()
