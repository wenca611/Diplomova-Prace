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
    import platform  # Access to underlying platform’s identifying data
    import os  # Miscellaneous operating system interfaces
    from typing import Optional  # Support for type hints
    import types
    import threading
    #import functools  # Higher-order functions and operations on callable objects
    #import itertools  # Functions creating iterators for efficient looping
    import signal  # Set handlers for asynchronous events
    import re  # Regular expression operations
    import time as tim  # Time access and conversions
    #import concurrent.futures  # Launching parallel tasks
except ImportError as L_err:
    print("Chyba v načtení standardní knihovny: {0}".format(L_err))
    exit(1)
except Exception as e:
    print(f"Jiná chyba v načtení standardní knihovny: {e}")
    exit(1)

# Third-party libraries:
try:
    pass
    # Data manipulation and analysis
    #import numpy as np  # Fundamental package for scientific computing
    #from scipy.stats import skew, kurtosis, hmean, gmean, linregress  # Library for statistics and regression analysis
    #from scipy.fftpack import dct  # Library for discrete cosine transform

    # Visualization
    # from tqdm import tqdm  # displaying progress bars
    #import matplotlib.pyplot as plt  # Library for creating static, animated, and interactive visualizations
    #import matplotlib as mpl  # Library for customization of matplotlib plots
    #import matplotlib.colors as mcolors  # Library for color mapping and normalization
except ImportError as L_err:
    print("Chyba v načtení knihovny třetích stran: {0}".format(L_err))
    exit(1)
except Exception as e:
    print(f"Jiná chyba v načtení knihovny třetích stran: {e}")
    exit(1)


def load_tensorflow() -> types.ModuleType:
    try:
        import tensorflow as tf
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        return tf
    except ImportError as load_err:
        print("Chyba v načtení knihovny třetích stran: {0}".format(load_err))
        exit(1)
    except Exception as exc:
        print(f"Jiná chyba v načtení knihovny třetích stran: {exc}")
        exit(1)


# DEBUG option
DEBUG_PRINT = False


class Utils:
    """
    A utility class providing various helper functions.
    """

    @staticmethod
    def welcome() -> None:
        """
        Prints Welcome text

        :return: None
        """
        print("""============Optimalizace řízení s pomocí zpětnovazebního učení na platformě Robocode================
-autor: Bc. Václav Pastušek
-škola: VUT FEKT
-minimální požadovaná verze Pythonu: 3.10
-aktuální verze Pythonu: {}
-VUT číslo: 204437\n""".format(platform.python_version()))

    @staticmethod
    def pyhelp() -> None:
        """
        Prints Help text

        :return: None
        """
        print("""\nNápověda:
pro výpis nápovědy použijte: 'h', 'n' nebo 't'
pro výběr epizod použijte: '1', '10', '1e6',... [e>0]
a pro ukončení programu použijte: 'k', 'e', 'x' nebo '.'\n""")

    @staticmethod
    def handle_keyboard_interrupt(frame: Optional[object] = None, signal_interrupt: Optional[object] = None) -> None:
        """
        A function for handling keyboard interrupt signal.

        :param frame: Not used.
        :param signal_interrupt: Not used.
        :return: None
        """
        _, _ = frame, signal_interrupt  # to reduce warnings
        print("\nUkončeno stiskem klávesy Ctrl+C nebo tlačítkem Stop")
        exit()


