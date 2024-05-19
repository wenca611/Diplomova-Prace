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

# Standard libraries:
try:
    import platform  # Access to underlying platform’s identifying data
    import os  # Miscellaneous operating system interfaces
    from typing import Optional, Tuple, Match  # Support for type hints
    import types  # Dynamic creation of new types
    import threading  # Thread-based parallelism
    import subprocess  # Spawn new processes, connect to their input/output/error pipes, and obtain their return codes
    import copy  # Shallow and deep copy operations
    from datetime import datetime  # Basic date and time types
    import signal  # Set handlers for asynchronous events
    import re  # Regular expression operations
    import csv  # CSV file reading and writing
    import time  # Time access and conversions
    import ast  # Abstract Syntax Trees
    import random as rnd  # Generate pseudo-random numbers
    import sys  # System-specific parameters and functions
    import warnings  # Warning control
    import importlib  # Reload modules dynamically
    import gc  # Garbage collector for memory management
    import winsound  # For sound notifications

    os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'  # Set the minimum Tensorflow log level to '2'
    warnings.simplefilter(action='ignore', category=FutureWarning)  # Ignore FutureWarnings
except ImportError as L_err:
    print("Chyba v načtení standardní knihovny: {0}".format(L_err))
    exit(1)
except Exception as e:
    print(f"Jiná chyba v načtení standardní knihovny: {e}")
    exit(1)

# Set the current working directory
current_working_directory = os.path.abspath(os.path.dirname(__file__))
# Append the path to the virtual environment site-packages directory to sys.path
sys.path.append(os.path.abspath(os.path.join(current_working_directory, 'venv', 'Lib', 'site-packages')))

# Third-party libraries:
try:
    from tqdm import tqdm

    # Dictionary containing libraries to load and their shortcuts
    libraries_to_load: dict = {'numpy': 'np', 'pandas': 'pd', 'tensorflow': 'tf'}

    # Displaying a progress bar with library names as descriptions
    for library, shortcut in tqdm(libraries_to_load.items(),
                                  desc="Načítání knihoven: {0}".format(', '.join(list(libraries_to_load.keys()))),
                                  unit="lib"):
        # Importing the library
        __import__(library)

    import numpy as np  # Fundamental package for scientific computing
    import tensorflow as tf  # Neural network library
    from tensorflow.keras.callbacks import Callback  # Base class for Keras callbacks
    from tensorflow.keras import layers  # Keras layers module
    import pandas as pd  # Data manipulation and analysis library
    from pandasgui import show  # GUI tool for exploring pandas DataFrames
    import matplotlib.pyplot as plt  # Plotting library
    from matplotlib.widgets import Slider  # Widgets for matplotlib plots
    from matplotlib.backends.backend_pdf import PdfPages  # PDF backend for matplotlib

    # Disable eager execution mode
    tf.compat.v1.disable_eager_execution()
    # Get list of physical devices
    physical_devices = tf.config.list_physical_devices('GPU')

    # If physical devices are available
    if physical_devices:
        # Set memory growth for each physical device
        for device in physical_devices:
            tf.config.experimental.set_memory_growth(device, True)

        # Set visible devices
        tf.config.set_visible_devices(physical_devices[0], 'GPU')

        print("Počet volných GPU: ", len(tf.config.list_physical_devices('GPU')))
except ImportError as L_err:
    print("Chyba v načtení knihovny třetích stran: {0}".format(L_err))
    exit(1)
except Exception as e:
    print(f"Jiná chyba v načtení knihovny třetích stran: {e}")
    exit(1)

# Debug option
DEBUG_PRINT: bool = False
# Notification sound for training and testing
NOTIFICATION_SOUND: bool = True


