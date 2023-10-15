"""
RoboCode AI trainer

Name: robocode_rl_trainer.py
Description: Optimization of control using reinforcement learning on the Robocode platform
Autor: Bc. Václav Pastušek
Creation date: 15. 10. 2023
Last update: 15. 10. 2023
School: BUT FEEC
VUT number: 204437
Python version: 3.11.6
"""

# Standard libraries:
try:
    #import platform  # Access to underlying platform’s identifying data
    import os  # Miscellaneous operating system interfaces
    #from typing import Union, Callable, Optional, Generator  # Support for type hints
    #import functools  # Higher-order functions and operations on callable objects
    #import itertools  # Functions creating iterators for efficient looping
    #import signal  # Set handlers for asynchronous events
    #import re  # Regular expression operations
    #import time as tim  # Time access and conversions
    #import concurrent.futures  # Launching parallel tasks
except ImportError as L_err:
    print("Chyba v načtení standardní knihovny: {0}".format(L_err))
    exit(1)
except Exception as e:
    print(f"Jiná chyba v načtení standardní knihovny: {e}")
    exit(1)

# Third-party libraries:
try:
    import tensorflow as tf

    # Libraries for web scraping
    #import requests  # HTTP library for sending requests
    #from bs4 import BeautifulSoup  # Library for parsing HTML and XML documents

    # Data manipulation and analysis
    #import xarray as xr  # Library for working with labeled multi-dimensional arrays
    #import numpy as np  # Fundamental package for scientific computing
    #from scipy.stats import skew, kurtosis, hmean, gmean, linregress  # Library for statistics and regression analysis
    #from scipy.fftpack import dct  # Library for discrete cosine transform

    # Visualization
    #import tqdm  # displaying progress bars
    #import matplotlib.pyplot as plt  # Library for creating static, animated, and interactive visualizations
    #import matplotlib as mpl  # Library for customization of matplotlib plots
    #import matplotlib.colors as mcolors  # Library for color mapping and normalization

    # User interaction
    #import keyboard  # Library for detecting keyboard input
except ImportError as L_err:
    print("Chyba v načtení knihovny třetích stran: {0}".format(L_err))
    exit(1)
except Exception as e:
    print(f"Jiná chyba v ačtení knihovny třetích stran: {e}")
    exit(1)

import re
import subprocess
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # TODO

# Globals for game.properties
game_width: int = 800  # game width: 800
game_height: int = 600  # game height: 600
numberOfRounds: int = 10  # number of rounds: 10
isVisible: bool = True  # Game is visible: True

enemies: dict = {
    0: "",
    1: "Corners",
    2: "Crazy",
    3: "Fire",
    4: "Interactive",
    5: "Interactive_v2",
    6: "MyFirstJuniorRobot",
    7: "MyFirstRobot",
    8: "PaintingRobot",
    9: "RamFire",
    10: "SittingDuck",
    11: "SpinBot",
    12: "Target",
    13: "Tracker",
    14: "TrackFire",
    15: "VelociRobot",
    16: "Walls",
    17: "PyRobotClient"
}

opponent_list: str = "Crazy, 13, 17"  # "Crazy, 13, 17"

# Rozdělit seznam protivníků podle čárky a odstranit případné mezery
opponents: list[str] = [opponent.strip() for opponent in opponent_list.split(",")]
# Převést čísla na jména protivníků
opponents_with_names: list[str] = [enemies[int(opponent)] if opponent.isdigit() else opponent for opponent in opponents]
# Vytvořit nový řetězec pro seznam protivníků
opponent_list: str = ", ".join(opponents_with_names)

# Globals for robocode.properties









layer_sizes: list[int] = [1024, 4]  # [1024, 2**11, 2**11, 4]