class GameSettingsModifier:
    # parameters for game.properties
    path_to_game_properties: str = "RoboCode/config/game.properties"
    gameWidth: int = 800  # game width: 800  <400; 5000>
    gameHeight: int = 600  # game height: 600 <400; 5000>
    numberOfRounds: int = 100  # number of rounds: 10 <1; max_int(2_147_483_647)>
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

    listOfEnemies: str = "Crazy, 13, Walls, 17"  # opponents list: Crazy, 13, Walls, 17
    # listOfEnemies: str = "1, "*999 + "1"  # 1000 tanks ≈ 3 FPS and 3 TPS

    # parameters for robocode.properties
    path_to_robocode_properties: str = "RoboCode/config/robocode.properties"
    view_ground = True  # True
    rendering_method = 2  # 2; 0-2 Default, Quality, Speed
    view_FPS = True  # True
    rendering_antialiasing = 0  # 2; 0-2 Default, On, Off
    sound_enableSound = True  # True
    view_robotNames = True  # True
    battle_desiredTPS = 50  # 50; TPS<0 => max TPS; TPS=0 => error!
    sound_enableRobotDeath = True  # True
    view_TPS = True  # True
    sound_enableRobotCollision = True  # True
    rendering_forceBulletColor = True  # True
    rendering_noBuffers = 3  # 0; 0-3 [max ~40] Without buffer, Single, Double, Triple
    view_explosions = True  # True
    rendering_text_antialiasing = 0  # 2; 0-2 Default, On, Off
    rendering_bufferImages = True  # True
    view_explosionDebris = True  # True
    sound_enableBulletHit = True  # True
    view_preventSpeedupWhenMinimized = False  # False
    view_robotEnergy = True  # True
    common_dontHideRankings = True  # True
    sound_enableWallCollision = True  # True
    common_showResults = True  # True
    sound_enableMixerVolume = True  # True
    view_sentryBorder = False  # False
    sound_enableGunshot = True  # True
    common_appendWhenSavingResults = True  # True
    view_scanArcs = False  # False

    # parameters for game.properties
    path_to_window_properties: str = "RoboCode/config/window.properties"
    RobocodeFrame: str = "0,0,1200,800"  # RoboCode frame: 0, 0, 1200, 800

    def __init__(self) -> None:
        # Rozdělit seznam protivníků podle čárky a odstranit případné mezery
        opponents: list[str] = [opponent.strip() for opponent in self.listOfEnemies.split(",")]

        # Převést čísla na jména protivníků
        opponents_with_names: list[str] = [self.enemies[int(opponent)] if opponent.isdigit() else opponent for opponent
                                           in opponents]
        # update seznamu protivníků
        self.listOfEnemies: str = ", ".join(opponents_with_names)

        print("Seznam protivníků:", self.listOfEnemies) if DEBUG_PRINT else None

    @staticmethod
    def read_file(filename):
        try:
            with open(filename, 'r') as file:
                content = file.read()
            return content
        except FileNotFoundError:
            print(f"Soubor {filename.removeprefix('RoboCode/config/')} nebyl nalezen.")
            exit(1)
        except Exception as exc:
            print(f"Chyba při čtení souboru: {exc}")
            exit(1)

    @staticmethod
    def write_file(filename, content):
        try:
            with open(filename, 'w') as file:
                file.write(content)
            print(f"Soubor {filename.removeprefix('RoboCode/config/')} byl úspěšně uložen.")
        except Exception as exc:
            print(f"Chyba při zápisu souboru: {exc}")
            exit(1)

    @staticmethod
    def update_content(var, var_type, content):
        var_text, var_value = var
        # odstran prefix
        var_text: str = var_text.removeprefix("self.")
        regex_part: str = ""
        match var_type:
            case "int":
                regex_part = rf"-?\d+"
            case "bool":
                regex_part = rf"\w+"
                var_value = var_value.lower()
            case "str":
                regex_part = rf".*"
                var_value = var_value[1:-1] if len(var_value) > 0 else var_value
            case "robocode_bool" | "robocode_int":
                var_text = "robocode.options." + var_text.replace("_", ".")
                match var_type:
                    case "robocode_bool":
                        regex_part = rf"\w+"
                        var_value = var_value.lower()
                    case "robocode_int":
                        regex_part = rf"-?\d+"
            case "frame":
                var_text = "net.sf.robocode.ui.dialog." + var_text
                var_value = var_value[1:-1] if len(var_value) > 0 else var_value
                regex_part = rf".*"
            case _:
                print("Špatný typ u proměnné")
                exit(1)

        # Hledání shody
        match = re.search(rf"{var_text}\s*=\s*" + regex_part, content)

        # Pokud regex nenalezne shodu, přidej text na začátek obsahu
        if match is None:
            content = f"{var_text} = {var_value}\n" + content
        else:
            # Pokud byla nalezena shoda, uprav ji
            content = re.sub(rf"{var_text}\s*=\s*" + regex_part, f"{var_text} = {var_value}", content)

        return content

    def set_game_properties(self):
        content = self.read_file(self.path_to_game_properties)
        print("Game properties[:300]:", content[:300]) if DEBUG_PRINT else None

        content = self.update_content(f'{self.numberOfRounds=}'.split('='), 'int', content)
        content = self.update_content(f'{self.gameWidth=}'.split('='), 'int', content)
        content = self.update_content(f'{self.gameHeight=}'.split('='), 'int', content)
        content = self.update_content(f'{self.numberOfRounds=}'.split('='), 'int', content)
        content = self.update_content(f'{self.isVisible=}'.split('='), 'bool', content)
        content = self.update_content(f'{self.listOfEnemies=}'.split('='), 'str', content)

        print("Game new properties[:300]:", content[:300]) if DEBUG_PRINT else None
        self.write_file(self.path_to_game_properties, content)

    def set_robocode_properties(self):
        content = self.read_file(self.path_to_robocode_properties)
        print("Robocode properties[:500]:", content[:500]) if DEBUG_PRINT else None

        content = self.update_content(f'{self.view_ground=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.rendering_method=}'.split('='), 'robocode_int', content)
        content = self.update_content(f'{self.view_FPS=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.rendering_antialiasing=}'.split('='), 'robocode_int', content)
        content = self.update_content(f'{self.sound_enableSound=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_robotNames=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.battle_desiredTPS=}'.split('='), 'robocode_int', content)
        content = self.update_content(f'{self.sound_enableRobotDeath=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_TPS=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.sound_enableRobotCollision=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.rendering_forceBulletColor=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.rendering_noBuffers=}'.split('='), 'robocode_int', content)
        content = self.update_content(f'{self.view_explosions=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.rendering_text_antialiasing=}'.split('='), 'robocode_int', content)
        content = self.update_content(f'{self.rendering_bufferImages=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_explosionDebris=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.sound_enableBulletHit=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_preventSpeedupWhenMinimized=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_robotEnergy=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.common_dontHideRankings=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.sound_enableWallCollision=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.common_showResults=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.sound_enableMixerVolume=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_sentryBorder=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.sound_enableGunshot=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.common_appendWhenSavingResults=}'.split('='), 'robocode_bool', content)
        content = self.update_content(f'{self.view_scanArcs=}'.split('='), 'robocode_bool', content)

        print("Robocode new properties[:500]:", content[:500]) if DEBUG_PRINT else None
        self.write_file(self.path_to_robocode_properties, content)

    def set_window_properties(self):
        content = self.read_file(self.path_to_window_properties)
        print("Window properties[:300]:", content[:300]) if DEBUG_PRINT else None

        content = self.update_content(f'{self.RobocodeFrame=}'.split('='), 'frame', content)

        print("Window new properties[:300]:", content[:300]) if DEBUG_PRINT else None
        self.write_file(self.path_to_window_properties, content)