class Utils:
    """
    A utility class providing various helper functions.
    """

    def __init__(self):
        """
        Initializes the Utils class with lists for help and termination options.
        """
        self.help_list = ["h", "help", "tut", "tutorial", "napoveda"]
        self.end_list = ["k", "konec", "e", "end", "x", "."]

    @staticmethod
    def welcome() -> None:
        """
        Prints Welcome text.

        :return: None
        """
        print("""============Optimalizace řízení s pomocí zpětnovazebního učení na platformě Robocode================
-autor: Bc. Václav Pastušek
-škola: VUT FEKT
-datum: 2023/24
-minimální požadovaná verze Pythonu: 3.10
-aktuální verze Pythonu: {}\n""".format(platform.python_version()))

    @staticmethod
    def pyhelp() -> None:
        """
        Prints Help text.

        :return: None
        """
        print("""Nápověda:
Výpis nápovědy: 'h', 'help'
Výběr epizod použijte: '1', '10', '1e6',... [e>0]
Ukončení programu: 'k', 'e', 'end', 'x' nebo '.'

Vytvoření NN:
    název NN - vytvoří se automaticky, dle aktuálního času; slouží jako primární klíč
    přezdívka NN - 'nn_v1.0'
    vnitřní vrstva - '[]' nebo '[[64,relu,0],[64,relu,0]]' nebo '[[64,gelu,0.1]]'
        - [velikost vrstvy, typ aktivační funkce, dropout pravděpodobnost]
        - (relu, elu, leaky_relu a gelu mají další parametr; u relu je jich více a oddělují se ';')
    vstupní maska - 't' nebo 'false'
    diskontní faktor gama - '0.9' nebo '0.99'
    epsilon - '0.1,0.01,0.01' nebo '0,0,0'
        - epsilon start, epsilon stop, epsilon step
    typ optimizéru - 'adam'
    rychlost učení - '0.0001' nebo '0.01
    typ ztrátové funkce - 'mean_squared_error'
    typ metriky - 'accuracy'
    velikost epochy - '100' nebo '1'
    velikost dávky - '128' nebo '1'
    poznámky - 'vlastní poznámka k danému modelu, třeba počet nebo typ tanků'\n""")

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
    GameSettingsModifier class is designed to modify the settings for the Robocode game. It provides a set of parameters
    and functions to customize various aspects of the game, such as game properties, opponent selection, and rendering
    preferences. The class initializes with default settings, and its methods allow users to update and print the
    modified configurations.
    """
    # parameters for game.properties
    path_to_game_properties: str = "RoboCode/config/game.properties"
    gameWidth: int = 800  # game width: 800  <400; 5000>
    gameHeight: int = 600  # game height: 600  <400; 5000>
    numberOfRounds: int = 1  # number of rounds: 10  <1; max_int(2_147_483_647)>
    isVisible: bool = True  # Game is visible: True
    epsilon: float = 0.0  # epsilon: 0.0
    nnName: str = ""  # NN name: 2024-03-27-15-16-21.keras

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
        17: "PyRobotClient"  # Tank for training AI
    }

    # List of the best tanks
    # best_tanks: list[int] = [16, 11, 13, 14, 2]

    # List of the second best tanks
    # best_tanks: list[int] = [15, 9, 3, 6, 8]

    # List of the worst tanks
    best_tanks: list[int] = [1, 7, 12, 4, 10, 5]

    listOfEnemies: str = ""
    opponents_with_names: list[str] = []

    # listOfEnemies: str = "1, Crazy, 13, Walls, 17"  # opponents list: Crazy, 13, Walls, 17
    # listOfEnemies: str = "12, "*9 + "17"  # 1000 tanks ≈ 3 FPS and 3 TPS
    # listOfEnemies: str = ", ".join([str(i+1) for i in range(len(enemies)-1)]) # all tanks
    # listOfEnemies: str = "16, 11, 13, 14, 2"  # <-- training from 11
    # listOfEnemies: str = "16, 17, 13, 14, 2, 1, 3"  # --> testing from 17

    # listOfEnemies: str = ("Crazy, Fire, MyFirstJuniorRobot, PaintingRobot, RamFire, 17, Tracker, TrackFire,"
    #                      " VelociRobot, Walls")
    # all bots: Corners, Crazy, Fire, Interactive, Interactive_v2, MyFirstJuniorRobot, MyFirstRobot, PaintingRobot,
    # RamFire, SittingDuck, SpinBot, Target, Tracker, TrackFire, VelociRobot, Walls
    # top 10 bots: Crazy, Fire, MyFirstJuniorRobot, PaintingRobot, RamFire, SpinBot, Tracker, TrackFire,
    # VelociRobot, Walls
    # top 5 bots: 1. Walls, 2. SpinBot, 3. Tracker, 4. TrackFire, 5. Crazy

    # parameters for robocode.properties
    path_to_robocode_properties: str = "RoboCode/config/robocode.properties"
    view_ground = True  # True
    rendering_method: int = 1  # 2; 0-2 Default, Quality, Speed
    view_FPS: bool = True  # True
    rendering_antialiasing: int = 1  # 2; 0-2 Default, On, Off
    sound_enableSound: bool = False  # True
    view_robotNames: bool = True  # True
    battle_desiredTPS: int = 90  # 50; TPS<0 => max TPS; TPS=0 => error!
    sound_enableRobotDeath: bool = False  # True
    view_TPS: bool = True  # True
    sound_enableRobotCollision: bool = False  # True
    rendering_forceBulletColor: bool = True  # True
    rendering_noBuffers: int = 3  # 0; 0-3 [max ~40] Without buffer, Single, Double, Triple
    view_explosions: bool = True  # True
    rendering_text_antialiasing: int = 2  # 2; 0-2 Default, On, Off
    rendering_bufferImages: bool = True  # True
    view_explosionDebris: bool = True  # True
    sound_enableBulletHit: bool = False  # True
    view_preventSpeedupWhenMinimized: bool = False  # False
    view_robotEnergy: bool = True  # True
    common_dontHideRankings: bool = True  # True
    sound_enableWallCollision: bool = False  # True
    common_showResults: bool = True  # True
    sound_enableMixerVolume: bool = False  # True
    view_sentryBorder: bool = False  # False
    sound_enableGunshot: bool = False  # True
    common_appendWhenSavingResults: bool = True  # True
    view_scanArcs: bool = False  # False

    # parameters for game.properties
    path_to_window_properties: str = "RoboCode/config/window.properties"
    RobocodeFrame: str = "0,0,1200,800"  # RoboCode frame: 0, 0, 1200, 800

    def __init__(self):
        """
        Initialization of the class. Splits the list of enemies by comma and removes any spaces.
        Converts numbers to enemy names and converts the list back to a string.
        """
        self.regenerate_opponents()

    def regenerate_opponents(self) -> None:
        """
        Regenerates a new set of opponents for the battle.

        :return: None
        """
        selected_tanks: list[int] = rnd.choices(self.best_tanks, k=9)

        # Adding the number 17 to the beginning of the list
        selected_tanks.insert(0, 17)

        # Converting the list to a string
        listOfEnemies: str = ", ".join(map(str, selected_tanks))

        # Split the list of enemies by comma and remove any spaces
        opponents: list[str] = [opponent.strip() for opponent in listOfEnemies.split(",")]

        # Convert numbers to enemy names
        self.opponents_with_names: list[str] = [self.enemies[int(opponent)] if opponent.isdigit() else opponent for
                                                opponent in opponents]
        # Convert the list back to a string
        self.listOfEnemies: str = ", ".join(self.opponents_with_names)

    @staticmethod
    def read_file(filename: str) -> str:
        """
        Reads and return the content of the specified file.

        :param filename: The path to the file to be read.
        :return: The content of the file.
        """
        try:
            with open(filename) as file:  # default is 'r'
                content: str = file.read()
            return content
        except FileNotFoundError:
            print(f"Soubor {filename.removeprefix('RoboCode/config/')} nebyl nalezen.")
            exit(1)
        except Exception as exc:
            print(f"Chyba při čtení souboru: {exc}")
            exit(1)

    @staticmethod
    def write_file(filename: str, content: str) -> None:
        """
        Writes the provided content to the specified file, used for saving Robocode game settings.

        :param filename: The path to the file to write to.
        :param content: The content to be written to the file.
        :return: None
        """
        try:
            with open(filename, 'w') as file:
                file.write(content)
            print(f"Soubor {filename.removeprefix('RoboCode/config/')} byl úspěšně uložen.") if DEBUG_PRINT else None
        except Exception as exc:
            print(f"Chyba při zápisu souboru: {exc}")
            exit(1)

    @staticmethod
    def update_content(var: list[str], var_type: str, content: str) -> str:
        """
        Update the content of a file with a new variable value.

        :param var: Tuple containing the variable name and its new value.
        :param var_type: Type of the variable.
        :param content: Original content of the file.
        :return: Updated content with the new variable value.
        """
        # Unpack the tuple containing the variable name and value
        var_text, var_value = var

        # Remove the prefix from the variable name
        var_text: str = var_text.removeprefix("self.")

        # https://regex101.com/
        # Determine the appropriate regex pattern based on the variable type
        regex_part: str = ""
        match var_type:
            case "int":
                regex_part: str = rf"-?\d+"
            case "bool":
                regex_part: str = rf"\w+"
                var_value: str = var_value.lower()
            case "float":
                regex_part: str = rf"-?\d+(\.\d+)?((e|E)-?\d+)?"
            case "str":
                regex_part: str = rf".*"
                # Remove quotes from the string value if present
                var_value: str = var_value[1:-1] if len(var_value) > 0 else var_value
            case "robocode_bool" | "robocode_int":
                # Prefix the variable name with "robocode.options."
                var_text: str = "robocode.options." + var_text.replace("_", ".")
                match var_type:
                    case "robocode_bool":
                        regex_part: str = rf"\w+"
                        var_value: str = var_value.lower()
                    case "robocode_int":
                        regex_part: str = rf"-?\d+"
            case "frame":
                # Prefix the variable name with "net.sf.robocode.ui.dialog."
                var_text: str = "net.sf.robocode.ui.dialog." + var_text
                # Remove quotes from the string value if present
                var_value: str = var_value[1:-1] if len(var_value) > 0 else var_value
                regex_part: str = rf".*"
            case _:
                # If an unsupported variable type is provided, exit the program
                print("Špatný typ u proměnné")
                exit(1)

        # Search for a match using the regex pattern
        # noinspection PyTypeChecker
        match = re.search(rf"{var_text}\s*=\s*" + regex_part, content)

        # If no match is found, add the variable assignment to the beginning of the content
        if match is None:
            content: str = f"{var_text} = {var_value}\n" + content
        else:
            # If a match is found, replace the variable assignment with the new value
            content: str = re.sub(rf"{var_text}\s*=\s*" + regex_part, f"{var_text} = {var_value}", content)

        return content

    def set_game_properties(self) -> None:
        """
        GameSettingsModifier class is designed to modify the settings for the Robocode game. It provides a set of
        parameters and functions to customize various aspects of the game, such as game properties, opponent selection,
        and rendering preferences. The class initializes with default settings, and its methods allow users to update
        and print the modified configurations.

        :return: None
        """
        content: str = self.read_file(self.path_to_game_properties)
        print("Game properties[:300]:", content[:300]) if DEBUG_PRINT else None

        content: str = self.update_content(f'{self.numberOfRounds=}'.split('='), 'int', content)
        content: str = self.update_content(f'{self.gameWidth=}'.split('='), 'int', content)
        content: str = self.update_content(f'{self.gameHeight=}'.split('='), 'int', content)
        content: str = self.update_content(f'{self.isVisible=}'.split('='), 'bool', content)
        content: str = self.update_content(f'{self.epsilon=}'.split('='), 'float', content)
        content: str = self.update_content(f'{self.nnName=}'.split('='), 'str', content)
        content: str = self.update_content(f'{self.listOfEnemies=}'.split('='), 'str', content)

        print("Game new properties[:300]:", content[:300]) if DEBUG_PRINT else None
        self.write_file(self.path_to_game_properties, content)

    def set_robocode_properties(self) -> None:
        """
        Updates Robocode properties based on class attributes.

        :return: None
        """
        # Read the content of the Robocode properties file
        content: str = self.read_file(self.path_to_robocode_properties)
        print("Robocode properties[:500]:", content[:500]) if DEBUG_PRINT else None

        content: str = self.update_content(f'{self.view_ground=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.rendering_method=}'.split('='), 'robocode_int', content)
        content: str = self.update_content(f'{self.view_FPS=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.rendering_antialiasing=}'.split('='), 'robocode_int',
                                           content)
        content: str = self.update_content(f'{self.sound_enableSound=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.view_robotNames=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.battle_desiredTPS=}'.split('='), 'robocode_int', content)
        content: str = self.update_content(f'{self.sound_enableRobotDeath=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.view_TPS=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.sound_enableRobotCollision=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.rendering_forceBulletColor=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.rendering_noBuffers=}'.split('='), 'robocode_int', content)
        content: str = self.update_content(f'{self.view_explosions=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.rendering_text_antialiasing=}'.split('='), 'robocode_int',
                                           content)
        content: str = self.update_content(f'{self.rendering_bufferImages=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.view_explosionDebris=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.sound_enableBulletHit=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.view_preventSpeedupWhenMinimized=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.view_robotEnergy=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.common_dontHideRankings=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.sound_enableWallCollision=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.common_showResults=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.sound_enableMixerVolume=}'.split('='), 'robocode_bool',
                                           content)
        content: str = self.update_content(f'{self.view_sentryBorder=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.sound_enableGunshot=}'.split('='), 'robocode_bool', content)
        content: str = self.update_content(f'{self.common_appendWhenSavingResults=}'.split('='),
                                           'robocode_bool', content)
        content: str = self.update_content(f'{self.view_scanArcs=}'.split('='), 'robocode_bool', content)

        # Print the updated Robocode properties
        print("Robocode new properties[:500]:", content[:500]) if DEBUG_PRINT else None
        # Write the updated content back to the Robocode properties file
        self.write_file(self.path_to_robocode_properties, content)

    def set_window_properties(self) -> None:
        """
        Updates window properties for Robocode.

        :return: None
        """
        # Read the content of the window properties file
        content: str = self.read_file(self.path_to_window_properties)
        print("Window properties[:300]:", content[:300]) if DEBUG_PRINT else None

        # Update window properties using helper method update_content
        content: str = self.update_content(f'{self.RobocodeFrame=}'.split('='), 'frame', content)

        # Print the updated window properties
        print("Window new properties[:300]:", content[:300]) if DEBUG_PRINT else None

        # Write the updated content back to the window properties file
        self.write_file(self.path_to_window_properties, content)


class UserInterface:
    """
    The UserInterface class represents the interface for interacting with the RoboCode application.
    """

    def __init__(self, utils: Utils):
        self.utils: Utils = utils
        # Path to the folder containing the models and table data
        self.models_folder: str = 'RoboCode/NNModels/'
        self.data_file_name_parameters: str = self.models_folder + '_neural_network_parameters_data.csv'
        self.data_file_name_training: str = self.models_folder + '_neural_network_training_data.csv'
        self.data_file_name_testing: str = self.models_folder + '_neural_network_testing_data.csv'
        self.game_data_file_path = "RoboCode/ModelGameData.txt"
        self.primary_key = 'NN name'
        self.fieldnames: list = [[self.primary_key, 'NN nickname', 'NN hidden layers', 'input mask', 'gamma', 'epsilon',
                                  'optimizer type', 'learning rate', 'loss function type', 'metric type', 'epochs',
                                  'batch size', 'notes'],  # parameters
                                 [self.primary_key, 'sum time', 'number of episodes', 'sum of ranks', 'number of hits',
                                  'my score', 'best score', 'number of movements', 'sum loss', 'sum accuracy',
                                  'action frequency'],  # training
                                 [self.primary_key, 'sum time', 'number of episodes', 'sum of ranks', 'number of hits',
                                  'my score', 'best score', 'number of movements', 'action frequency']]  # testing

        self.keras_model_files: list[str] = []
        self.nn_parameters: dict = {'NN name': "", 'NN nickname': "", 'NN hidden layers': [], 'input mask': False,
                                    'gamma': 0., 'epsilon': [], 'optimizer type': "", 'learning rate': 0.,
                                    'loss function type': "", 'metric type': "", 'epochs': 0, 'batch size': 0,
                                    'notes': ""}
        self.activation_functions: list[str] = ["sigmoid", "softmax", "softplus", "softsign", "tanh", "selu",
                                                "exponential", "relu6", "silu", "hard_silu", "hard_sigmoid", "linear",
                                                "mish", "log_softmax"]
        self.activation_functions_with_value: list[str] = ["relu", "elu", "leaky_relu", "gelu"]
        self.optimizers: list[str] = ["SGD", "RMSprop", "Adam", "AdamW", "Adadelta", "Adagrad", "Adamax", "Adafactor",
                                      "Nadam", "Ftrl", "Lion"]
        # Probabilistic + Regression + Hinge losses functions
        self.losses: list[str] = ["binary_crossentropy", "categorical_crossentropy", "sparse_categorical_crossentropy",
                                  "poisson", "kl_divergence"] + \
                                 ["mean_squared_error", "mean_absolute_error", "mean_absolute_percentage_error",
                                  "mean_squared_logarithmic_error", "cosine_similarity", "huber", "log_cosh"] + \
                                 ["hinge", "squared_hinge", "categorical_hinge"]
        # Accuracy + Probabilistic + Regression + True/False positives & negatives + Image segmentation +
        # Hinge + wrappers and reduction metrics
        self.metrics: list[str] = ["Accuracy", "BinaryAccuracy", "CategoricalAccuracy", "SparseCategoricalAccuracy",
                                   "TopKCategoricalAccuracy", "SparseTopKCategoricalAccuracy"] + \
                                  ["BinaryCrossentropy", "CategoricalCrossentropy", "SparseCategoricalCrossentropy",
                                   "KLDivergence", "Poisson"] + \
                                  ["MeanSquaredError", "RootMeanSquaredError", "MeanAbsoluteError",
                                   "MeanAbsolutePercentageError", "MeanSquaredLogarithmicError", "CosineSimilarity",
                                   "LogCoshError", "R2Score"] + \
                                  ["AUC", "Precision", "Recall", "TruePositives", "TrueNegatives", "FalsePositives",
                                   "FalseNegatives", "PrecisionAtRecall", "RecallAtPrecision",
                                   "SensitivityAtSpecificity", "SpecificityAtSensitivity", "F1Score", "FBetaScore"] + \
                                  ["IoU", "BinaryIoU", "OneHotIoU", "OneHotMeanIoU", "MeanIoU"] + \
                                  ["Hinge", "SquaredHinge", "CategoricalHinge"] + ["MeanMetricWrapper", "Mean", "Sum"]

    def initialize(self) -> None:
        """
        Initializes the UserInterface.

        :return: None
        """
        # Prints out a welcome message.
        self.utils.welcome()

        # Check if the NNModels (NeuralNetworkModels) folder exists
        if not os.path.exists(self.models_folder):
            # Create the folder if it doesn't exist
            os.makedirs(self.models_folder)
            print(f"Složka '{self.models_folder}' byla vytvořena.")

        for idx, data_file_name in enumerate([self.data_file_name_parameters, self.data_file_name_training,
                                              self.data_file_name_testing]):
            # If the file does not exist yet, we create it and write the header.
            try:
                with open(data_file_name, 'x', newline='', encoding='utf-8') as file:
                    writer: csv.DictWriter = csv.DictWriter(file, fieldnames=self.fieldnames[idx])
                    writer.writeheader()
                    print(f"Vytvoření tabulkových dat '{data_file_name}'.")
            except FileExistsError:
                pass

    def check_nn_models(self) -> bool:
        """
        Checks if there are any saved neural network models.

        :return: bool
        """
        # Get a list of all *.keras files in the models_folder directory
        self.keras_model_files: list[str] = [file for file in os.listdir(self.models_folder) if file.endswith(".keras")]
        return bool(self.keras_model_files)

    def create_nn(self) -> None:
        """
        Creates a new neural network.

        :return: None
        """
        # NN parameters:
        # 'NN name': "", 'NN nickname': "", 'NN hidden layers': [], 'input mask': False, 'gamma': 0., 'epsilon': [],
        # 'optimizer type': "", 'learning rate': 0., 'loss function type': "", 'metric type': "", 'epochs': 0,
        # 'batch size': 0, 'notes': ""
        nn_parameters: dict = copy.deepcopy(self.nn_parameters)
        current_param_idx: int = 1
        print("Pro vrácení na předchozí parametr napište 'back'")
        print("Pro přeskočení vytváření NN napište 'skip'")

        timestamp: str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        print(f"Název NN je '{timestamp}.keras'")
        list_nn_parameters: list = list(nn_parameters)
        nn_parameters[list_nn_parameters[0]]: str = timestamp

        # Max length of symbols
        max_length: int = 50
        max_inner_layers: int = 20

        # Loop for entering parameters
        while True:
            if current_param_idx < 1:
                current_param_idx: int = 1
            elif current_param_idx >= len(nn_parameters):
                break

            user_input = input(f"Zadejte {list(nn_parameters)[current_param_idx]}: ").lower()
            if user_input in ['b', 'back']:
                current_param_idx -= 1
                continue
            elif user_input in ['s', 'skip']:
                print("Přeskočení vytváření NN\n")
                return

            # Conditions for help and termination
            if user_input in self.utils.help_list:
                self.utils.pyhelp()
            if user_input in self.utils.end_list:
                print("Program byl úspěšně ukončen.")
                exit(0)

            match current_param_idx:
                case 1:  # NN nickname
                    regex: str = rf'^[\w\s,.:-]{{1,{max_length}}}$'
                    if re.match(regex, user_input):
                        nn_parameters[list_nn_parameters[1]]: str = user_input
                    else:
                        print("Chyba v přezdívce NN, napište to znovu")
                        continue
                case 2:  # NN hidden layers: [[size, https://keras.io/api/layers/activations/, dropout],...]
                    regex: str = rf'^\[(\[.*\](,\[.*\]){{0,{max_inner_layers}}})?\]$'
                    if re.match(regex, user_input):
                        control_input: str = user_input[1:-1].replace(" ", "")
                        if len(control_input) > 0:
                            input_parts: list[str] = control_input[1:-1].split("],[")
                            error_encountered: bool = False
                            for input_part in input_parts:
                                hidden_layer: list[str] = input_part.split(",")
                                if len(hidden_layer) != 3:
                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                    continue
                                try:
                                    if int(float(hidden_layer[0])) <= 0. or not (1. >= float(hidden_layer[2]) >= 0.):
                                        raise ValueError
                                except (ValueError, TypeError):
                                    print(hidden_layer)
                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                    error_encountered: bool = True
                                    break

                                if hidden_layer[1] in self.activation_functions or \
                                        hidden_layer[1].startswith(tuple(self.activation_functions_with_value)):
                                    elu_flag: bool = hidden_layer[1].startswith("elu")
                                    leaky_relu_flag: bool = hidden_layer[1].startswith("leaky_relu")
                                    if hidden_layer[1].startswith("relu") and hidden_layer[1] != "relu6":
                                        control_activation: str = hidden_layer[1][4:]
                                        control_activation_len: int = len(control_activation)
                                        if control_activation_len == 0:
                                            pass
                                        elif control_activation_len > 0:
                                            if control_activation[0] == "(" and control_activation[-1] == ")" and \
                                                    control_activation_len > 2:
                                                control_elements: list[str] = control_activation[1:-1].split(";")
                                                if not (4 > len(control_elements) > 0):
                                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                                    error_encountered: bool = True
                                                    break
                                                try:
                                                    float_elements = [float(s) for s in control_elements]
                                                    if not all(num > 0. for num in float_elements):
                                                        raise ValueError
                                                except (ValueError, TypeError):
                                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                                    error_encountered: bool = True
                                                    break
                                            else:
                                                print("Chyba ve skryté vrstvě, napište to znovu")
                                                error_encountered: bool = True
                                                break
                                        else:
                                            print("Chyba ve skryté vrstvě, napište to znovu")
                                            error_encountered: bool = True
                                            break
                                    elif elu_flag or leaky_relu_flag:
                                        if elu_flag:
                                            control_activation: str = hidden_layer[1][3:]
                                        else:
                                            control_activation: str = hidden_layer[1][10:]
                                        control_activation_len: int = len(control_activation)
                                        if control_activation_len == 0:
                                            pass
                                        elif control_activation_len > 0:
                                            if control_activation[0] == "(" and control_activation[-1] == ")" and \
                                                    control_activation_len > 2:
                                                control_element: str = control_activation[1: -1]
                                                try:
                                                    float_element: float = float(control_element)
                                                    if float_element <= 0.:
                                                        raise ValueError
                                                except (ValueError, TypeError):
                                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                                    error_encountered: bool = True
                                                    break
                                            else:
                                                print("Chyba ve skryté vrstvě, napište to znovu")
                                                error_encountered: bool = True
                                                break
                                        else:
                                            print("Chyba ve skryté vrstvě, napište to znovu")
                                            error_encountered: bool = True
                                            break
                                    elif hidden_layer[1].startswith("gelu"):
                                        control_activation: str = hidden_layer[1][4:]
                                        control_activation_len: int = len(control_activation)
                                        if control_activation_len == 0:
                                            pass
                                        elif control_activation_len > 0:
                                            if control_activation[0] == "(" and control_activation[-1] == ")" and \
                                                    control_activation_len > 2:
                                                control_element: str = control_activation[1: -1]
                                                if control_element not in ["t", "true", "f", "false"]:
                                                    print("Chyba v hodnotě vstupní masky, napište to znovu")
                                                    error_encountered: bool = True
                                                    break
                                            else:
                                                print("Chyba ve skryté vrstvě, napište to znovu")
                                                error_encountered: bool = True
                                                break
                                        else:
                                            print("Chyba ve skryté vrstvě, napište to znovu")
                                            error_encountered: bool = True
                                            break
                                else:
                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                    error_encountered: bool = True
                                    break
                            if error_encountered:
                                continue
                        nn_parameters[list_nn_parameters[2]]: str = user_input
                    else:
                        print("Chyba ve skryté vrstvě, napište to znovu")
                        continue
                case 3:  # input mask
                    if user_input in ["t", "true"]:
                        nn_parameters[list_nn_parameters[3]]: bool = True
                    elif user_input in ["f", "false"]:
                        nn_parameters[list_nn_parameters[3]]: bool = False
                    else:
                        print("Chyba v hodnotě vstupní masky, napište to znovu")
                        continue
                case 4:  # gamma
                    try:
                        float_number: float = float(user_input)
                        if not (1. >= float_number >= 0.):
                            raise ValueError
                    except (ValueError, TypeError):
                        print("Chyba v hodnotě gama, napište to znovu")
                        continue
                    nn_parameters[list_nn_parameters[4]]: float = float_number
                case 5:  # epsilon: start, end, step
                    epsilon_parts: list[str] = user_input.replace(" ", "").split(",")
                    if len(epsilon_parts) != 3:
                        print("Chyba v hodnotách epsilon, napište to znovu")
                        continue
                    epsilons: list[float] = []
                    error_flag: bool = False
                    for epsilon_part in epsilon_parts:
                        try:
                            epsilon: float = float(epsilon_part)
                            if not (1. >= epsilon >= 0.):
                                raise ValueError
                        except (ValueError, TypeError):
                            print("Chyba v hodnotách epsilon, napište to znovu")
                            error_flag: bool = True
                            break
                        epsilons.append(epsilon)
                    if error_flag:
                        continue
                    if epsilons[0] < epsilons[1]:
                        print("Chyba v hodnotách epsilon, napište to znovu")
                        continue
                    nn_parameters[list_nn_parameters[5]] = f"[{user_input.replace(' ', '')}]"
                case 6:  # optimizer type: https://keras.io/api/optimizers/
                    if user_input not in [opt.lower() for opt in self.optimizers]:
                        print("Chyba v typu optimizéru")
                        print("Zvolte jednu z možností:", ", ".join(
                            [option for option in self.optimizers if option.lower().startswith(user_input.lower())]))
                        continue
                    nn_parameters[list_nn_parameters[6]]: str = user_input
                case 7:  # learning rate
                    try:
                        float_number = float(user_input)
                        if not (1. >= float_number >= 0.):
                            raise ValueError
                    except (ValueError, TypeError):
                        print("Chyba v hodnotě rychlosti učení, napište to znovu")
                        continue
                    nn_parameters[list_nn_parameters[7]]: float = float_number
                case 8:  # loss function type: https://keras.io/api/losses/
                    if user_input not in [opt.lower() for opt in self.losses]:
                        print("Chyba v typu ztrátové funkce")
                        print("Zvolte jednu z možností:", ", ".join(
                            [option for option in self.losses if option.lower().startswith(user_input.lower())]))
                        continue
                    nn_parameters[list_nn_parameters[8]]: str = user_input
                case 9:  # metric type: https://keras.io/api/metrics/
                    if user_input not in [opt.lower() for opt in self.metrics]:
                        print("Chyba v typu metriky")
                        print("Zvolte jednu z možností:", ", ".join(
                            [option for option in self.metrics if option.lower().startswith(user_input.lower())]))
                        continue
                    nn_parameters[list_nn_parameters[9]]: str = user_input
                case 10:  # epochs
                    try:
                        float_number = float(user_input)
                        if not (int(float_number) >= 1.):
                            raise ValueError
                    except (ValueError, TypeError):
                        print("Chyba v hodnotě epochy, napište to znovu")
                        continue
                    nn_parameters[list_nn_parameters[10]]: int = int(float_number)
                case 11:  # batch size
                    try:
                        float_number: float = float(user_input)
                        if not (int(float_number) >= 1.):
                            raise ValueError
                    except (ValueError, TypeError):
                        print("Chyba v hodnotě velikosti dávky, napište to znovu")
                        continue
                    nn_parameters[list_nn_parameters[11]]: int = int(float_number)
                case 12:  # notes
                    regex = rf'^[\w\s,.:-]{{1,{max_length * 4}}}$'
                    if re.match(regex, user_input):
                        nn_parameters[list_nn_parameters[12]]: str = user_input
                    else:
                        print("Chyba v poznámce, napište to znovu")
                        continue

            print("Aktuální nastavení NN:", nn_parameters) if DEBUG_PRINT else None

            current_param_idx += 1

            if current_param_idx == 13:
                try:
                    # Open the file in write mode and write data
                    with open(self.data_file_name_parameters, 'a', newline='') as file:
                        writer: csv.DictWriter = csv.DictWriter(file, fieldnames=list(nn_parameters.keys()))
                        writer.writerow(nn_parameters)

                    # Open the training data file in append mode
                    with open(self.data_file_name_training, 'a', newline='') as train_file:
                        train_writer: csv.DictWriter = csv.DictWriter(train_file, fieldnames=self.fieldnames[1])
                        # Create a row with values, where the last element will be an array of 44 zeros
                        row = {key: nn_parameters[self.primary_key] if key == self.primary_key else (
                            [0] * 44 if key == self.fieldnames[1][-1] else (
                                0.0 if key == self.fieldnames[1][-2] or key == self.fieldnames[1][-3] else 0))
                               for key in self.fieldnames[1]}
                        train_writer.writerow(row)

                    # Open the testing data file in append mode
                    with open(self.data_file_name_testing, 'a', newline='') as test_file:
                        test_writer: csv.DictWriter = csv.DictWriter(test_file, fieldnames=self.fieldnames[2])
                        # Create a row with values, where the last element will be an array of 44 zeros
                        row = {key: nn_parameters[self.primary_key] if key == self.primary_key else (
                            [0] * 44 if key == self.fieldnames[2][-1] else 0) for key in self.fieldnames[2]}
                        test_writer.writerow(row)

                    print(f"Data byla úspěšně zapsána do CSV souborů: \n    {self.data_file_name_parameters}"
                          f"\n  {self.data_file_name_training}\n    {self.data_file_name_testing}")
                except PermissionError:
                    print(
                        f"Jeden ze souborů je již otevřený jiným programem."
                        f" Zavřete soubor a stiskněte Enter pro pokračování.")
                    input()
                    continue
                except Exception as e:
                    print(f"Nastala chyba při zápisu do jednoho ze souborů: {e}")
                    input()  # Příkaz pro ruční zavření souboru
                    continue

                # noinspection PyUnresolvedReferences
                # Creating an empty Sequential model
                model = tf.keras.Sequential()

                # Adding the input layer
                model.add(tf.keras.layers.Input(shape=(160,)))

                # Adding hidden layers
                hidden_layers = nn_parameters['NN hidden layers']

                # Regular expression pattern to parse the hidden layers list
                pattern: str = r'\[(\d+),([^,\[\]]+),(0(?:\.\d+)?)\]'
                # Parsing the hidden layers list
                hidden_layers_list: list[any] = ast.literal_eval(re.sub(pattern, r'[\1,"\2",\3]', hidden_layers))

                # https://keras.io/api/layers/initializers  kernel_initializer: random_normal, random_uniform,
                # zeros, ones, ...
                for idx, layer_params in enumerate(hidden_layers_list):
                    size, activation, dropout = layer_params
                    model.add(tf.keras.layers.Dense(size, activation=activation))
                    if dropout:
                        model.add(tf.keras.layers.Dropout(dropout))

                # Adding the output layer
                model.add(tf.keras.layers.Dense(44, activation='linear'))

                # Saving the model in Keras format
                model.save(self.models_folder + nn_parameters[self.primary_key] + ".keras")
                print(f"Nový TensorFlow model byl vytvořen a uložen v '{nn_parameters[self.primary_key]}.keras'.")

                # List to store dataframes from neural network files
                neuron_networks_df: list = []
                # Iterate through each data file: parameters, training, testing
                for data_file_name in [self.data_file_name_parameters, self.data_file_name_training,
                                       self.data_file_name_testing]:
                    # Read each CSV file and append it to the list
                    neuron_networks_df.append(pd.read_csv(data_file_name))

                # Rename columns of training and testing dataframes
                neuron_networks_df[1] = neuron_networks_df[1].drop(columns=self.primary_key).rename(
                    columns=lambda x: f"{x} - train")
                neuron_networks_df[2] = neuron_networks_df[2].drop(columns=self.primary_key).rename(
                    columns=lambda x: f"{x} - test")

                # Concatenate dataframes horizontally
                merged_data_df = pd.concat(neuron_networks_df, axis=1)
                # Display the merged dataframe
                show(merged_data_df)

    def training_nn(self, test_flag: bool = False) -> None:
        """
        Trains the neural network.

        :param test_flag: Flag indicating if testing is enabled.
        :return: None
        """
        # Check if the primary keys match the neural network names without the '.keras' extension
        for nn_name in self.keras_model_files:
            nn_primary_key: str = nn_name[:-6]  # Remove the '.keras' extension
            for file_path in [self.data_file_name_parameters, self.data_file_name_training,
                              self.data_file_name_testing]:
                df = pd.read_csv(file_path)  # Load CSV file into DataFrame
                if nn_primary_key not in df['NN name'].str.strip().values:
                    print(f"Varování: Primární klíč '{nn_primary_key}' nenalezen v {file_path}.")

        # Load data from self.data_file_name_parameters
        df = pd.read_csv(self.data_file_name_parameters)

        # Create a selection of neural networks with their nickname, date, and notes
        options: list[str] = []
        for index, row in df.iterrows():
            option = f"{row['NN nickname']} - {row['NN name']} ({row['notes']})"
            options.append(option)

        # Add help and quit options to the end of the selection
        options.extend(["Nápověda (h)", "Konec programu (k)"])

        selected_nn_number: int = 0
        while True:
            # Printing options
            print("Možnosti:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")

            # Getting user input
            user_input: str = input("\nVyberte neuronovou síť:").lower()

            # Processing user input
            if user_input in self.utils.help_list or user_input == str(len(options) - 1):
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list or user_input == str(len(options)):
                print("Program byl úspěšně ukončen.")
                exit(0)

            try:
                selected_nn_number: int = int(user_input) - 1
                selected_option: str = options[selected_nn_number]
                print(f"Vybraná neuronová síť: {selected_option}")
            except (ValueError, IndexError):
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue

            if selected_nn_number + 1 > len(options) or selected_nn_number + 1 < 1:
                print("Zadané číslo je mimo rozsah možností.")
                continue
            break

        params: list[any] = [elem for elem in df.iterrows()]
        # Epsilons: Extracts epsilon values from params based on selected neural network number
        epsilons: list[float] = params[selected_nn_number][1]['epsilon'][1:-1].split(",")
        # Game_settings: Instantiates GameSettingsModifier class to modify game settings
        game_settings: GameSettingsModifier = GameSettingsModifier()

        # Episodes: Stores the number of episodes initialized to 0
        episodes: int = 0
        # Loop to input the number of episodes
        while True:
            user_input = input("\nZadejte počet epizod (kol):").lower()
            if user_input in self.utils.help_list:
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list:
                print("Program byl úspěšně ukončen.")
                exit(0)

            try:
                episodes: int = int(user_input)
            except (ValueError, IndexError):
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue

            if episodes < 1:
                print("Zadané číslo je mimo rozsah možností.")
                continue
            break

        # Loop to input the game speed
        while True:
            user_input: str = input("\nZadejte rychlost hry (-1 = maximum):").lower()
            if user_input in self.utils.help_list:
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list:
                print("Program byl úspěšně ukončen.")
                exit(0)

            try:
                user_input_number: int = int(user_input)
                game_settings.battle_desiredTPS = user_input_number
                break
            except (ValueError, TypeError):
                print("Neplatný vstup. Zadejte celé číslo.")

        # Loop to input the game visibility
        while True:
            user_input: str = input("\nZadejte viditelnost hry (ano/ne):").lower()
            if user_input in self.utils.help_list:
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list:
                print("Program byl úspěšně ukončen.")
                exit(0)

            if user_input in ['t', 'true', 'y', 'yes', 'a', 'ano']:
                game_settings.isVisible = True
            elif user_input in ['f', 'false', 'n', 'no', 'ne']:
                game_settings.isVisible = False
            else:
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue
            break

        selected_nn_path: str = self.models_folder + params[selected_nn_number][1]['NN name'] + '.keras'
        print(episodes, selected_nn_path) if DEBUG_PRINT else None
        # Creating or loading the TensorFlow model
        if os.path.exists(selected_nn_path):
            # Loading an existing model
            # noinspection PyUnresolvedReferences
            model = tf.keras.models.load_model(selected_nn_path)
            print("Existující TensorFlow model byl načten.")
        else:
            print(f"Nepovedlo se načíst model: {selected_nn_path}")
            return None

        optimizer_type: str = params[selected_nn_number][1]['optimizer type']  # Type of the optimizer used
        learning_rate: float = params[selected_nn_number][1]['learning rate']  # Learning rate of the model
        loss_type: str = params[selected_nn_number][1]['loss function type']  # Type of the loss function used
        metrics_type: str = params[selected_nn_number][1]['metric type']  # Type of metric used for evaluation

        # Find the corresponding full name of the optimizer
        full_optimizer_name = None
        for optimizer in self.optimizers:  # Iterates over available optimizers
            if optimizer.lower() == optimizer_type:  # Checks if the optimizer matches the given type
                full_optimizer_name = optimizer  # Assigns the full name of the optimizer.
                break  # Stops the loop once a match is found.

        # Set up optimizer
        optimizer = getattr(tf.keras.optimizers, full_optimizer_name)(learning_rate=learning_rate)
        # Set epsilon value for exploration in the epsilon-greedy strategy
        if not test_flag:
            game_settings.epsilon = float(epsilons[0])
        else:
            game_settings.epsilon = float(0)

        # Set neural network name from selected path
        game_settings.nnName = selected_nn_path.split("/")[-1]

        # Set predefined game settings (game engine setup)
        print("Nastavení předdefinovaných vlastností:") if DEBUG_PRINT else None
        game_settings.set_game_properties()
        game_settings.set_robocode_properties()
        game_settings.set_window_properties()
        print("Nastavení dokončeno") if DEBUG_PRINT else None

        # Compile the model with optimizer, loss function, and metrics
        model.compile(optimizer=optimizer, loss=loss_type, metrics=[metrics_type])


        start_time: float = time.time()
        empty_file_count: int = 0
        episode: int = 0
        curr_epsilon = float(epsilons[0])
        sum_of_ranks: int = 0
        sum_of_my_score: int = 0
        sum_of_best_score: int = 0
        sum_loss: list[float] = []
        sum_accuracy: list[float] = []
        sum_state: int = 0
        sum_hit_counter: int = 0
        sum_action_frequency: list[int] = [0] * 44
        energy_data: list[list] = []
        sum_good_hit_counter: list = []
        sum_good_hit_counter_min: list = []
        sum_good_hit_counter_avg: list = []
        sum_good_hit_counter_max: list = []
        sum_bad_hit_counter: list = []
        sum_bad_hit_counter_min: list = []
        sum_bad_hit_counter_avg: list = []
        sum_bad_hit_counter_max: list = []
        list_my_score: list[int] = []
        list_best_score: list[int] = []
        list_worst_score: list[int] = []
        list_avg_score: list[float] = []
        all_tanks_names: list[list[str]] = []
        break_flag: bool = False
        while episode < episodes:
            # Check if the file exists
            if os.path.exists(self.game_data_file_path):
                # Open the file in write mode to clear its contents
                with open(self.game_data_file_path, "w") as file:
                    # Clear the contents by writing an empty string
                    file.write("")
                    print(f"Contents of the file {self.game_data_file_path} cleared successfully."
                          ) if DEBUG_PRINT else None
            else:
                print(f"The file {self.game_data_file_path} does not exist.")

            if float(epsilons[2]) != 0.0 and curr_epsilon - float(epsilons[2]) >= float(epsilons[1]):
                curr_epsilon -= float(epsilons[2])
                game_settings.epsilon = curr_epsilon
                game_settings.set_game_properties()
            game_settings.regenerate_opponents()
            game_settings.set_game_properties()
            print(f"Epizoda {episode + 1} - start arény")
            start_ep_time: float = time.time()
            robocode_runner: RobocodeRunner = RobocodeRunner()
            my_rank, my_score, best_score, worst_score, average_score, tanks_names = robocode_runner.start
            print("Čas arény: {:.2f} s".format(time.time() - start_ep_time))

            try:
                with open(self.game_data_file_path) as file:
                    # Reading the file content into a list of lines
                    lines: list[str] = file.readlines()

                    # Checking if the file is empty
                    if not lines:
                        print("Prázdný soubor pro učení")
                        empty_file_count += 1  # Incrementing the count of empty files
                        if empty_file_count >= 10:
                            print("Dosáhnuto 10 prázdných souborů za sebou. Ukončuji trénování.\n")
                            return
                        continue  # Skipping neural network training; it might work the next time
                    else:
                        empty_file_count: int = 0  # Resetting the counter of empty files if the file is not empty
            except FileNotFoundError:
                print("Soubor 'ModelGameData.txt' neexistuje.")
                exit(1)
            except ValueError as ve:
                print(f"Chyba: {ve}")
                exit(1)
            except Exception as e:
                print(f"Neočekávaná chyba: {e}")
                exit(1)

            sum_of_ranks += my_rank
            sum_of_my_score += my_score
            sum_of_best_score += best_score
            list_my_score.append(my_score)
            list_best_score.append(best_score)
            list_worst_score.append(worst_score)
            list_avg_score.append(average_score)
            all_tanks_names.append(game_settings.opponents_with_names)

            # Initializing lists for states and actions
            states: list = []
            actions: list = []

            # Iterating through each string in the array
            for line in lines:
                # Splitting the string by the '|' character
                parts: list[str] = line.strip().split('|')

                # Checking if both parts (state and action) were found
                if len(parts) == 2:
                    # Splitting and converting the first part into float numbers
                    states_float: list = [np.float32(x) for x in parts[0].split()]

                    # Splitting and converting the second part into float numbers
                    actions_float: list = np.float32(parts[1])

                    # Adding to the states list
                    states.append(states_float)

                    # Adding to the actions list
                    actions.append(actions_float)
                else:
                    print(f"Chyba při rozdělování: {line}")

            # Printing lists of states and actions
            print("Seznam stavů:", states[:5]) if DEBUG_PRINT else None
            print("Seznam akcí:", actions[:5]) if DEBUG_PRINT else None

            # Converting lists to numpy arrays
            states_np = np.array(states, dtype=np.float32)
            actions_np = np.array(actions, dtype=np.float32)

            # Extracting energy data from states
            episode_energy = np.transpose(states_np[:, :10 * 8:8]).tolist()
            energy_data.append(episode_energy)

            # Applying input mask if enabled
            if params[selected_nn_number][1]['input mask']:
                states_np[:, 7][states_np[:, 7] == 3.0] = 0.0

            # Updating total state count
            sum_state += len(states)

            if np.any(np.isinf(states_np)) or np.any(np.isnan(states_np)):
                print("inf or nan stavy:", states_np)

            if np.any(np.isinf(actions_np)) or np.any(np.isnan(actions_np)):
                print("inf or nan akce:", actions_np)

            targets: np.ndarray = np.zeros((len(actions_np), 44))
            gamma: float = 0.99
            same_actions: np.ndarray = actions_np[0]
            action_frequency: list[int] = [0] * 44
            all_actions_for_reward: list[int] = [0] * 44
            good_hit_counter: list[int] = [0] * 10
            bad_hit_counter: list[int] = [0] * 10
            for i in range(len(actions_np) - 1):  # Iterate through actions, excluding the last one
                reward: float = -1.  # Initialize reward with a small negative value

                # Increment action frequency counter
                action_frequency[int(actions_np[i])] += 1
                all_actions_for_reward[int(actions_np[i])] += 1

                # Update counters for action rewards
                if actions_np[i] != same_actions:
                    same_actions = actions_np[i]
                    for _ in range(10):
                        if sum(1 for value in all_actions_for_reward if value != 0) > 1:
                            all_actions_for_reward = [value - 1 if value != 0 else value for
                                                      value in all_actions_for_reward]

                # Calculate reward based on sum of actions
                sum_action = sum(all_actions_for_reward)
                if sum_action > 29:
                    reward -= (sum_action - 29.) / 100.

                # Get current and next state
                curr_state = np.expand_dims(states_np[i], axis=0)
                next_state = np.expand_dims(states_np[i + 1], axis=0)

                # Predict Q-values for current and next states
                targets[i] = model.predict(curr_state)
                Qsa = np.max(model.predict(next_state))

                # Calculate delta energy and update hit counters
                delta_energy = [states_np[i + 1][k] - states_np[i][k] for k in range(0, 80, 8)]
                for k in range(10):
                    if delta_energy[k] > 0:
                        good_hit_counter[k] += 1
                    else:
                        bad_hit_counter[k] += 1

                # Update reward based on delta energy
                if delta_energy[0] > 0:
                    reward += delta_energy[0] * 50
                else:
                    reward += delta_energy[0] * 5

                # Adjust reward based on tank state
                tank_state = int(states_np[i][7])
                if tank_state in [1, 2]:
                    reward -= 25.

                # Update target Q-values with reward and gamma
                targets[i, int(actions_np[i])] = reward + gamma * Qsa

            print("všechny použité akce:", action_frequency, "celkem různých:",
                  sum(1 for value in action_frequency if value != 0))

            if not test_flag:
                # Set the target value for the last action based on the good_hit_counter
                targets[len(actions_np) - 1, int(actions_np[len(actions_np) - 1])] = -10. + good_hit_counter[0] * 50 + \
                                                                                     (10 - my_rank) * 20
                epochs = params[selected_nn_number][1]['epochs']  # Number of epochs for training
                batch_size = params[selected_nn_number][1]['batch size']  # Batch size for training
                max_attempts: int = 10  # Maximum number of attempts
                history: any = None
                for attempt in range(max_attempts):
                    try:
                        # Train the model using fit method from Keras API
                        history = model.fit(states_np, targets, epochs=epochs, batch_size=batch_size, verbose=0,
                                            workers=10, use_multiprocessing=True, callbacks=[NaNCallback()])
                        break  # If training succeeds, exit the loop
                    except Exception as e:
                        print(f"Chyba při tréninku modelu (pokus {attempt + 1}): {e}")
                        tf.compat.v1.reset_default_graph()  # Clear TensorFlow graph
                        tf.compat.v1.keras.backend.clear_session()  # Clear TensorFlow backend
                        tf.keras.backend.clear_session()
                        print("config:", tf.config.list_physical_devices('GPU'))
                        if tf.config.list_physical_devices('GPU'):
                            # Reset memory stats for GPU:0
                            tf.config.experimental.reset_memory_stats('GPU:0')
                        del model
                        # Reload the model from the selected path
                        model = tf.keras.models.load_model(selected_nn_path)
                        # Compile the model with specified optimizer, loss, and metrics
                        model.compile(optimizer=optimizer, loss=loss_type, metrics=[metrics_type])
                        gc.collect()  # Run garbage collection to free up memory
                        time.sleep(10)  # Wait for 10 seconds
                        # Print garbage collector status
                        print("Garbage collector:", gc.get_count()) if DEBUG_PRINT else None

                        if attempt < max_attempts - 1:
                            print("Pokus o znovu trénink modelu.")
                        else:
                            print("Dosáhli jste maximálního počtu pokusů. Trénink modelu selhal.")
                            print("U GPU je občas problém s opakovaným voláním model.fit() (padá na 150. trénování)")
                            print("Doporučuji přerušit program a znovu spustit.")
                            break_flag: bool = True
                            break

                if break_flag:
                    return None

                train_loss = np.mean(history.history['loss'])
                print("Trénovací ztráta: {:.2f}. ".format(train_loss), end="")
                train_accuracy = np.mean(history.history['accuracy'])
                print("Trénovací přesnost: {:.2f}.".format(train_accuracy))

                # Save the TF model to a file
                model.save(selected_nn_path)
                print(f"Model uložen zde: {selected_nn_path}") if DEBUG_PRINT else None

                sum_loss.append(train_loss)
                sum_accuracy.append(train_accuracy)

            sum_hit_counter += good_hit_counter[0]
            sum_action_frequency: list[int] = [x + y for x, y in zip(sum_action_frequency, action_frequency)]
            sum_good_hit_counter.append(good_hit_counter[0])
            sum_good_hit_counter_min.append(np.min(good_hit_counter))
            sum_good_hit_counter_avg.append(np.mean(good_hit_counter))
            sum_good_hit_counter_max.append(np.max(good_hit_counter))
            sum_bad_hit_counter.append(bad_hit_counter[0])
            sum_bad_hit_counter_min.append(np.min(bad_hit_counter))
            sum_bad_hit_counter_avg.append(np.mean(bad_hit_counter))
            sum_bad_hit_counter_max.append(np.max(bad_hit_counter))

            print("\nEpizoda", episode + 1, "dokončena")
            print("Čas na epizodu: {:.2f} s\n".format(time.time() - start_ep_time))
            episode += 1

        delta_time: float = time.time() - start_time
        print("Celkový čas: {:.2f} s. ".format(delta_time), end="")
        print("Průměrný čas: {:.2f} s.\n".format(delta_time / episodes))

        data_file_name: str = self.data_file_name_training if not test_flag else self.data_file_name_testing
        df: pd.DataFrame = pd.read_csv(data_file_name)  # Loading pandas DataFrame from a CSV file
        # Selecting a row from the DataFrame and making a copy
        selected_row: pd.Series = df.loc[selected_nn_number].copy()

        values_to_add = {
            'sum time': round(delta_time),  # Summing up time values
            'number of episodes': episodes,  # Adding number of episodes
            'sum of ranks': sum_of_ranks,  # Summing up ranks
            'number of hits': sum_hit_counter,  # Adding number of hits
            'my score': sum_of_my_score,  # Summing up personal scores
            'best score': sum_of_best_score,  # Summing up best scores
            'number of movements': sum_state,  # Adding number of movements
        }

        if not test_flag:
            values_to_add.update({
                'sum loss': np.round(sum(sum_loss), decimals=1),  # Summing up losses
                'sum accuracy': np.round(sum(sum_accuracy), decimals=1)  # Summing up accuracies
            })

        for column, value in values_to_add.items():
            selected_row[column] += value  # Updating values in the selected row

        previous_action_frequency: list[int] = df.loc[selected_nn_number]['action frequency'].replace(" ", "")[
                                               1:-1].split(",")

        previous_action_frequency: list[int] = [int(x) for x in previous_action_frequency]
        new_action_frequency: list[int] = [x + y for x, y in zip(previous_action_frequency, sum_action_frequency)]
        selected_row['action frequency']: pd.Series = new_action_frequency
        df.loc[selected_nn_number]: pd.Series = selected_row  # Updating the DataFrame with the modified row
        try:
            df.to_csv(data_file_name, index=False)  # Saving the DataFrame to a CSV file
        except PermissionError:
            print("Nemáte oprávnění k zápisu do souboru.")
            print("Jedna z možností je, že máte otevřený soubor, který je potřeba mít zavřený pro zápis.")
            while True:
                try:
                    df.to_csv(data_file_name, index=False)  # Trying to save again
                    break  # If successful, exit the loop
                except PermissionError:
                    time.sleep(1)  # Waiting for a second before retrying

        if NOTIFICATION_SOUND:
            for i in range(30):
                if i % 5 == 0:
                    time.sleep(1)
                winsound.Beep(2000 if test_flag else 4000, 250)

        z_episodes: list[int] = list(range(1, episodes + 1))
        # Creating the first plot
        fig1, (ax, tank_names_ax) = plt.subplots(1, 2, figsize=(10, 6), gridspec_kw={
            'width_ratios': [13, 1]})  # Dividing space for the plot and tank names

        # Creating axes for all episodes
        axes_list = [ax] + [plt.axes(ax.get_position(), visible=False) for _ in range(episodes - 1)]

        # Setting data and title for each episode
        for i, ax_i in enumerate(axes_list):
            x_time = list(range(len(energy_data[i][0])))  # List of time points for the current episode
            tank_names: list[str] = all_tanks_names[i]
            for j in range(10):
                alpha_value = 0.4  # Default transparency for all plots
                markersize_value = 4
                marker_value = ','
                label_value: str = tank_names[j]
                if j == 0:
                    alpha_value = 1.0  # The first tank in the first episode won't be transparent
                    markersize_value = 8  # Larger marker size
                ax_i.plot(x_time, energy_data[i][j], marker=marker_value, markersize=markersize_value,
                          alpha=alpha_value, linestyle='-', label=label_value)
            ax_i.set_xlabel('Čas [herní tik]')
            ax_i.set_ylabel('Energie tanků [-]')
            ax_i.set_title(f'Energie tanků za epizody - epizoda: {z_episodes[i]}')
            ax_i.set_xlim(0, len(x_time))  # Adjusting the x-axis range
            min_energy = min(min(energy_data[i][j]) for j in range(10))
            max_energy = max(max(energy_data[i][j]) for j in range(10))
            ax_i.set_ylim(min_energy - .5, max_energy + .5)  # Adjusting the y-axis range

            # Creating legend for each plot
            ax_i.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
            ax_i.grid(True)

        # Creating a slider for selecting episodes
        episode_slider_ax = plt.axes((0.1, 0.01, 0.8, 0.03))
        min_episode = min(z_episodes)
        max_episode = max(z_episodes)
        if episodes == 1:
            episode_slider = Slider(episode_slider_ax, 'Epizoda', min_episode - 0.5, max_episode + 0.5,
                                    valinit=1, valstep=1)
        else:
            episode_slider = Slider(episode_slider_ax, 'Epizoda', min_episode, max_episode, valinit=min_episode,
                                    valstep=1)

        def update(val) -> None:
            """
            Function to update the plot when episode changes.

            :param val:
            :return:
            """
            episode_index = int(episode_slider.val) - 1
            for i, ax_i in enumerate(axes_list):
                ax_i.set_visible(i == episode_index)
            fig1.canvas.draw_idle()

        episode_slider.on_changed(update)

        def scroll(event) -> None:
            """
            Function for scrolling the slider using mouse wheel

            :param event:
            :return:
            """
            current_value = episode_slider.val
            if event.button == 'up':
                episode_slider.set_val(min(current_value + 1, max(z_episodes)))
            elif event.button == 'down':
                episode_slider.set_val(max(current_value - 1, min(z_episodes)))

        fig1.canvas.mpl_connect('scroll_event', scroll)

        # Displaying tank names in the right area
        tank_names_ax.axis('off')

        plt.grid(True)
        plt.show(block=False)

        # Definice dat
        z_episodes: range = range(1, episodes + 1)

        # Určení počtu kroků pro zobrazení na ose x (maximálně 10)
        step: int = max(1, episodes // 10)
        x_ticks: int | range = z_episodes[::step]

        fig2 = plt.figure(figsize=(10, 6))
        plt.plot(z_episodes, list_my_score, label='Skóre AI tanku', marker='o')
        plt.plot(z_episodes, list_worst_score, label='Nejhorší skóre', linestyle='--', marker='x')
        plt.plot(z_episodes, list_avg_score, label='Průměrné skóre', linestyle='-.', marker='s')
        plt.plot(z_episodes, list_best_score, label='Nejlepší skóre', linestyle=':', marker='^')
        # Setting labels for x and y axis
        plt.xlabel('Epizoda')
        plt.ylabel('Získané skóre')
        plt.title('Získané skóre za epizody')
        plt.grid(True)
        # Setting the display of values on the x-axis
        plt.xticks(x_ticks)
        # Adding legend and grid
        plt.legend()
        # Displaying the graph
        plt.show(block=False)

        fig3 = plt.figure(figsize=(10, 6))
        plt.plot(z_episodes, sum_good_hit_counter, label='AI tank', marker='o')
        plt.plot(z_episodes, sum_good_hit_counter_min, label='Nejhorší tank', linestyle='--', marker='x')
        plt.plot(z_episodes, sum_good_hit_counter_avg, label='Průměrný tank', linestyle='-.', marker='s')
        plt.plot(z_episodes, sum_good_hit_counter_max, label='Nejlepší tank', linestyle=':', marker='^')
        # Setting labels for x and y axis
        plt.xlabel('Epizoda')
        plt.ylabel('Počet zásahů za epizody')
        plt.title('Zásahy tanků')
        # Setting the display of values on the x-axis
        plt.xticks(x_ticks)
        # Adding legend and grid
        plt.legend()
        plt.grid(True)
        # Displaying the graph
        plt.show(block=False)

        blue_colors = plt.cm.Blues(np.linspace(0.9, 0.6, 5))
        green_colors = plt.cm.Greens(np.linspace(0.6, 0.9, 5))
        # Colors for all bars
        colors = [blue_colors[i // 5] if i < 25 else green_colors[(i - 24) // 5] for i in
                  range(len(sum_action_frequency))]

        # Number of blue actions
        count_blue_actions = sum(sum_action_frequency[:25])
        # Number of green actions
        count_green_actions = sum(sum_action_frequency[25:])

        # Create a bar plot
        fig4 = plt.figure(figsize=(10, 6))
        plt.bar(range(len(sum_action_frequency)), sum_action_frequency, color=colors, alpha=0.7)
        plt.xlabel('Index akce')
        plt.ylabel('Frekvence')
        plt.title('Frekvence akcí')
        plt.text(3, max(sum_action_frequency) * 0.95, 'Pohyb tanku ({} %)'.format(
            round(count_blue_actions / sum(sum_action_frequency) * 100, 2)),
                 color='darkblue', fontsize=12, fontweight='bold')
        plt.text(23, max(sum_action_frequency) * 0.95, 'Střelba s otočením kanónu ({} %)'.format(
            round(count_green_actions / sum(sum_action_frequency) * 100, 2)), color='darkgreen', fontsize=12,
                 fontweight='bold')
        plt.xticks(np.arange(0, len(sum_action_frequency), 5))
        plt.grid(True)
        if not test_flag:
            plt.show(block=False)
        else:
            plt.show()

        z_episodes: list[int] = list(range(1, episodes + 1))

        # Determining the number of steps to display on the x-axis (maximum of 10)
        step = max(1, episodes // 10)
        x_ticks: list[int] = z_episodes[::step]

        fig5, ax1 = plt.subplots()
        if not test_flag:
            # First Y-axis
            ax1.plot(z_episodes, sum_loss, 'g-', label='Ztrátová hodnota', marker='o')
            ax1.set_xlabel('Epizoda')
            ax1.set_ylabel('Ztrátová hodnota za epizody', color='g')
            ax1.set_ylim(0, max(sum_loss) * 1.1)

            # Creating the second Y-axis
            ax2 = ax1.twinx()
            ax2.plot(z_episodes, sum_accuracy, 'b-', label='Přesnost', marker='x')
            ax2.set_ylabel('Přesnost', color='b')
            ax2.set_ylim(0, max(sum_accuracy) * 1.2)

            plt.title('Ztrátová hodnota a přesnost AI tanku')

            # Combined legend from both axes
            lines_1, labels_1 = ax1.get_legend_handles_labels()
            lines_2, labels_2 = ax2.get_legend_handles_labels()
            lines = lines_1 + lines_2
            labels = labels_1 + labels_2
            ax1.legend(lines, labels, loc='upper right')
            ax1.grid(True)
            plt.grid(True)
            # Setting the display of values on the x-axis
            plt.xticks(x_ticks)
            plt.show()

        # Create a folder for saving graphs if it doesn't exist yet
        if not os.path.exists("graphs"):
            os.makedirs("graphs")

        name_prefix: str = params[selected_nn_number][1]['NN name'] + ("-train" if not test_flag else "-test")

        # List files in the folder
        files = os.listdir("graphs/")

        # List files with the desired prefix
        matching_files = [file for file in files if file.startswith(name_prefix)]

        # If files with the desired prefix are found
        if matching_files:
            # Determine the number for the new file
            numbers = [int(file.split("_")[1].split(".")[0]) for file in matching_files]
            new_number = max(numbers) + 1
        else:
            # If no files with the desired prefix exist, start with number 1
            new_number = 1

        # Creating a new file name for graph
        new_filename = f"graphs/{name_prefix}_{new_number}.pdf"

        with PdfPages(new_filename) as pdf:
            pdf.savefig(fig2)
            pdf.savefig(fig3)
            pdf.savefig(fig4)
            if not test_flag:
                pdf.savefig(fig5)
            for episode_number in z_episodes:
                episode_slider.set_val(episode_number)  # Sets the slider to the given episode number
                pdf.savefig(fig1)  # Adds the current state of the graph to the PDF

    def testing_nn(self) -> None:
        """
        Tests the neural network.

        :return: None
        """
        self.training_nn(test_flag=True)

    def copy_nn(self) -> None:
        """
        Copies the neural network.

        :return: None
        """
        # Loading data from self.data_file_name_parameters
        df = pd.read_csv(self.data_file_name_parameters)

        # Creating a selection of neural networks with their nickname, date, and notes
        options = []
        for index, row in df.iterrows():
            option = f"{row['NN nickname']} - {row['NN name']} ({row['notes']})"
            options.append(option)

        # Adding help and quit options to the end of the selection
        options.extend(["Nápověda (h)", "Konec programu (k)"])

        selected_nn_number: int = 0
        while True:
            # Display selection
            print("Možnosti:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")

            # Get user input
            user_input = input("\nVyberte neuronovou síť:").lower()

            # Process user input
            if user_input in self.utils.help_list or user_input == str(len(options) - 1):
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list or user_input == str(len(options)):
                print("Program byl úspěšně ukončen.")
                exit(0)

            try:
                selected_nn_number = int(user_input) - 1
                selected_option = options[selected_nn_number]
                print(f"Vybraná neuronová síť: {selected_option}")
            except (ValueError, IndexError):
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue

            if selected_nn_number + 1 > len(options) or selected_nn_number + 1 < 1:
                print("Zadané číslo je mimo rozsah možností.")
                continue
            break

        only_params_copy: bool = False
        while True:
            user_input = input("\nZadejte zda chcete jen kopii parametrů s novou NN nebo ne:").lower()
            if user_input in self.utils.help_list:
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list:
                print("Program byl úspěšně ukončen.")
                exit(0)

            if user_input in ['t', 'true', 'y', 'yes', 'a', 'ano']:
                only_params_copy = True
            elif user_input in ['f', 'false', 'n', 'no', 'ne']:
                only_params_copy = False
            else:
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue
            break

        copied_params = copy.deepcopy(df.iloc[selected_nn_number])
        old_NN_name = copied_params['NN name']
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        copied_params['NN name'] = timestamp

        # Adding a copy of parameters to the DataFrame using concat
        new_df = pd.concat([df, pd.DataFrame([copied_params])], ignore_index=True)

        while True:
            try:
                # Saving data to CSV files
                new_df.to_csv(self.data_file_name_parameters, index=False)

                with open(self.data_file_name_training, 'a', newline='') as train_file:
                    train_writer = csv.DictWriter(train_file, fieldnames=self.fieldnames[1])
                    # Creating a row with values, where the last element will be an array of 44 zeros
                    row = {key: copied_params[self.primary_key] if key == self.primary_key else (
                        [0] * 44 if key == self.fieldnames[1][-1] else (
                            0.0 if key == self.fieldnames[1][-2] or key == self.fieldnames[1][-3] else 0)) for
                           key in self.fieldnames[1]}
                    train_writer.writerow(row)

                with open(self.data_file_name_testing, 'a', newline='') as test_file:
                    test_writer = csv.DictWriter(test_file, fieldnames=self.fieldnames[2])
                    # Creating a row with values, where the last element will be an array of 44 zeros
                    row = {key: copied_params[self.primary_key] if key == self.primary_key else (
                        [0] * 44 if key == self.fieldnames[2][-1] else 0) for key in self.fieldnames[2]}
                    test_writer.writerow(row)

                print(f"Data byla úspěšně zapsána do CSV souborů: \n    {self.data_file_name_parameters}"
                      f"\n  {self.data_file_name_training}\n    {self.data_file_name_testing}")
                break
            except PermissionError:
                print(
                    f"Jeden ze souborů je již otevřený jiným programem."
                    f" Zavřete soubor a stiskněte Enter pro pokračování.")
                input()
                continue
            except Exception as e:
                print(f"Nastala chyba při zápisu do jednoho ze souborů: {e}")
                input()
                continue

        selected_nn_path = self.models_folder + old_NN_name + '.keras'
        print(selected_nn_path) if DEBUG_PRINT else None
        # Creating or loading the TensorFlow model
        if os.path.exists(selected_nn_path):
            # Loading an existing model
            # noinspection PyUnresolvedReferences
            model = tf.keras.models.load_model(selected_nn_path)
            print("Existující TensorFlow model byl načten.")
        else:
            print(f"Nepovedlo se načíst model: {selected_nn_path}")
            return None

        model_cloned = tf.keras.models.clone_model(model)
        if not only_params_copy:
            # Setting weights to the cloned model
            model_cloned.set_weights(model.get_weights())

        # Getting the folder path
        folder_path = os.path.dirname(selected_nn_path)

        # New filename for saving the model
        new_model_filename = os.path.join(folder_path, timestamp + '.keras')

        # Saving the model under the new filename
        model.save(new_model_filename)

    def change_nn(self) -> None:
        """
        Changes the neural network.

        :return: None
        """
        # NN parameters:
        # 'NN name': "", 'NN nickname': "", 'NN hidden layers': [], 'input mask': False, 'gamma': 0., 'epsilon': [],
        # 'optimizer type': "", 'learning rate': 0., 'loss function type': "", 'metric type': "", 'epochs': 0,
        # 'batch size': 0, 'notes': ""

        # Check if the primary keys match the neural network names without the '.keras' extension
        for nn_name in self.keras_model_files:
            nn_primary_key = nn_name[:-6]  # Remove the '.keras' extension
            for file_path in [self.data_file_name_parameters, self.data_file_name_training,
                              self.data_file_name_testing]:
                df = pd.read_csv(file_path)  # Load CSV file into DataFrame
                if nn_primary_key not in df['NN name'].str.strip().values:
                    print(f"Varování: Primární klíč '{nn_primary_key}' nenalezen v {file_path}.")
                    return None

        # Loading data from self.data_file_name_parameters
        df = pd.read_csv(self.data_file_name_parameters)

        # Creating a selection of neural networks with their nickname, date, and notes
        options = []
        for index, row in df.iterrows():
            option = f"{row['NN nickname']} - {row['NN name']} ({row['notes']})"
            options.append(option)

        # Adding help and quit options to the end of the selection
        options.extend(["Nápověda (h)", "Konec programu (k)"])

        selected_nn_number: int = 0
        while True:
            # Options output
            print("Možnosti:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")

            # User input retrieval
            user_input = input("\nVyberte neuronovou síť:").lower()

            # User input processing
            if user_input in self.utils.help_list or user_input == str(len(options) - 1):
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list or user_input == str(len(options)):
                print("Program byl úspěšně ukončen.")
                exit(0)

            try:
                selected_nn_number = int(user_input) - 1
                selected_option = options[selected_nn_number]
                print(f"Vybraná neuronová síť: {selected_option}")
            except (ValueError, IndexError):
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue

            if selected_nn_number + 1 > len(options) or selected_nn_number + 1 < 1:
                print("Zadané číslo je mimo rozsah možností.")
                continue
            break

        params = copy.deepcopy([elem for elem in df.iterrows()])
        selected_nn_path = self.models_folder + params[selected_nn_number][1]['NN name'] + '.keras'

        if os.path.exists(selected_nn_path):
            # Loading an existing model
            # noinspection PyUnresolvedReferences
            model = tf.keras.models.load_model(selected_nn_path)
            print("Existující TensorFlow model byl načten.")
        else:
            print(f"Nepovedlo se načíst model: {selected_nn_path}")
            return None

        print("Vstupní vrstva:", model.input_shape[1])
        print(model.summary())
        print(f"\nParametry NN:\n{params[selected_nn_number][1]}")
        print("Pro ukončení modifikace parametrů NN napište 'skip'")
        old_nn_hidden_layers = params[selected_nn_number][1]["NN hidden layers"]

        break_flag = False
        index_param: int = 0
        while True:
            param_key: list = []
            while True:
                user_input = input("\nVyberte si indexem parametr pro úpravu (potvrďte napsáním 'skip'):").lower()
                if user_input in ['s', 'skip']:
                    break_flag = True
                    break
                if user_input in self.utils.help_list:
                    self.utils.pyhelp()
                    continue
                if user_input in self.utils.end_list:
                    print("Program byl úspěšně ukončen.")
                    exit(0)

                try:
                    index_param = int(user_input)
                    if not (0 < index_param < len(self.nn_parameters)):
                        print("Zadané číslo je mimo rozsah možností.")
                        continue
                    param_key = list(self.nn_parameters.keys())[index_param]
                    param_value = params[selected_nn_number][1][param_key]
                    print(f"Vybrán parametr {param_key} s hodnotou {param_value}.")
                    break
                except (ValueError, IndexError):
                    print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                    continue

            if break_flag:
                break
            # Max length of symbols
            max_length = 50
            max_inner_layers = 20

            # Loop for entering parameters
            while True:
                user_input = input(f"Zadejte {list(self.nn_parameters.keys())[index_param]}: ").lower()
                if user_input in ['s', 'skip']:
                    break_flag = True
                    break

                # Conditions for help and termination
                if user_input in self.utils.help_list:
                    self.utils.pyhelp()
                if user_input in self.utils.end_list:
                    print("Program byl úspěšně ukončen.")
                    exit(0)

                match index_param:
                    case 1:  # NN nickname
                        regex = rf'^[\w\s,.:-]{{1,{max_length}}}$'
                        if re.match(regex, user_input):
                            params[selected_nn_number][1][param_key] = user_input
                        else:
                            print("Chyba v přezdívce NN, napište to znovu")
                            continue
                    case 2:  # NN hidden layers: [[size, https://keras.io/api/layers/activations/, dropout],...]
                        regex = rf'^\[(\[.*\](,\[.*\]){{0,{max_inner_layers}}})?\]$'
                        if re.match(regex, user_input):
                            control_input = user_input[1:-1].replace(" ", "")
                            if len(control_input) > 0:
                                input_parts = control_input[1:-1].split("],[")
                                error_encountered = False
                                for input_part in input_parts:
                                    hidden_layer = input_part.split(",")
                                    if len(hidden_layer) != 3:
                                        print("Chyba ve skryté vrstvě, napište to znovu")
                                        continue
                                    try:
                                        if int(float(hidden_layer[0])) <= 0. or not (
                                                1. >= float(hidden_layer[2]) >= 0.):
                                            raise ValueError
                                    except (ValueError, TypeError):
                                        print(hidden_layer)
                                        print("Chyba ve skryté vrstvě, napište to znovu")
                                        error_encountered = True
                                        break

                                    if hidden_layer[1] in self.activation_functions or \
                                            hidden_layer[1].startswith(tuple(self.activation_functions_with_value)):
                                        elu_flag = hidden_layer[1].startswith("elu")
                                        leaky_relu_flag = hidden_layer[1].startswith("leaky_relu")
                                        if hidden_layer[1].startswith("relu") and hidden_layer[1] != "relu6":
                                            control_activation = hidden_layer[1][4:]
                                            control_activation_len = len(control_activation)
                                            if control_activation_len == 0:
                                                pass
                                            elif control_activation_len > 0:
                                                if control_activation[0] == "(" and control_activation[-1] == ")" and \
                                                        control_activation_len > 2:
                                                    control_elements = control_activation[1:-1].split(";")
                                                    if not (4 > len(control_elements) > 0):
                                                        print("Chyba ve skryté vrstvě, napište to znovu")
                                                        error_encountered = True
                                                        break
                                                    try:
                                                        float_elements = [float(s) for s in control_elements]
                                                        if not all(num > 0. for num in float_elements):
                                                            raise ValueError
                                                    except (ValueError, TypeError):
                                                        print("Chyba ve skryté vrstvě, napište to znovu")
                                                        error_encountered = True
                                                        break
                                                else:
                                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                                    error_encountered = True
                                                    break
                                            else:
                                                print("Chyba ve skryté vrstvě, napište to znovu")
                                                error_encountered = True
                                                break
                                        elif elu_flag or leaky_relu_flag:
                                            if elu_flag:
                                                control_activation = hidden_layer[1][3:]
                                            else:
                                                control_activation = hidden_layer[1][10:]
                                            control_activation_len = len(control_activation)
                                            if control_activation_len == 0:
                                                pass
                                            elif control_activation_len > 0:
                                                if control_activation[0] == "(" and control_activation[-1] == ")" and \
                                                        control_activation_len > 2:
                                                    control_element = control_activation[1: -1]
                                                    try:
                                                        float_element = float(control_element)
                                                        if float_element <= 0.:
                                                            raise ValueError
                                                    except (ValueError, TypeError):
                                                        print("Chyba ve skryté vrstvě, napište to znovu")
                                                        error_encountered = True
                                                        break
                                                else:
                                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                                    error_encountered = True
                                                    break
                                            else:
                                                print("Chyba ve skryté vrstvě, napište to znovu")
                                                error_encountered = True
                                                break
                                        elif hidden_layer[1].startswith("gelu"):
                                            control_activation = hidden_layer[1][4:]
                                            control_activation_len = len(control_activation)
                                            if control_activation_len == 0:
                                                pass
                                            elif control_activation_len > 0:
                                                if control_activation[0] == "(" and control_activation[-1] == ")" and \
                                                        control_activation_len > 2:
                                                    control_element = control_activation[1: -1]
                                                    if control_element not in ["t", "true", "f", "false"]:
                                                        print("Chyba v hodnotě vstupní masky, napište to znovu")
                                                        error_encountered = True
                                                        break
                                                else:
                                                    print("Chyba ve skryté vrstvě, napište to znovu")
                                                    error_encountered = True
                                                    break
                                            else:
                                                print("Chyba ve skryté vrstvě, napište to znovu")
                                                error_encountered = True
                                                break
                                    else:
                                        print("Chyba ve skryté vrstvě, napište to znovu")
                                        error_encountered = True
                                        break
                                if error_encountered:
                                    continue
                            params[selected_nn_number][1][param_key] = user_input
                        else:
                            print("Chyba ve skryté vrstvě, napište to znovu")
                            continue
                    case 3:  # input mask
                        if user_input in ["t", "true"]:
                            params[selected_nn_number][1][param_key] = True
                        elif user_input in ["f", "false"]:
                            params[selected_nn_number][1][param_key] = False
                        else:
                            print("Chyba v hodnotě vstupní masky, napište to znovu")
                            continue
                    case 4:  # gamma
                        try:
                            float_number = float(user_input)
                            if not (1. >= float_number >= 0.):
                                raise ValueError
                        except (ValueError, TypeError):
                            print("Chyba v hodnotě gama, napište to znovu")
                            continue
                        params[selected_nn_number][1][param_key] = float_number
                    case 5:  # epsilon: start, end, step
                        epsilon_parts = user_input.replace(" ", "").split(",")
                        if len(epsilon_parts) != 3:
                            print("Chyba v hodnotách epsilon, napište to znovu")
                            continue
                        epsilons = []
                        error_flag = False
                        for epsilon_part in epsilon_parts:
                            try:
                                epsilon = float(epsilon_part)
                                if not (1. >= epsilon >= 0.):
                                    raise ValueError
                            except (ValueError, TypeError):
                                print("Chyba v hodnotách epsilon, napište to znovu")
                                error_flag = True
                                break
                            epsilons.append(epsilon)
                        if error_flag:
                            continue
                        if epsilons[0] < epsilons[1]:
                            print("Chyba v hodnotách epsilon, napište to znovu")
                            continue
                        params[selected_nn_number][1][param_key] = f"[{user_input.replace(' ', '')}]"
                    case 6:  # optimizer type: https://keras.io/api/optimizers/
                        if user_input not in [opt.lower() for opt in self.optimizers]:
                            print("Chyba v typu optimizéru")
                            print("Zvolte jednu z možností:", ", ".join(
                                [option for option in self.optimizers if
                                 option.lower().startswith(user_input.lower())]))
                            continue
                        params[selected_nn_number][1][param_key] = user_input
                    case 7:  # learning rate
                        try:
                            float_number = float(user_input)
                            if not (1. >= float_number >= 0.):
                                raise ValueError
                        except (ValueError, TypeError):
                            print("Chyba v hodnotě rychlosti učení, napište to znovu")
                            continue
                        params[selected_nn_number][1][param_key] = float_number
                    case 8:  # loss function type: https://keras.io/api/losses/
                        if user_input not in [opt.lower() for opt in self.losses]:
                            print("Chyba v typu ztrátové funkce")
                            print("Zvolte jednu z možností:", ", ".join(
                                [option for option in self.losses if option.lower().startswith(user_input.lower())]))
                            continue
                        params[selected_nn_number][1][param_key] = user_input
                    case 9:  # metric type: https://keras.io/api/metrics/
                        if user_input not in [opt.lower() for opt in self.metrics]:
                            print("Chyba v typu metriky")
                            print("Zvolte jednu z možností:", ", ".join(
                                [option for option in self.metrics if option.lower().startswith(user_input.lower())]))
                            continue
                        params[selected_nn_number][1][param_key] = user_input
                    case 10:  # epochs
                        try:
                            float_number = float(user_input)
                            if not (int(float_number) >= 1.):
                                raise ValueError
                        except (ValueError, TypeError):
                            print("Chyba v hodnotě epochy, napište to znovu")
                            continue
                        params[selected_nn_number][1][param_key] = int(float_number)
                    case 11:  # batch size
                        try:
                            float_number = float(user_input)
                            if not (int(float_number) >= 1.):
                                raise ValueError
                        except (ValueError, TypeError):
                            print("Chyba v hodnotě velikosti dávky, napište to znovu")
                            continue
                        params[selected_nn_number][1][param_key] = int(float_number)
                    case 12:  # notes
                        regex = rf'^[\w\s,.:-]{{1,{max_length * 4}}}$'
                        if re.match(regex, user_input):
                            params[selected_nn_number][1][param_key] = user_input
                        else:
                            print("Chyba v poznámce, napište to znovu")
                            continue
                break

            if break_flag:
                break
        print(f"\nZměněné parametry NN:\n{params[selected_nn_number][1]}\n")

        # Find the index of the row you want to overwrite based on the primary key
        index_to_replace = df[df[self.primary_key] == params[selected_nn_number][1][self.primary_key]].index[0]

        # Modify the desired record in the DataFrame
        df.loc[index_to_replace] = params[selected_nn_number][1].to_dict()

        # Write the modified DataFrame back to the CSV file
        df.to_csv(self.data_file_name_parameters, index=False)

        new_model = tf.keras.models.clone_model(model)
        if old_nn_hidden_layers != params[selected_nn_number][1]["NN hidden layers"]:
            # Creating a new Sequential model if the number of hidden layers has changed
            # noinspection PyUnresolvedReferences
            new_model = tf.keras.Sequential()

            # Adding the input layer
            new_model.add(tf.keras.layers.Input(shape=(160,)))

            # Adding hidden layers
            hidden_layers = params[selected_nn_number][1]['NN hidden layers']

            # Parsing the hidden layers parameter
            pattern = r'\[(\d+),([^,\[\]]+),(0(?:\.\d+)?)\]'
            hidden_layers_list = ast.literal_eval(re.sub(pattern, r'[\1,"\2",\3]', hidden_layers))

            # https://keras.io/api/layers/initializers  kernel_initializer: random_normal, random_uniform, zeros, etc.
            # Adding dense layers with specified size, activation and dropout
            for idx, layer_params in enumerate(hidden_layers_list):
                size, activation, dropout = layer_params
                new_model.add(tf.keras.layers.Dense(size, activation=activation))
                if dropout:
                    new_model.add(tf.keras.layers.Dropout(dropout))

            # Adding the output layer
            new_model.add(tf.keras.layers.Dense(44, activation='linear'))

        optimizer_type = params[selected_nn_number][1]['optimizer type']
        learning_rate = params[selected_nn_number][1]['learning rate']
        loss_type = params[selected_nn_number][1]['loss function type']
        metrics_type = params[selected_nn_number][1]['metric type']

        # Find the corresponding full name of the optimizer
        full_optimizer_name = None
        for optimizer in self.optimizers:
            if optimizer.lower() == optimizer_type:
                full_optimizer_name = optimizer
                break

        optimizer = getattr(tf.keras.optimizers, full_optimizer_name)(learning_rate=learning_rate)
        new_model.compile(optimizer=optimizer, loss=loss_type, metrics=[metrics_type])

        if old_nn_hidden_layers == params[selected_nn_number][1]["NN hidden layers"]:
            new_model.set_weights(model.get_weights())

        # Saving the TF model to a file
        new_model.save(selected_nn_path)
        print(f"Model uložen zde: {selected_nn_path}") if DEBUG_PRINT else None

    def show_database(self) -> None:
        """
        Shows the neural network and its parameters.

        :return: None
        """
        neuron_networks_df = list()
        for data_file_name in [self.data_file_name_parameters, self.data_file_name_training,
                               self.data_file_name_testing]:
            neuron_networks_df.append(pd.read_csv(data_file_name))

        neuron_networks_df[1] = neuron_networks_df[1].drop(columns=self.primary_key).rename(
            columns=lambda x: f"{x} - train")
        neuron_networks_df[2] = neuron_networks_df[2].drop(columns=self.primary_key).rename(
            columns=lambda x: f"{x} - test")

        # Merging data using pd.concat()
        merged_data_df = pd.concat(neuron_networks_df, axis=1)

        print("Ukázka databáze")
        # Displaying merged data
        show(merged_data_df)

        train_episodes = neuron_networks_df[1]['number of episodes - train']
        neuron_networks_df[1]['time/episode - train'] = neuron_networks_df[1]['sum time - train'] / train_episodes
        neuron_networks_df[1]['sum of ranks/episodes - train'] = (neuron_networks_df[1]['sum of ranks - train'] /
                                                                  train_episodes)
        neuron_networks_df[1]['number of hits/episodes - train'] = (neuron_networks_df[1]['number of hits - train'] /
                                                                    train_episodes)
        neuron_networks_df[1]['my score/episodes - train'] = (neuron_networks_df[1]['my score - train'] /
                                                              train_episodes)
        neuron_networks_df[1]['movements/episodes - train'] = (neuron_networks_df[1]['number of movements - train'] /
                                                               train_episodes)
        neuron_networks_df[1]['loss/episodes - train'] = (neuron_networks_df[1]['sum loss - train'] /
                                                          train_episodes)
        neuron_networks_df[1]['accuracy/episodes - train'] = (neuron_networks_df[1]['sum accuracy - train'] /
                                                              train_episodes)

        test_episodes = neuron_networks_df[2]['number of episodes - test']
        neuron_networks_df[2]['time/episode - test'] = neuron_networks_df[2]['sum time - test'] / test_episodes
        neuron_networks_df[2]['sum of ranks/episodes - test'] = (neuron_networks_df[2]['sum of ranks - test'] /
                                                                 test_episodes)
        neuron_networks_df[2]['number of hits/episodes - test'] = (neuron_networks_df[2]['number of hits - test'] /
                                                                   test_episodes)
        neuron_networks_df[2]['my score/episodes - test'] = (neuron_networks_df[2]['my score - test'] /
                                                             test_episodes)
        neuron_networks_df[2]['movements/episodes - test'] = (neuron_networks_df[2]['number of movements - test'] /
                                                              test_episodes)

        # Merge data using pd.concat()
        merged_data_df = pd.concat(neuron_networks_df, axis=1)

        # Define columns to drop
        columns_to_drop = ['NN name', 'NN hidden layers', 'input mask', 'gamma', 'epsilon', 'optimizer type',
                           'learning rate', 'loss function type', 'metric type', 'epochs', 'batch size',
                           'action frequency - train', 'action frequency - test']
        # Drop specified columns
        merged_data_df = merged_data_df.drop(columns=columns_to_drop)

        print("Ukázka vybraných dat")
        # Display selected data
        show(merged_data_df)

    def delete_nn(self) -> None:
        """
        Deletes the neural network.

        :return: None
        """
        # Check if the primary keys match the neural network names without the '.keras' extension
        for nn_name in self.keras_model_files:
            nn_primary_key = nn_name[:-6]  # Remove the '.keras' extension
            for file_path in [self.data_file_name_parameters, self.data_file_name_training,
                              self.data_file_name_testing]:
                df = pd.read_csv(file_path)  # Load CSV file into DataFrame
                if nn_primary_key not in df['NN name'].str.strip().values:
                    print(f"Varování: Primární klíč '{nn_primary_key}' nenalezen v {file_path}.")

        # Load data from self.data_file_name_parameters
        df = pd.read_csv(self.data_file_name_parameters)

        # Create a selection of neural networks with their nickname, date, and notes
        options = []
        for index, row in df.iterrows():
            option = f"{row['NN nickname']} - {row['NN name']} ({row['notes']})"
            options.append(option)

        # Add help and quit options to the end of the selection
        options.extend(["Nápověda (h)", "Konec programu (k)"])

        selected_nn_number: int = 0
        while True:
            # Printing options
            print("Možnosti:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")

            # Getting user input
            user_input = input("\nVyberte neuronovou síť:").lower()

            # Processing user input
            if user_input in self.utils.help_list or user_input == str(len(options) - 1):
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list or user_input == str(len(options)):
                print("Program byl úspěšně ukončen.")
                exit(0)

            try:
                selected_nn_number = int(user_input) - 1
                selected_option = options[selected_nn_number]
                print(f"Vybraná neuronová síť: {selected_option}")
            except (ValueError, IndexError):
                print("Neplatná volba. Zadejte číslo možnosti nebo 'help' pro nápovědu, 'k' pro ukončení.")
                continue

            if selected_nn_number + 1 > len(options) or selected_nn_number + 1 < 1:
                print("Zadané číslo je mimo rozsah možností.")
                continue
            break

        params: list = [elem for elem in df.iterrows()]

        # Getting the primary key of the selected neural network
        selected_nn_name = params[selected_nn_number][1]['NN name']

        # Loop for iterating through all CSV databases
        for file_path in [self.data_file_name_parameters, self.data_file_name_training, self.data_file_name_testing]:
            # Loading CSV file into DataFrame
            df = pd.read_csv(file_path)

            # Checking if the primary key of the selected neural network exists in the given CSV database
            if selected_nn_name in df['NN name'].str.strip().values:
                # Removing the row with the selected neural network from the DataFrame
                df = df[df['NN name'].str.strip() != selected_nn_name]

                # Writing the modified DataFrame back to the CSV file
                df.to_csv(file_path, index=False)
                print(f"Neuronová síť {selected_nn_name} byla úspěšně odstraněna z {file_path}.")
            else:
                print(f"Varování: Primární klíč '{selected_nn_name}' nebyl nalezen v {file_path}.")

        selected_nn_path: str = self.models_folder + params[selected_nn_number][1]['NN name'] + '.keras'

        # Checking if the file exists before deleting it
        if os.path.exists(selected_nn_path):
            os.remove(selected_nn_path)
            print(f"Model {selected_nn_path} byl úspěšně smazán.")
        else:
            print(f"Soubor {selected_nn_path} neexistuje.")

    def start(self) -> None:
        """
         Start the user interface.
        :return: None
        """
        # initialize etc.
        self.initialize()

        # main UI loop
        while True:
            # Check if neural network models exist
            nn_exist: bool = self.check_nn_models()

            if not nn_exist:
                # Options for when no neural network models exist
                options: list[str] = ["Vytvoření NN"]
            else:
                # Options for when neural network models exist
                options: list[str] = ["Vytvoření NN", "Trénink NN", "Testování NN", "Kopie NN", "Úprava NN",
                                      "Ukázka databáze NN", "Vymazání NN"]

            # Add options for help and exiting
            options.extend(["Nápověda (h)", "Konec programu (k)"])

            print("Možnosti:")
            # Display available options
            for i, option in enumerate(options, start=1):
                print(f"{i}. {option}")

            # Prompt user for input
            user_input: str = input("\nVyberte možnost:").lower()
            print()

            # Conditions for providing help and quitting
            if user_input in self.utils.help_list or user_input == str(len(options) - 1):
                self.utils.pyhelp()
                continue
            if user_input in self.utils.end_list or user_input == str(len(options)):
                print("Program byl úspěšně ukončen.")
                exit(0)

            # Checking if the input is a number
            try:
                user_input_number: int = int(user_input)
            except (ValueError, TypeError):
                print("Chyba: Zadali jste neplatný vstup. Zadejte prosím číslo.")
                continue

            if user_input_number > len(options) or user_input_number < 1:
                print("Zadané číslo je mimo rozsah možností.")
                continue

            match user_input_number:
                case 1:
                    # Create neural network
                    self.create_nn()
                case 2:
                    # Train neural network
                    self.training_nn()
                case 3:
                    # Test neural network
                    self.testing_nn()
                case 4:
                    # Copy neural network
                    self.copy_nn()
                case 5:
                    # Modify neural network
                    self.change_nn()
                case 6:
                    # Show database
                    self.show_database()
                case 7:
                    # Delete neural network
                    self.delete_nn()
                case _:
                    print("Chyba: Zadali jste neplatnou možnost.")
                    continue


class RobocodeRunner:
    """
    The RobocodeRunner class handles the execution of Robocode battles and processing of the results.
    """
    # This command needs to be adjusted according to your development environment. You need to run Robocode in IntelliJ
    # (Eclipse) and add its call to this command.
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
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    java_program_directory: str = current_dir + r"\RoboCode"

    @property
    def start(self) -> tuple[int, int, int, int, float, list[str]]:
        """
            Start the Robocode battle and process the results.

            :return: A tuple containing the order of the user's tank, user's score, the best score in the battle,
                     the worst score in the battle, the average score of all tanks, and the list of tank names.
            """
        # Set the working directory to the directory containing the Java program
        os.chdir(self.java_program_directory)

        process = None
        try:
            # Run the command and capture the output and error output
            process: Optional[subprocess.Popen] = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                                                                   stderr=subprocess.PIPE, universal_newlines=True)

            # Retrieving standard output and standard error output.
            stdout, stderr = process.communicate()
        finally:
            # Clean up resources
            if process:
                # Close the standard output and standard error streams
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
                # Wait for the process to finish and retrieve the exit status
                process.wait()
        print("stdout:\n", stdout, "\nstderr:\n", stderr) if DEBUG_PRINT else None

        # Process the error output
        err_lines: list[str] = stderr.split('\n')
        for err_line in err_lines:
            if not err_line.strip():
                # skips empty lines
                continue
            if not err_line.startswith('WARNING: '):
                print("Chyba v textu:")
                print(err_line)
                continue

        # If the entire text passes through, it means that all lines start with "WARNING: "
        print("V stderr vše v pořádku, pokračujeme.") if DEBUG_PRINT else None

        # Find text between "-- Battle results --" and the end of the text
        # noinspection RegExpAnonymousGroup
        match: Optional[Match[str]] = re.search(r'-- Battle results --\s+(.*)', stdout, re.DOTALL)

        my_score: int = 0
        best_score: int = 0
        worst_score: int = 2 ** 31 - 1
        total_scores: list[int] = []
        average_score: float = 0.0
        my_tank_order: int = 0
        tank_names: list[str] = []

        if match:
            results_text: str = match.group(1)

            # Extract tank names and scores using regular expression
            # noinspection RegExpAnonymousGroup
            tank_results: list[str] = re.findall(r"(\w+(?:\.\w+)?(?:\s\(?\w+\)?)?)\s*:\s+(\d+)", results_text)[:-1]
            print("Výsledky tanků:", tank_results, results_text) if DEBUG_PRINT else None
            if tank_results:
                for idx, (tank, score) in enumerate(tank_results):
                    tank: str = tank.removeprefix('sample.')
                    tank_names.append(tank)  # Adding tank name to the list
                    score_int = int(score)
                    total_scores.append(score_int)
                    if tank == 'PyRobotClient':
                        my_score: int = score_int
                        my_tank_order: int = idx + 1  # Tank order

                    if score_int > best_score:  # Updating the best score
                        best_score: int = score_int
                    if score_int < worst_score:  # Updating the worst score
                        worst_score: int = score_int

                    average_score: float = sum(total_scores) / len(total_scores)

                    if idx < len(tank_results) - 1:
                        print(f"{tank}: {score_int}", end=",        ")
                    else:
                        print(f"{tank}: {score_int}")
                    if (idx + 1) % 4 == 0 and idx + 1 != len(tank_results):
                        print()
            else:
                print("Nenalezena žádná data o výsledcích tanků.")
        else:
            print("Nenalezena část textu s výsledky.")

        os.chdir(self.current_dir)
        return my_tank_order, my_score, best_score, worst_score, average_score, tank_names


class NaNCallback(Callback):
    """
    A callback that stops training if NaN (not a number) values are encountered during training.
    """

    def on_epoch_end(self, epoch, logs=None) -> None:
        """
        Method called at the end of each epoch.

        :param epoch: Integer, index of epoch.
        :param logs: Dictionary, contains the loss value and all the metrics at the end of the epoch.
        :return: None
        """
        values = np.array(list(logs.values()))
        if np.isnan(values).any():
            self.model.stop_training = True
            print("Training stopped due to NaN values.")


if __name__ == '__main__':
    # Utils tools like welcome text, help and handle keyboard interrupt
    utils_tool = Utils()

    # Sets up a keyboard interrupt signal handler
    signal.signal(signal.SIGINT, utils_tool.handle_keyboard_interrupt)

    # User Interface
    UI = UserInterface(utils_tool)
    UI.start()
