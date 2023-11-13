# -*- coding: utf-8 -*-
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
import time

# Standard libraries:
try:
    import platform  # Access to underlying platform’s identifying data
    import os  # Miscellaneous operating system interfaces
    from typing import Optional  # Support for type hints
    import types
    import threading
    import subprocess
    #import functools  # Higher-order functions and operations on callable objects
    #import itertools  # Functions creating iterators for efficient looping
    import signal  # Set handlers for asynchronous events
    import re  # Regular expression operations
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
    pass
    # Data manipulation and analysis
    import numpy as np  # Fundamental package for scientific computing
    from tensorflow.keras.callbacks import Callback
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


def load_tensorflow() -> None:
    global tf  # Použijte globální proměnnou "tf"
    try:
        import tensorflow as tf
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    except ImportError as load_err:
        print("Chyba v načtení knihovny třetích stran: {0}".format(load_err))
        exit(1)
    except Exception as exc:
        print(f"Jiná chyba v načtení knihovny třetích stran: {exc}")
        exit(1)


# DEBUG option
DEBUG_PRINT = False

# Globální proměnná pro uchování knihovny TensorFlow
tf = None


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
    """
    TODO
    """
    # parameters for game.properties
    path_to_game_properties: str = "RoboCode/config/game.properties"
    gameWidth: int = 800  # game width: 800  <400; 5000>
    gameHeight: int = 600  # game height: 600  <400; 5000>
    numberOfRounds: int = 1  # number of rounds: 10  <1; max_int(2_147_483_647)>
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

    # listOfEnemies: str = "1, Crazy, 13, Walls, 17"  # opponents list: Crazy, 13, Walls, 17
    #listOfEnemies: str = "2, "*9 + "17"  # 1000 tanks ≈ 3 FPS and 3 TPS
    # listOfEnemies: str = ", ".join([str(i+1) for i in range(len(enemies)-1)])
    listOfEnemies: str = "1, 17, 3, 12, 11, 2"

    # parameters for robocode.properties
    path_to_robocode_properties: str = "RoboCode/config/robocode.properties"
    view_ground = True  # True
    rendering_method = 1  # 2; 0-2 Default, Quality, Speed
    view_FPS = False  # True
    rendering_antialiasing = 1  # 2; 0-2 Default, On, Off
    sound_enableSound = False  # True
    view_robotNames = True  # True
    battle_desiredTPS = 50  # 50; TPS<0 => max TPS; TPS=0 => error!
    sound_enableRobotDeath = False  # True
    view_TPS = True  # True
    sound_enableRobotCollision = False  # True
    rendering_forceBulletColor = True  # True
    rendering_noBuffers = 3  # 0; 0-3 [max ~40] Without buffer, Single, Double, Triple
    view_explosions = True  # True
    rendering_text_antialiasing = 2 # 2; 0-2 Default, On, Off
    rendering_bufferImages = True  # True
    view_explosionDebris = True  # True
    sound_enableBulletHit = False  # True
    view_preventSpeedupWhenMinimized = False  # False
    view_robotEnergy = True  # True
    common_dontHideRankings = True  # True
    sound_enableWallCollision = False  # True
    common_showResults = True  # True
    sound_enableMixerVolume = False  # True
    view_sentryBorder = False  # False
    sound_enableGunshot = False  # True
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
            user_input: str = input(text + " (1, 100, 2.3e6, help, end): ")
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


