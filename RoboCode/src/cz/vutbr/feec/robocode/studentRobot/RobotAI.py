import logging
#import tensorflow
import site
import os

# Konfigurace logování
logging.basicConfig(filename='error.log', level=logging.ERROR)

try:
    site.addsitedir(r'D:\FEKT\Ing\diplomka\RoboCodeProject\venv')
    import onnxruntime
    #print("onnxruntime bylo úspěšně naimportováno.")
except ImportError as e:
    logging.error("Chyba při importu onnxruntime: %s", str(e))


import socket
import sys
# import time
# import random
import numpy as np
"""import keyboard

up_down = 0.
left_right = 0.
gun_left_right = 0.
fire = 0.

# i am here: RoboCodeProject\RoboCode\src\cz\vutbr\feec\robocode\studentRobot

keyboard_on = False
keyboard_timeout = 25

def generate_random_input(batch_size=1, input_size=160):
    # Generátor náhodných čísel v rozmezí -1 až 1
    random_data = np.random.uniform(low=-1, high=1, size=(batch_size, input_size))
    return random_data.astype(np.float32)  # Převod na float32

def on_key_event(e):
    global up_down, left_right, gun_left_right, fire, keyboard_on
    if e.event_type == keyboard.KEY_DOWN:
        keyboard_on = True
        if keyboard.is_pressed('up'):
            up_down += 10.
        if keyboard.is_pressed('down'):
            up_down += -30.

        if keyboard.is_pressed('left'):
            left_right += -10.
        if keyboard.is_pressed('right'):
            left_right += 10.

        if keyboard.is_pressed('a'):
            gun_left_right += -2.
        if keyboard.is_pressed('d'):
            gun_left_right += 2.

        if keyboard.is_pressed('q'):
            fire = 1.
        if keyboard.is_pressed('w'):
            fire = 2.
        if keyboard.is_pressed('e'):
            fire = 3.
"""

# Získání aktuální pracovní složky
current_working_directory = os.path.abspath(os.path.dirname(__file__))

# Získání cesty do složky NeuralNetworkModels
neural_network_models_folder = os.path.abspath(
    os.path.join(current_working_directory, '..', '..', '..', '..', '..', '..', 'NNModels'))

# Vypsání získaných cest
#logging.error(f"Aktuální pracovní složka: {current_working_directory}")
#logging.error(f"Cesta do složky NeuralNetworkModels: {neural_network_models_folder}")
onnx_model_path = neural_network_models_folder + '/my_model.onnx'

# Kontrola existence cesty
if not os.path.exists(onnx_model_path):
    error_message = f"Cesta '{onnx_model_path}' neexistuje. Program bude ukončen."
    #ing.error(error_message)
    current_path = os.path.abspath(os.path.dirname(__file__))
    #logging.error(f"Aktuální pracovní složka: {current_path}")
    sys.exit(1)

# Inicializace ONNX Runtime session
onnx_session = onnxruntime.InferenceSession(onnx_model_path)

# Zkontrolujte, zda byl poskytnut právě jeden argument
if len(sys.argv) != 2:
    print("Použití: python script.py <port>")
    sys.exit(1)

# Získání portu z argumentu
port = sys.argv[1]

# Zkontrolujte, zda je port platným číslem
try:
    port = int(port)
except ValueError:
    print("Zadaný port není platné číslo.")
    sys.exit(1)

# Vytvořte socket a připojte se k localhostu na zadaném portu
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect(("localhost", port))
except ConnectionRefusedError:
    print("Nepodařilo se připojit k localhostu na portu", port)
    exit(1)


bad_data_counter = 0
while True:
    # Nastavíme socket na neblokující režim a nastavíme timeout na 1 sekundu
    s.settimeout(0.5)


    #------------------------získané STAVY do Neuronové sítě------------------------------------#
    try:
        received_data = s.recv(5000)  # Pokusíme se přijmout data ze socketu, 160n asi 1000+B
        if not received_data:
            # Data nebyla obdržena
            if bad_data_counter == 200:
                s.close()
                break
            else:
                bad_data_counter += 1
                continue
    except socket.timeout:
        # Uplynulo 0.6 sekundy a data nebyla obdržena
        # logging.error("vypršel čas")  # good on end
        s.close()
        break

    #logging.error(received_data[:100])

    # Dekódování bajtů na řetězec a odstranění \r\n na konci
    decoded_data = received_data.decode('utf-8').strip()

    # Rozdělení řetězce podle mezery a převedení na pole floatů
    float_array = np.array([[float(num) for num in decoded_data.split()]], dtype=np.float32)

    """if np.any(np.isinf(float_array)) or np.any(np.isnan(float_array)):
        logging.error("inf or nan float stav:")
    else:
        pass  # logging.error("vse ciselne je ok")"""

    output_data = None

    try:
        # Inference (získání výstupu) z ONNX modelu
        output_data = onnx_session.run(None, {'input_name': float_array})
    except Exception as e:
        # Logování chyby
        pass
        # logging.error("Chyba při inference ONNX modelu: %s", str(e))

    formatted_data = np.squeeze(output_data)
    epsilon = 0.1
    if np.random.rand() < epsilon:
        formatted_data = np.random.uniform(-10, 10, 4)

    # logging.error(formatted_data)
    """if keyboard_on:
        for i in range(4):
            formatted_data[i] = 0.

    if keyboard_timeout > 0:
        keyboard_timeout -= 1
    else:
        keyboard_on = False
        keyboard_timeout = 100

    # Nastavení hooku pro klávesnici
    keyboard.hook(on_key_event)
    if up_down != 0.:
        formatted_data[0] = up_down

    if left_right != 0.:
        formatted_data[1] = left_right

    if gun_left_right != 0.:
        formatted_data[2] = gun_left_right

    if fire != 0.:
        formatted_data[3] = fire"""

    up_down = left_right = gun_left_right = fire = 0.

    # keyboard.unhook_all()
    formatted_data = np.array2string(formatted_data, precision=8)
    formatted_data = formatted_data.strip("[]")
    # logging.error("akce:" + str(formatted_data))

    # ------------------------AKCE z Neuronové sítě------------------------------------#
    if output_data:
        # Pošlete ... do Javy s končícím znakem "\n"
        s.sendall((formatted_data + "\n").encode())

# Uzavřeme socket
s.close()
