import ast
import sys

# import numpy

if len(sys.argv) > 1:
    basicParams = ast.literal_eval(sys.argv[1])
    myTank = ast.literal_eval(sys.argv[2])
    listOfTanks = ast.literal_eval(sys.argv[3])
    listOfBullets = ast.literal_eval(sys.argv[4])
else:
    exit(420)


def generateResponse():
    moveForward = -10
    turnTankRight = -3
    fireStrength = 3
    turnGunRight = -10

    print("RESPONSE:{},{},{},{}".format(moveForward, turnGunRight, fireStrength, turnTankRight))


generateResponse()
