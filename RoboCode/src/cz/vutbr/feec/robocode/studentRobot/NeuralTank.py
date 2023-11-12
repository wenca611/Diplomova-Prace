import logging

# Konfigurace logování
logging.basicConfig(filename='error.log', level=logging.ERROR)

try:
    import onnxruntime
    print("onnxruntime bylo úspěšně naimportováno.")
except ImportError as e:
    print("Chyba při importu onnxruntime:", str(e))
    logging.error("Chyba při importu onnxruntime: %s", str(e))

import socket
import sys
import time
import random
import os
import numpy as np

# i am here: RoboCodeProject\RoboCode\src\cz\vutbr\feec\robocode\studentRobot

def generate_random_input(batch_size=1, input_size=160):
    # Generátor náhodných čísel v rozmezí -1 až 1
    random_data = np.random.uniform(low=-1, high=1, size=(batch_size, input_size))
    return random_data.astype(np.float32)  # Převod na float32

# Získání aktuální pracovní složky
current_working_directory = os.path.abspath(os.path.dirname(__file__))

# Získání cesty do složky NeuralNetworkModels
neural_network_models_folder = os.path.abspath(
    os.path.join(current_working_directory, '..', '..', '..', '..', '..', '..', 'NeuralNetworkModels'))

# Vypsání získaných cest
#logging.error(f"Aktuální pracovní složka: {current_working_directory}")
#logging.error(f"Cesta do složky NeuralNetworkModels: {neural_network_models_folder}")
onnx_model_path = neural_network_models_folder + '/my_model.onnx'

# Kontrola existence cesty
if not os.path.exists(onnx_model_path):
    error_message = f"Cesta '{onnx_model_path}' neexistuje. Program bude ukončen."
    logging.error(error_message)
    current_path = os.path.abspath(os.path.dirname(__file__))
    logging.error(f"Aktuální pracovní složka: {current_path}")
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

while True:
    # Nastavíme socket na neblokující režim a nastavíme timeout na 1 sekundu
    s.settimeout(0.6)

    #------------------------získané STAVY do Neuronové sítě------------------------------------#
    try:
        received_data = s.recv(4096)  # Pokusíme se přijmout data ze socketu, 160n asi 1000+B
        if not received_data:
            # Data nebyla obdržena
            s.close()
            logging.error("no data")
            continue
    except socket.timeout:
        # Uplynulo 0.6 sekundy a data nebyla obdržena
        # logging.error("vypršel čas")  # good on end
        s.close()
        break

    # logging.error(received_data)


    # Dekódování bajtů na řetězec a odstranění \r\n na konci
    decoded_data = received_data.decode('utf-8').strip()

    # Rozdělení řetězce podle mezery a převedení na pole floatů
    float_array = np.array([[float(num) for num in decoded_data.split()]], dtype=np.float32)

    # Výsledek
    # logging.error("float data: " + str(float_array))
    # logging.error("délka: "+str(float_array.shape[1]))


    # Převedení vstupních dat do formátu, který akceptuje ONNX model
    #input_data = float_array.reshape(1, -1)
    # input_data = generate_random_input(batch_size=1, input_size=160)
    #logging.error("rand input:" + str(input_data))

    output_data = None
    try:
        # Inference (získání výstupu) z ONNX modelu
        output_data = onnx_session.run(None, {'input_name': float_array})
    except Exception as e:
        # Logování chyby
        logging.error("Chyba při inference ONNX modelu: %s", str(e))

    if output_data:
        action = output_data[0][0]
        # Pošlete ... do Javy s končícím znakem "\n"
        s.sendall((str(action) + "\n").encode())

# Uzavřeme socket
s.close()