"""def create_model():
    global layer_sizes
    if len(layer_sizes) < 3:
        del layer_sizes
        layer_sizes = [1024, 4]

    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Input(shape=(layer_sizes[0],)))

    for size in layer_sizes[1:-1]:
        model.add(tf.keras.layers.Dense(size, activation='relu'))

    # Výstupní vrstva s lineární aktivační funkcí a počet výstupů dle poslední hodnoty v seznamu
    model.add(tf.keras.layers.Dense(layer_sizes[-1], activation='linear'))

    return model


create_model()

path_to_java_server: str = "RoboCode/src/cz/vutbr/feec/robocode/battle/RobocodeRunner.java"

# Open for read
with open(path_to_java_server, "r") as server_file:
    content = server_file.read()

new_content = re.sub(r'BattlefieldSpecification\(\s*\d+\s*,\s*\d+\s*\)',
                     f'BattlefieldSpecification({game_width}, {game_height})',
                     content)

new_content = re.sub(
    r'numberOfRounds\s*=\s*\d+',
    f'numberOfRounds = {numberOfRounds}',
    new_content
)

new_content = re.sub(
    r'engine\.setVisible\(\s*\w+\s*\)',
    f'engine.setVisible({str(isVisible).lower()})',  # Převod na malá písmena
    new_content
)

new_content = re.sub(
    r'String seznamProtivniku\s*=\s*".*?";',
    f'String seznamProtivniku = "{opponent_list}";',
    new_content
)

# Zapsat upravený obsah zpět do souboru
with open(path_to_java_server, "w") as server_file:
    server_file.write(new_content)

print("Nastavení serveru bylo úspěšné.")"""



# TODO, předat proměnnou s výběrem do funkce a zjistit si název, upravit ho a vykonat úpravu v suboru!!!
"""robocode.options.view.ground=false
robocode.options.rendering.method=0
robocode.options.rendering.antialiasing=2
robocode.options.sound.enableSound=false
robocode.options.sound.enableMixerPan=true
robocode.options.common.notifyAboutNewBetaVersions=false
robocode.options.common.enableAutoRecording=false
robocode.options.view.robotNames=false
robocode.options.common.enableReplayRecording=false
robocode.options.sound.enableRobotDeath=false
robocode.options.sound.enableRobotCollision=false
robocode.options.rendering.forceBulletColor=false
robocode.options.rendering.noBuffers=1
robocode.options.view.explosions=false
robocode.options.rendering.text.antialiasing=2
robocode.options.rendering.bufferImages=false
robocode.options.view.explosionDebris=false
robocode.options.sound.enableBulletHit=false
robocode.options.view.preventSpeedupWhenMinimized=false
robocode.options.view.robotEnergy=false
robocode.options.common.dontHideRankings=false
robocode.options.sound.enableWallCollision=false
robocode.versionchecked=01/01/9999 10\:10\:10
robocode.options.common.showResults=false
robocode.options.sound.enableMixerVolume=true
robocode.options.sound.mixer=DirectAudioDevice
robocode.options.view.sentryBorder=false
robocode.options.sound.enableGunshot=false
robocode.options.common.appendWhenSavingResults=false
robocode.options.view.scanArcs=false"""
"""robocode_options_view_FPS: bool = True
robocode_options_view_TPS: bool = True
robocode_options_battle_desiredTPS: int = 30

path_to_robocode_properties: str = "RoboCode/config/robocode.properties"
del content, new_content

# Open for read
with open(path_to_robocode_properties, "r") as robocode_properties_file:
    content = robocode_properties_file.read()

new_content = re.sub(
    r'robocode.options.view.FPS=\w+',
    f'robocode.options.view.FPS={str(robocode_options_view_FPS).lower()}',  # Převod na malá písmena
    content
)

new_content = re.sub(
    r'robocode.options.view.TPS=\w+',
    f'robocode.options.view.TPS={str(robocode_options_view_TPS).lower()}',  # Převod na malá písmena
    new_content
)

new_content = re.sub(
    r'robocode.options.battle.desiredTPS=\d+',
    f'robocode.options.battle.desiredTPS={robocode_options_battle_desiredTPS}',  # Převod na malá písmena
    new_content
)

# Zapsat upravený obsah zpět do souboru
with open(path_to_robocode_properties, "w") as robocode_properties_file:
    robocode_properties_file.write(new_content)

print("Nastavení konfigu bylo úspěšné.")

path_to_client: str = "RoboCode/src/sample/PyRobotClient.java"
del content, new_content

# Open for read
with open(path_to_client, "r") as client_file:
    content = client_file.read()"""

# Najděte všechny výskyty řetězce, které chcete nahradit
"""matches = re.findall(r'\{0\.', content)
print(matches)"""