class UserInterface:
    """
    The UserInterface class represents a collection of static methods used for handling user input and
    parsing it into the desired format.
    """

    @staticmethod
    def input_loop(text: str):
        """
        Loops until valid user input is entered.

        :param text: message to display to the user
        :return: valid user input
        """
        help_list = ["h", "help", "t", "tut", "tutorial", "n", "napoveda"]
        end_list = ["k", "konec", "e", "end", "x", "."]
        while True:
            user_input: str = input(text + " (1/10/2.3e6/help/end): ")
            low_user_input: str = user_input.lower()

            try:
                num = float(low_user_input)
                if num > 0. and num.is_integer():
                    return int(num)
                else:
                    print("Zadejte celé číslo větší než 0.")
            except ValueError:
                if low_user_input in help_list:
                    # Display help message
                    Utils.pyhelp()
                elif low_user_input in end_list:
                    # Exit program if user input is in end list
                    exit()
                else:
                    print("Zadali jste nesprávný vstup.")


"""
layer_sizes: list[int] = [1024, 4]  # [1024, 2**11, 2**11, 4]

def create_model():
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

"""

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
    # Vlákno pro načítání TensorFlow.
    tensorflow_thread = threading.Thread(target=load_tensorflow)
    tensorflow_thread.start()

    # Sets up a keyboard interrupt signal handler.
    signal.signal(signal.SIGINT, Utils.handle_keyboard_interrupt)

    # Prints out a welcome message.
    Utils.welcome()

    # nastavení konfigurace hry, platformy a obrazovky
    game_settings = GameSettingsModifier()
    print("Nastavení předdefinovaných vlastností:")
    game_settings.set_game_properties()
    game_settings.set_robocode_properties()
    game_settings.set_window_properties()
    print("Nastavení dokončeno")

    episode: int = UserInterface.input_loop("Zadejte počet epizod")
    print("Počet epizod je:", episode) if DEBUG_PRINT or 1 else None

    # Vyčkání na dokončení vlákna
    tensorflow_thread.join()
    print("Načten Tensorflow") if DEBUG_PRINT else None

    # nastavení epizod, možnost interakce or not
    # zapnuti robocode a počkání na konec
    # načtení dat, načtení neuronky a zpěně gradient a uložení neuronky
    # konec epizod
    # uložení dat pro grafy