class RobocodeRunner:
    """
    TODO
    """
    command: list[str] = [
        r'C:\Users\venca611\.jdks\semeru-11.0.20-1\bin\java.exe',
        r'-javaagent:C:\Program Files\JetBrains\IntelliJ IDEA Community Edition 2023.2\lib\idea_rt.jar=52793:'
        r'C:\Program Files\JetBrains\IntelliJ IDEA Community Edition 2023.2\bin',
        '-Dfile.encoding=UTF-8',
        '-classpath',
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\target\classes;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.api\1.9.4.3\robocode.api-1.9.4.3.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.core\1.9.4.3\robocode.core-1.9.4.3.jar;'
        r'C:\Users\venca611\.m2\repository\org\picocontainer\picocontainer\2.14.2\picocontainer-2.14.2.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.battle\1.9.4.3\robocode.battle-1.9.4.3.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.host\1.9.4.3\robocode.host-1.9.4.3.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.repository\1.9.4.3\robocode.repository-1.9.4.3.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\codesize\1.2\codesize-1.2.jar;'
        r'C:\Users\venca611\.m2\repository\org\apache\bcel\bcel\6.2\bcel-6.2.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.ui\1.9.4.3\robocode.ui-1.9.4.3.jar;'
        r'C:\Users\venca611\.m2\repository\net\sf\robocode\robocode.sound\1.9.4.3\robocode.sound-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\bcel-6.2.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\codesize-1.2.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\junit-4.13.2.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\hamcrest-core-1.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.ui-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\picocontainer-2.14.2.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.api-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.core-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.host-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.sound-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.battle-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\robocode.repository-1.9.4.3.jar;'
        r'D:\FEKT\Ing\diplomka\RoboCodeProject\RoboCode\libraries\positional-protocol-1.1.0-SNAPSHOT.jar',
        'cz.vutbr.feec.robocode.battle.RobocodeRunner'
    ]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    java_program_directory = current_dir + r"\RoboCode"

    def __init__(self):
        # Nastavíme pracovní adresář na adresář s Java programem
        os.chdir(self.java_program_directory)

        # Spusťte příkaz a uložte výstup a chybový výstup
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)

        # Získání výstupu a chybového výstupu
        stdout, stderr = process.communicate()

        # Výstup a chybový výstup jsou nyní uloženy v proměnných 'stdout' a 'stderr'.
        print("stdout:\n", stdout, "\nstderr:\n", stderr) if DEBUG_PRINT else None

        err_lines = stderr.split('\n')
        for err_line in err_lines:
            if not err_line.strip():
                # Prázdné řádky přeskočíme
                continue
            if not err_line.startswith('WARNING: '):
                print("Chyba v textu:")
                print(err_line)
                exit(1)

        # Pokud projde celý text, znamená to, že všechny řádky začínají s "WARNING: "
        print("V stderr vše v pořádku, pokračujeme.")

        # Najdeme text mezi "-- Battle results --" a koncem textu
        match = re.search(r'-- Battle results --\s+(.*)', stdout, re.DOTALL)

        if match:
            results_text = match.group(1)

            # Pomocí regulárního výrazu získáme názvy tanků a jejich skóre
            tank_results = re.findall(r'(\S+):\s+(\d+)', results_text)

            if tank_results:
                for tank, score in tank_results:
                    print(f"{tank.removeprefix('sample.')}: {score}")
            else:
                print("Nenalezena žádná data o výsledcích tanků.")
        else:
            print("Nenalezena část textu s výsledky.")

        os.chdir(self.current_dir)

class NaNCallback(Callback):
    def on_epoch_end(self, epoch, logs=None):
        values = np.array(list(logs.values()))
        if np.isnan(values).any():
            self.model.stop_training = True
            print("Training stopped due to NaN values.")


# Předpokládejme, že můžeme použít funkci predict pro predikci Q-hodnot
def predict_q_values(model, state):
    return model.predict(np.array([state]))


# Funkce pro výpočet target_q_values
def calculate_target_q_values(model, gamma, states):
    states_for_learning = stavy[:-1]
    target_q_values = np.zeros_like(states_for_learning, dtype=float)

    for i in range(len(states_for_learning)):
        next_state = states[i+1]
        max_q_value_next = np.max(predict_q_values(model, next_state))
        reward = 0.1  # TODO
        target_q_values[i] = reward + gamma * max_q_value_next

    return target_q_values