"""new_content = re.sub(
    r'\{\d\., \d\., \d\., \d\.},',
    '{1., 1., 1., 1.},',
    content
)

# Zapsat upravený obsah zpět do souboru
with open(path_to_client, "w") as client_file:
    client_file.write(new_content)

print("Nastavení konfigu bylo úspěšné.")"""

# Adresář, kde se nachází váš Java program
"""java_program_directory = "D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode"

# Nastavíme pracovní adresář na adresář s Java programem
os.chdir(java_program_directory)


# Funkce pro spuštění příkazu a chycení výstupu
def run_command(command):
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        print("Výstup:", output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        print("Chyba při spuštění příkazu:", e.output.decode("utf-8"))


# Spustit příkazy Maven "clean" a "validate"
# run_command(maven_clean_command)
# print("maven clean done")
# run_command(maven_validate_command)
# print("maven validate done")
# run_command(maven_compile_command)
# print("Maven compile done")

# Aktualizovaný příkaz pro spuštění vašeho Java programu
java_command = [
    "C:\\Users\\venca611\\.jdks\\semeru-11.0.20\\bin\\java.exe",
    "-javaagent:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\lib\\idea_rt.jar=55777:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\bin",
    "-Dfile.encoding=UTF-8",
    "-classpath",
    "D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\target\\classes;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\bcel-6.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\codesize-1.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\junit-4.13.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\hamcrest-core-1.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.ui-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\picocontainer-2.14.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.api-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.core-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.host-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.sound-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.battle-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.repository-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\positional-protocol-1.1.0-SNAPSHOT.jar",
    "cz.vutbr.feec.robocode.battle.RobocodeRunner"
]

# "-javaagent:C:\Program Files\JetBrains\IntelliJ IDEA Community Edition 2023.2\lib\idea_rt.jar=61629:C:\Program Files\JetBrains\IntelliJ IDEA Community Edition 2023.2\bin" -Dfile.encoding=UTF-8 -classpath D:\FEKT\Ing\diplomka\RoboCode\RoboCode\target\classes;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\bcel-6.2.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\codesize-1.2.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\junit-4.13.2.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\hamcrest-core-1.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.ui-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\picocontainer-2.14.2.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.api-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.core-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.host-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.sound-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.battle-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\robocode.repository-1.9.4.3.jar;D:\FEKT\Ing\diplomka\RoboCode\RoboCode\libraries\positional-protocol-1.1.0-SNAPSHOT.jar cz.vutbr.feec.robocode.battle.RobocodeRunner


# Spustit příkaz a chytit výstup
try:
    output = subprocess.check_output(java_command, stderr=subprocess.STDOUT)
    print("STDOUT:", output.decode("utf-8"))
except subprocess.CalledProcessError as e:
    print("Chyba při spuštění příkazu:", e.output.decode("utf-8"))"""

"""# Funkce pro spuštění klienta
def start_client():
    client_command = [
        "C:\\Users\\venca611\\.jdks\\semeru-11.0.20\\bin\\java.exe",
        "-javaagent:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\lib\\idea_rt.jar=57247:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\bin",
        "-Dfile.encoding=UTF-8",
        "-classpath",
        "D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\target\\classes;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\bcel-6.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\codesize-1.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\junit-4.13.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\hamcrest-core-1.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.ui-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\picocontainer-2.14.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.api-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.core-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.host-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.sound-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.battle-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.repository-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\positional-protocol-1.1.0-SNAPSHOT.jar",
        "cz.vutbr.feec.robocode.battle.StudentServerRunner"
    ]
    subprocess.run(client_command)


# Funkce pro spuštění serveru s prodlevou
def start_server_with_delay():
    time.sleep(5)  # Prodleva 1 sekundy
    server_command = [
        "C:\\Users\\venca611\\.jdks\\semeru-11.0.20\\bin\\java.exe",
        "-javaagent:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\lib\\idea_rt.jar=57369:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\bin",
        "-Dfile.encoding=UTF-8",
        "-classpath",
        "D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\target\\classes;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\bcel-6.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\codesize-1.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\junit-4.13.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\hamcrest-core-1.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.ui-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\picocontainer-2.14.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.api-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.core-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.host-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.sound-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.battle-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.repository-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\positional-protocol-1.1.0-SNAPSHOT.jar",
        "cz.vutbr.feec.robocode.battle.RobocodeRunner"
    ]
    subprocess.run(server_command)


# Vytvoření vláken pro klienta a server
client_thread = threading.Thread(target=start_client)
server_thread = threading.Thread(target=start_server_with_delay)

# Spuštění vláken
#client_thread.start()
#server_thread.start()

# Připojte se k vláknům (čekáme na jejich dokončení)
#client_thread.join()
#server_thread.join()
start_client()


exit(0)"""

