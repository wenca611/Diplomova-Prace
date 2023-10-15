import ast
import sys
import random as rnd
import logging
import site

sys.path.append(r'D:\FEKT\Ing\diplomka\RoboCode\RoboCode\venv\Lib\site-packages')
print("sys.path:", sys.path)
site_packages = site.getsitepackages()
print("Umístění všech site-packages:", site_packages)

# Nastavení logovacího souboru
logging.basicConfig(filename='errors.log', level=logging.ERROR)

try:
    import numpy as np
except ImportError:
    error_msg = "Chyba: Numpy nelze načíst. Ujistěte se, že máte tyto knihovny nainstalované."
    logging.error(error_msg)
    sys.exit(1)

if len(sys.argv) == 5:
    basicParams = ast.literal_eval(sys.argv[1])
    myTank = ast.literal_eval(sys.argv[2])
    listOfTanks = ast.literal_eval(sys.argv[3])
    listOfBullets = ast.literal_eval(sys.argv[4])
else:
    exit(1)


# basicParams = ast.literal_eval("[800,600]")
#
# myTank = ast.literal_eval(
# 	"[65.0,-3.5,5.8230205626818385,1.9832962082943324,0.7999999999999997,232.26827171238176,226.30317878637314,0]")
#
# listOfTanks = ast.literal_eval(
# 	"[[88.0,-4.0,2.366363565550951,2.366363565550951,0.6,98.29499535215871,24.020248063887227,0], " \
# 	"[101.0,0.0,4.71238898038469,2.4085543677521777,0.0,18.0,582.0,0], " \
# 	"[85.0,-3.0,3.9793506945470742,3.193952531149622,0.0,483.73344344939414,102.55663052621038,0]] ")
#
# listOfBullets = ast.literal_eval("[[2.4085543677521777,461.6335920159215,89.29498070848638,1.0], " \
# 								 "[1.5469638952957507,698.0918554698923,223.31099556972507,3.0], " \
# 								 "[2.4085543677521777,347.881388934916,215.62960103964372,1.0], " \
# 								 "[2.9781338819311,321.5879391600116,-5.710270443620345,3.0], " \
# 								 "[1.493698939553786,485.51166197489704,80.68061540795992,1.0], " \
# 								 "[2.4085543677521777,177.25308431340773,405.1315315363797,1.0], " \
# 								 "[4.409303868566449,148.02065396941026,226.8346004995168,3.0]]")

def countState():
    if not listOfBullets or not listOfTanks:
        return 0

    state = 5
    for bullet in listOfBullets:
        state += bullet[2] * bullet[0]

    for tank in listOfTanks:
        state -= tank[0] * tank[4]
    state = state // (len(listOfBullets) * len(listOfTanks)) + 1

    return state % 5


def generateResponse():
    error_msg = "Delky dat: " + str(len(basicParams)) + " " + str(len(myTank)) + " " + str(len(listOfTanks)) + \
                " " + str(len(listOfBullets))
    logging.error(error_msg)
    logging.error("Vnitřní data1(zakladni param): " + str(basicParams))
    logging.error("Vnitřní data2(muj tank): " + str(myTank))
    logging.error("Vnitřní data3(ostatni tanky): " + str(listOfTanks))
    logging.error("Vnitřní data4(strely): " + str(listOfBullets))

    rewards = np.array([
        [100, -80, 2, 45],
        [-42, 69, 3, 78],
        [197, 125, 0, 20],
        [-200, -45, 4, 100],
        [70, 15, 5, -64]])

    state = int(countState())
    print(state)
    print("RESPONSE:{},{},{},{}".format(rewards[state][0],
                                        rewards[state][1],
                                        rewards[state][2],
                                        rewards[state][3]))


generateResponse()