if __name__ == '__main__':
    # Vlákno pro načítání TensorFlow.
    tensorflow_thread = threading.Thread(target=load_tensorflow)
    tensorflow_thread.start()

    # Sets up a keyboard interrupt signal handler.
    signal.signal(signal.SIGINT, Utils.handle_keyboard_interrupt)

    # Prints out a welcome message.
    Utils.welcome()

    # nastavení konfigurace hry, platformy a obrazovky
    GameSettingsModifier.isVisible = True

    game_settings = GameSettingsModifier()
    print("Nastavení předdefinovaných vlastností:")
    game_settings.set_game_properties()
    game_settings.set_robocode_properties()
    game_settings.set_window_properties()
    print("Nastavení dokončeno")

    num_episode: int = UserInterface.input_loop("\nZadejte počet epizod")
    print("Počet epizod je:", num_episode) if DEBUG_PRINT or 1 else None

    # Vyčkání na dokončení vlákna
    tensorflow_thread.join()
    print("Načten Tensorflow") if DEBUG_PRINT else None

    if tf is None:
        print("Knihovna TensorFlow není načtena. Program bude ukončen.")
        exit(1)  # Importujte modul sys na začátku kódu

    # TODO do funkce
    import tf2onnx
    import onnx

    # Cesta k složce s modely
    models_folder = 'RoboCode/NeuralNetworkModels/'

    # Kontrola, zda existuje složka NeuralNetworkModels
    if not os.path.exists(models_folder):
        # Vytvoření složky, pokud neexistuje
        os.makedirs(models_folder)
        print(f"Složka '{models_folder}' byla vytvořena.")


    # Vytvoření nebo načtení TensorFlow modelu
    if os.path.exists(models_folder + 'my_model.keras'):
        # Načtení existujícího modelu
        # noinspection PyUnresolvedReferences
        model_tf = tf.keras.models.load_model(models_folder + 'my_model.keras')
        print("Existující TensorFlow model byl načten.")
    else:
        # Vytvoření a trénink nového modelu 160, 1024, 1024, 1024, 1024, 4
        # noinspection PyUnresolvedReferences
        model_tf = tf.keras.Sequential([
            tf.keras.layers.Dense(int(2 ** 10), activation='relu', input_shape=(160,),
                                  kernel_initializer='random_normal'),
            tf.keras.layers.Dense(int(2 ** 10), activation='relu', kernel_initializer='random_normal'),
            tf.keras.layers.Dense(int(2 ** 10), activation='relu', kernel_initializer='random_normal'),
            tf.keras.layers.Dense(int(2 ** 10), activation='relu', kernel_initializer='random_normal'),
            tf.keras.layers.Dense(4, activation='linear', kernel_initializer='random_normal')
        ])

        # Uložení modelu ve formátu Keras
        model_tf.save(models_folder + 'my_model.keras')
        print(f"Nový TensorFlow model byl vytvořen a uložen v '{models_folder}my_model.keras'.")

    # Kompilace modelu (definujte optimizér, ztrátovou funkci a metriky)
    model_tf.compile(optimizer='adam', loss='mean_squared_error')

    # Převod modelu do formátu ONNX
    onnx_model_path = models_folder + 'my_model.onnx'
    #input_signature = [tf.TensorSpec([None, 160], tf.float32, name='x')]
    # noinspection PyUnresolvedReferences
    input_signature = [tf.TensorSpec([1, 160], tf.float32, name='input_name')]
    onnx_model, _ = tf2onnx.convert.from_keras(model_tf, input_signature)
    onnx.save_model(onnx_model, onnx_model_path)
    print(f"Model byl převeden do formátu ONNX a uložen v '{onnx_model_path}'.")

    start_time = time.time()
    for episode in range(num_episode):
        start_ep_time = time.time()
        print("TODO return")
        RobocodeRunner()

        lines = []

        # load game_data -> input stavy, target akce a sample_weight=rewards ceny
        try:
            with open("RoboCode/ModelGameData.txt", "r") as file:
                # Načtení obsahu souboru do pole řádků
                lines = file.readlines()

                # Kontrola, zda soubor není prázdný
                if not lines:
                    raise ValueError("Soubor je prázdný.")

                # Zde můžete dále pracovat s obsahem souboru, například vypsání obsahu
                """print("Obsah souboru:")
                for line in lines:
                    print(line.strip())  # Strip odstraní bílé znaky na začátku a konci každého řádku"""

        except FileNotFoundError:
            print("Soubor 'ModelGameData.txt' neexistuje.")
            exit(1)
        except ValueError as ve:
            print(f"Chyba: {ve}")
            exit(1)
        except Exception as e:
            print(f"Neočekávaná chyba: {e}")
            exit(1)

        # Inicializace seznamů pro stavy a akce
        stavy = []
        akce = []

        # Procházení každého stringu v poli
        for line in lines:
            # Rozdělení stringu podle znaku '|'
            parts = line.strip().split('|')

            # Kontrola, zda byly nalezeny obě části (stav a akce)
            if len(parts) == 2:
                # Rozdělení a převod první části na float čísla
                stavy_float = [float(x) for x in parts[0].split()]

                # Rozdělení a převod druhé části na float čísla
                akce_float = [float(x) for x in parts[1].split()]

                # Přidání do seznamu stavy
                stavy.append(stavy_float)

                # Přidání do seznamu akce
                akce.append(akce_float)
            else:
                print(f"Chyba při rozdělování: {line}")

        # Výpis seznamů se stavy a akcemi
        #print("Seznam stavů:", stavy)
        #print("Seznam akcí:", akce)


        # lines -> stavy a akce
        # hodit to do Belmanna s reward fcí
        gamma = 0.9

        # Výpočet cílových hodnot
        #target_values = calculate_target_q_values(model_tf, gamma, stavy)

        # Odstranění posledního stavu pro učení
        states_for_learning = np.array(stavy[:-1])

        #print("Rozměry target_values:", target_values.shape)
        #print("Rozměry states_for_learning:", states_for_learning.shape)
        #print(len(stavy))
        stavy = np.array(stavy, dtype=np.float32)
        akce = np.array(akce, dtype=np.float32)
        # Vytvořte pole rewards
        rewards = np.arange(0, len(stavy) * 0.001, 0.001, dtype=np.float32)
        rewards = rewards[:len(stavy)]

        for i, stav in enumerate(stavy):
            #print(stav[:8])
            match int(stav[7]):
                case 0:
                    rewards[i] += 0.1
                case 1:
                    rewards[i] -= 0.1
                case 2:
                    rewards[i] -= 0.02
                case 3:
                    rewards[i] -= 10
                case _:
                    print("nedefinovaný stav v tanku")
                    exit(1)
            rewards[i] = (stav[0]-100)/10.

        #print("velikosti:", stavy.shape, akce.shape, rewards.shape)
        #print(rewards)

        # noinspection PyUnresolvedReferences
        stavy = tf.convert_to_tensor(stavy, dtype=tf.float32)
        # noinspection PyUnresolvedReferences
        akce = tf.convert_to_tensor(akce, dtype=tf.float32)
        # noinspection PyUnresolvedReferences
        rewards = tf.convert_to_tensor(rewards, dtype=tf.float32)

        model_tf.fit(stavy, akce, epochs=1, batch_size=1, sample_weight=rewards, verbose=0, callbacks=[NaNCallback()])

        # Uložení TF a ONNX modelu do souboru
        model_tf.save(models_folder + 'my_model.keras')
        #print("uložení TF modelu")
        onnx_model, _ = tf2onnx.convert.from_keras(model_tf, input_signature)
        onnx.save_model(onnx_model, onnx_model_path)

        #print(f"Model byl převeden do formátu ONNX a uložen v '{onnx_model_path}'.")
        print("Epizoda", episode + 1, "dokončena")
        print("Čas na epizodu: {:.2f}\n".format(time.time() - start_ep_time))
    print("Celkový čas za všechny epizody:", time.time() - start_time)







    # TODO
    # načtení dat, načtení neuronky a zpěně gradient a uložení neuronky
    # konec epizod
    # uložení dat pro grafy, jako ceny
    # taky projet třeba dvojice botů a ukázat do tabulky výstup
    """
    +--------+-----------------+--------------+--------------+-------------+------------+------------------+------------------+
    | Číslo | Jméno bota | Celkové skóre | Nejlepší skóre | Nejhorší skóre | Rozdíl skóre | Nejlepší proti | Nejhorší proti |
    | | | | | | | (Číslo bota) | (Číslo bota) |
    +--------+-----------------+--------------+--------------+-------------+------------+------------------+------------------+
    | 1 | Bot A | 350 | 400 | 200 | 200 | 3 | 2 |
    | 2 | Bot B | 420 | 500 | 250 | 250 | 4 | 1 |
    | 3 | Bot C | 290 | 350 | 180 | 170 | 4 | 1 |
    | 4 | Bot D | 550 | 600 | 300 | 300 | 2 | 3 |
    +--------+-----------------+--------------+--------------+-------------+------------+------------------+------------------+
    """
    # sledování cen u agenta, během epizod, ...
    # neuronky s časovou značkou
    # tabulka přezdívek neuronek + neuronka čas. name + čas trénování + počet epizod + velikost a typy neuronů