"""# client
command = [
    "C:\\Users\\venca611\\.jdks\\semeru-11.0.20\\bin\\java.exe",
    "-javaagent:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\lib\\idea_rt.jar=60349:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\bin",
    "-Dfile.encoding=UTF-8",
    "-classpath",
    "D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\target\\classes;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\bcel-6.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\codesize-1.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\junit-4.13.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\hamcrest-core-1.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.ui-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\picocontainer-2.14.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.api-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.core-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.host-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.sound-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.battle-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.repository-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\positional-protocol-1.1.0-SNAPSHOT.jar",
    "cz.vutbr.feec.robocode.battle.StudentServerRunner"
]

subprocess.run(command)"""

"""# server
command = [
    "C:\\Users\\venca611\\.jdks\\semeru-11.0.20\\bin\\java.exe",
    "-javaagent:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\lib\\idea_rt.jar=60349:C:\\Program Files\\JetBrains\\IntelliJ IDEA Community Edition 2023.2\\bin",
    "-Dfile.encoding=UTF-8",
    "-classpath",
    "D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\target\\classes;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\bcel-6.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\codesize-1.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\junit-4.13.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\hamcrest-core-1.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.ui-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\picocontainer-2.14.2.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.api-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.core-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.host-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.sound-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.battle-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\robocode.repository-1.9.4.3.jar;D:\\FEKT\\Ing\\diplomka\\RoboCodeProject\\RoboCode\\libraries\\positional-protocol-1.1.0-SNAPSHOT.jar",
    "cz.vutbr.feec.robocode.battle.RobocodeRunner"
]

subprocess.run(command)"""

# exit(0)


# import os


"""path_to_java = "HelloWorld/"

compile_process = subprocess.Popen(["javac", path_to_java + "HelloWorld.java"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
compile_output, compile_errors = compile_process.communicate()

print("compile_output:")
print(compile_output)

if compile_errors:
    print("compile_errors:")
    print(compile_errors)

# get full path
script_directory = os.path.dirname(os.path.abspath(__file__))

run_process = subprocess.Popen(["java", "-cp", script_directory + "\\HelloWorld", "HelloWorld"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
run_output, run_errors = run_process.communicate()

print("\nrun_output:")
print(run_output)

if run_errors:
    print("run_errors:")
    print(run_errors)"""

# path_to_java = "RoboCode/src/cz/vutbr/feec/robocode/battle/"
"""
# Spuštění Maven kompilace s nastavením cesty k nativním knihovnám
maven_dir = "RoboCode"

# Získání cesty ke složce, ve které je aktuální skript
current_dir = os.path.dirname(os.path.abspath(__file__))
print("aktuální složka:", current_dir)

# Cesta k podadresáři s knihovnami
library_dir = os.path.join(current_dir, 'RoboCode\\libraries')
subprocess.run(['C:\\Program Files\\Java\\apache-maven-3.9.4\\bin\\mvn', 'clean', 'install', f'-Djava.library.path={library_dir}'], cwd=maven_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
# Kompilace projektu pomocí Maven
compile_process = subprocess.Popen(["mvn", "compile"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
compile_output, compile_errors = compile_process.communicate()

# Výpis výstupu kompilace
print("Maven compile output:")
print(compile_output)

if compile_errors:
    print("Maven compile errors:")
    print(compile_errors)
"""

"""# Cesta k adresáři, kde se nachází knihovny (JAR soubory)
libs_path = "D:/FEKT/Ing/diplomka/RoboCode/RoboCode/libraries"

compile_process = subprocess.Popen(["javac", "-cp", libs_path, path_to_java + "RobocodeRunner.java"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
compile_output, compile_errors = compile_process.communicate()

print("compile_output:")
print(compile_output)

if compile_errors:
    print("compile_errors:")
    print(compile_errors)


exit(0)










import os
import subprocess
import time

# Získání cesty ke složce, ve které je aktuální skript
current_dir = os.path.dirname(os.path.abspath(__file__))
print("aktuální složka:", current_dir)

# Cesta k podadresáři s knihovnami
library_dir = os.path.join(current_dir, 'RoboCode\\libraries')
print("cesta ke knihovnám:", library_dir)

# Spuštění Maven kompilace s nastavením cesty k nativním knihovnám
maven_dir = "RoboCode" """
# subprocess.run(['C:\\Program Files\\Java\\apache-maven-3.9.4\\bin\\mvn', 'clean', 'install', f'-Djava.library.path={library_dir}'], cwd=maven_dir, shell=True)

# Vyčištění a kompilace pomocí Mavenu
# subprocess.run(['C:\\Program Files\\Java\\apache-maven-3.9.4\\bin\\mvn', 'clean'], cwd=maven_dir, shell=True)
# subprocess.run(['C:\\Program Files\\Java\\apache-maven-3.9.4\\bin\\mvn', 'validate'], cwd=maven_dir, shell=True)
# subprocess.run(['C:\\Program Files\\Java\\apache-maven-3.9.4\\bin\\mvn', 'compile'], cwd=maven_dir, shell=True)

# Sestavení cest ke zdrojovým souborům Java programů relativně k aktuálnímu adresáři
"""program_path = 'RoboCode\\src\\cz\\vutbr\\feec\\robocode\\battle'
java_program1_path = os.path.join(current_dir, program_path + '\\StudentServerRunner.java')
java_program2_path = os.path.join(current_dir, program_path + '\\RobocodeRunner.java')

print(java_program1_path)
print(java_program2_path)

# Kompilace prvního Java programu
s1 = subprocess.Popen("javac A.java", shell=True)
s2 = subprocess.Popen("java A", shell=True)
print(s1, s2)"""

"""compile_result_1 = subprocess.run(['javac', '-cp', library_dir, 'StudentServerRunner.java'], cwd=java_program1_path, shell=True)
#compile_result_1 = subprocess.run(['javac', '-cp', f'{library_dir}/*', java_program1_path], cwd=current_dir, shell=True)
print(compile_result_1)
if compile_result_1.returncode != 0:
    print("Chyba při kompilaci prvního Java programu.")
    exit(1)
"""
# Kompilace druhého Java programu
"""compile_result_2 = subprocess.run(['javac', '-cp', library_dir2, java_program2_path], cwd=current_dir, shell=True)
print(compile_result_2)
if compile_result_2.returncode != 0:
    print("Chyba při kompilaci druhého Java programu.")
    exit(1)"""

# time.sleep(0.5)

"""# Spuštění prvního Java programu
output_file1 = os.path.join(current_dir, 'output1.txt')
with open(output_file1, 'w') as stdout_file, open(output_file1, 'w') as stderr_file:
    subprocess.run(['java', '-cp', current_dir, 'cz.vutbr.feec.robocode.battle.StudentServerRunner'], stdout=stdout_file, stderr=stderr_file)

# Spuštění druhého Java programu
output_file2 = os.path.join(current_dir, 'output2.txt')
with open(output_file2, 'w') as stdout_file, open(output_file2, 'w') as stderr_file:
    subprocess.run(['java', '-cp', current_dir, 'cz.vutbr.feec.robocode.battle.RobocodeRunner'], stdout=stdout_file, stderr=stderr_file)
"""
# time.sleep(5)

# print("Java programy byly zkompilovány, spuštěny a výstupy uloženy do souborů.")



if __name__ == '__main__':
    pass
    # uvítání
    # vykonani game.properties
    # vykonání robocode.properties
    # TODO, pokud příkaz chybí, tak jej doplnit na začátek nebo (na konec)?
    # nastavení epizod, možnost interakce or not
    # zapnuti robocode a počkání na konec
    # načtení dat, načtení neuronky a zpěně gradient a uložení neuronky
    # konec epizod
    # uložení dat pro grafy
