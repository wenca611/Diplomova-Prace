import sys  # 0 ms
import socket  # 10 ms
import os  # 0 ms
import time  # 10 ms
import logging  # 19 ms

# import random  # avg = 2 ms, max = 10 ms

# Current directory: RoboCodeProject\RoboCode\src\cz\vutbr\feec\robocode\studentRobot

# Get the current working directory
current_working_directory = os.path.abspath(os.path.dirname(__file__))
# logging.basicConfig(filename='error.log', level=logging.DEBUG)
logging.basicConfig(filename='error.log', level=logging.ERROR)


class Timer:
    """
    Context manager class for measuring the execution time of a code block.
    """

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        :return: self
        """
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context related to this object.

        :param exc_type: Exception type, if an exception was raised
        :param exc_value: Exception value, if an exception was raised
        :param traceback: Traceback object, if an exception was raised
        :return: None
        """
        end_time: float = time.time()
        elapsed_time: float = end_time - self.start_time
        if exc_type is not None:
            logging.error("Výjimka: {}".format(exc_value))
        logging.error("Cas vykonani kodu: {:.6f} sekund".format(elapsed_time))


def main(port: int, epsilon: float, nnName: str) -> None:
    """
    Main function to connect to the server, load TensorFlow and NumPy, and establish a secondary connection.

    :param port: Port number to connect to the server.
    :param epsilon: Epsilon value for the neural network.
    :param nnName: Name of the neural network.
    :return: None
    """
    # logging.error("main, port: {0}, epsilon: {1}, nnName: {2}".format(port, epsilon, nnName))
    # Connect to the server port
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", port))
        client_socket.send("Connecting to the server...\n".encode())
    except Exception as e:
        return

    # Inform that we are attempting to load TensorFlow and NumPy
    client_socket.send("Attempting to load TensorFlow and NumPy...\n".encode())

    # Load TensorFlow and NumPy
    try:
        sys.path.append(os.path.abspath(os.path.join(
            current_working_directory, '..', '..', '..', '..', '..', '..', '..', 'venv', 'Lib', 'site-packages')))
        # logging.error("before tf")
        import tensorflow as tf  # avg = 3.4 s, max = 8.3 s
        # logging.error("after tf")
        tf.compat.v1.disable_eager_execution()
        import numpy as np  # avg = 90 ms, max = 150 ms
        client_socket.send("TensorFlow and NumPy loaded successfully.\n".encode())

        # Wait for the "ACK" message
        ack_received = False
        while not ack_received:
            ack_message = client_socket.recv(1024).decode()
            if ack_message.strip() == "ACK":
                ack_received = True

        # Close the existing communication after receiving "ACK"
        client_socket.close()

        # logging.error("end of first communication")

        # Establish a second connection and listen for new communication
        establish_second_connection(port, epsilon, nnName, tf, np)

    except Exception as e:
        client_socket.send("Error loading TensorFlow: {0}\n".format(e).encode())
        client_socket.close()
        logging.error("Error loading TensorFlow: {0}\n".format(e).encode())
        return


def establish_second_connection(port: int, epsilon: float, nnName: str, tf, np) -> None:
    """
    Establish a second connection to load the neural network model and listen for new communication.

    :param port: Port number to connect to the server.
    :param epsilon: Epsilon value for the neural network.
    :param nnName: Name of the neural network.
    :param tf: TensorFlow module.
    :param np: NumPy module.
    :return: None
    """
    neural_network_models_folder = os.path.abspath(
        os.path.join(current_working_directory, '..', '..', '..', '..', '..', '..', 'NNModels'))

    keras_model_path: str = neural_network_models_folder + '/' + nnName

    # Check if the model path exists
    if not os.path.exists(keras_model_path):
        error_message = f"Cesta '{keras_model_path}' neexistuje. Program bude ukončen."
        # logging.error(error_message)
        current_path = os.path.abspath(os.path.dirname(__file__))
        # logging.error(f"Current working directory: {current_path}")
        sys.exit(1)

    # logging.error("I am here1")

    # Connect to the same port and listen for new communication
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 0 ms
    server_socket.settimeout(30)  # 0 ms
    server_socket.bind(("localhost", port))  # 0 ms
    server_socket.listen()  # 0 ms

    model = tf.keras.models.load_model(keras_model_path, compile=False)  # 125 ms (with compile 160 ms)
    # time.sleep(2.5)

    # Accept connection from the client
    client_socket, address = server_socket.accept()  # 3.5 - 5 s
    client_socket.settimeout(0.5)  # 0 ms
    # logging.error("I am here 2")

    while True:  # 50 ms
        try:
            # ------------------------STATES for NN------------------------------------#
            # Attempt to receive data from the socket
            received_data = client_socket.recv(20000)  # Trying to receive data from the socket, 160 ~ 1000+B
            # logging.error(received_data.decode('utf-8').strip())
            if len(received_data) == 0:
                server_socket.close()
                client_socket.close()
                break
        except socket.timeout:
            # 0.5 seconds have passed and no data has been received
            # logging.error("socket.timeout")
            server_socket.close()
            client_socket.close()
            break
        except ConnectionRefusedError:
            # The server refused the connection
            logging.error("ConnectionRefusedError")
            break
        except OSError as e:
            # Other possible socket-related errors
            logging.error("OSError: " + str(e))
            break

        # Decoding bytes to a string and stripping \r\n at the end, 1 ms
        decoded_data = received_data.decode('utf-8').strip()

        # Splitting the string by spaces and converting to a float array
        float_array = np.array([[float(num) for num in decoded_data.split()]], dtype=np.float32)

        output_data = None

        # logging.error("Model architecture information:")
        # logging.error(f"Number of layers: {len(model.layers)}")
        # logging.error(f"Input shape: {model.input_shape}")
        # logging.error(f"Output shape: {model.output_shape}")
        # logging.error(f"float_array: {float_array}")

        # with Timer():
        try:  # 1 ms
            output_data = model.predict(float_array)
        except Exception as e:
            # Logging the error
            logging.error("Chyba pri spusteni modelu: %s", str(e))

        formatted_data = np.squeeze(output_data)
        # logging.error(f"formatted_data: {formatted_data}")

        # OUT DATA:
        # tank movement INT
        # tank rotation INT
        # firepower INT
        # gun movement INT

        if np.random.rand() < epsilon:
            formatted_data = np.random.uniform(-10, 10, 44)

        formatted_data = np.array2string(formatted_data, precision=6, separator=",")
        formatted_data = formatted_data.strip("[]").replace("\n", "").replace(" ", "")
        # logging.error("akce:" + formatted_data + "\n")

        # ------------------------ACTION from NN------------------------------------#
        if len(output_data):
            client_socket.send((formatted_data + "\n").encode())

        # logging.error("data poslana do Javy")

    # Close the socket
    client_socket.close()
    server_socket.close()


if __name__ == "__main__":
    port: int = int(sys.argv[1])  # Port passed as an argument when running the script
    epsilon: float = float(sys.argv[2])  # Epsilon value passed as an argument
    nnName: str = sys.argv[3]  # Neural network name passed as an argument
    main(port, epsilon, nnName)


# import logging  # 19 ms
# #import tensorflow
# import os
#
# # Konfigurace logování
# logging.basicConfig(filename='error.log', level=logging.ERROR)
#
# try:
#     import sys
#     sys.path.append(r"D:\FEKT\Ing\diplomka\RoboCodeProject\venv\Lib\site-packages")
#     import onnxruntime
#     #print("onnxruntime bylo úspěšně naimportováno.")
# except ImportError as e:
#     logging.error("Chyba při importu onnxruntime: %s", str(e))
#     logging.error(f"Aktuální pracovní složka: {os.path.abspath(os.path.dirname(__file__))}")
#
#
# import socket
# import sys
# # import time
# # import random
# import numpy as np
# """import keyboard
#
# up_down = 0.
# left_right = 0.
# gun_left_right = 0.
# fire = 0.
#
# # i am here: RoboCodeProject\RoboCode\src\cz\vutbr\feec\robocode\studentRobot
#
# keyboard_on = False
# keyboard_timeout = 25
#
# def generate_random_input(batch_size=1, input_size=160):
#     # Generátor náhodných čísel v rozmezí -1 až 1
#     random_data = np.random.uniform(low=-1, high=1, size=(batch_size, input_size))
#     return random_data.astype(np.float32)  # Převod na float32
#
# def on_key_event(e):
#     global up_down, left_right, gun_left_right, fire, keyboard_on
#     if e.event_type == keyboard.KEY_DOWN:
#         keyboard_on = True
#         if keyboard.is_pressed('up'):
#             up_down += 10.
#         if keyboard.is_pressed('down'):
#             up_down += -30.
#
#         if keyboard.is_pressed('left'):
#             left_right += -10.
#         if keyboard.is_pressed('right'):
#             left_right += 10.
#
#         if keyboard.is_pressed('a'):
#             gun_left_right += -2.
#         if keyboard.is_pressed('d'):
#             gun_left_right += 2.
#
#         if keyboard.is_pressed('q'):
#             fire = 1.
#         if keyboard.is_pressed('w'):
#             fire = 2.
#         if keyboard.is_pressed('e'):
#             fire = 3.
# """
#
# # Získání aktuální pracovní složky
# current_working_directory = os.path.abspath(os.path.dirname(__file__))
#
# # Získání cesty do složky NeuralNetworkModels
# neural_network_models_folder = os.path.abspath(
#     os.path.join(current_working_directory, '..', '..', '..', '..', '..', '..', 'NNModels'))
#
# # Vypsání získaných cest
# #logging.error(f"Aktuální pracovní složka: {current_working_directory}")
# #logging.error(f"Cesta do složky NeuralNetworkModels: {neural_network_models_folder}")
# onnx_model_path = neural_network_models_folder + '/my_model.onnx'
#
# # Kontrola existence cesty
# if not os.path.exists(onnx_model_path):
#     error_message = f"Cesta '{onnx_model_path}' neexistuje. Program bude ukončen."
#     #ing.error(error_message)
#     current_path = os.path.abspath(os.path.dirname(__file__))
#     #logging.error(f"Aktuální pracovní složka: {current_path}")
#     sys.exit(1)
#
# # Inicializace ONNX Runtime session
# onnx_session = onnxruntime.InferenceSession(onnx_model_path)
#
# # Zkontrolujte, zda byl poskytnut právě jeden argument
# if len(sys.argv) != 2:
#     print("Použití: python script.py <port>")
#     sys.exit(1)
#
# # Získání portu z argumentu
# port = sys.argv[1]
#
# # Zkontrolujte, zda je port platným číslem
# try:
#     port = int(port)
# except ValueError:
#     print("Zadaný port není platné číslo.")
#     sys.exit(1)
#
# # Vytvořte socket a připojte se k localhostu na zadaném portu
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
# try:
#     s.connect(("localhost", port))
# except ConnectionRefusedError:
#     print("Nepodařilo se připojit k localhostu na portu", port)
#     exit(1)
#
#
# bad_data_counter = 0
# while True:
#     # Nastavíme socket na neblokující režim a nastavíme timeout na 1 sekundu
#     s.settimeout(0.8)
#
#
#     #------------------------získané STAVY do Neuronové sítě------------------------------------#
#     try:
#         received_data = s.recv(6000)  # Pokusíme se přijmout data ze socketu, 160n asi 1000+B
#         if not received_data:
#             # Data nebyla obdržena
#             if bad_data_counter == 300:
#                 s.close()
#                 break
#             else:
#                 bad_data_counter += 1
#                 continue
#     except socket.timeout:
#         # Uplynulo 0.6 sekundy a data nebyla obdržena
#         # logging.error("vypršel čas")  # good on end
#         s.close()
#         break
#
#     # logging.error(received_data[:100])
#
#     # Dekódování bajtů na řetězec a odstranění \r\n na konci
#     decoded_data = received_data.decode('utf-8').strip()
#
#     # Rozdělení řetězce podle mezery a převedení na pole floatů
#     float_array = np.array([[float(num) for num in decoded_data.split()]], dtype=np.float32)
#
#     """if np.any(np.isinf(float_array)) or np.any(np.isnan(float_array)):
#         logging.error("inf or nan float stav:")
#     else:
#         pass  # logging.error("vse ciselne je ok")"""
#
#     output_data = None
#
#     try:
#         # Inference (získání výstupu) z ONNX modelu
#         output_data = onnx_session.run(None, {'input_name': float_array})
#     except Exception as e:
#         # Logování chyby
#         pass
#         # logging.error("Chyba při inference ONNX modelu: %s", str(e))
#
#     formatted_data = np.squeeze(output_data)
#     epsilon = 0.0
#     # OUT DATA:
#     #pohyb tanku INT
#     #otočení tanku INT
#     #síla střely INT
#     #pohyb dělem INT
#
#     if np.random.rand() < epsilon:
#         formatted_data = np.random.uniform(-10, 10, 44)
#
#     # logging.error(formatted_data)
#     """if keyboard_on:
#         for i in range(4):
#             formatted_data[i] = 0.
#
#     if keyboard_timeout > 0:
#         keyboard_timeout -= 1
#     else:
#         keyboard_on = False
#         keyboard_timeout = 100
#
#     # Nastavení hooku pro klávesnici
#     keyboard.hook(on_key_event)
#     if up_down != 0.:
#         formatted_data[0] = up_down
#
#     if left_right != 0.:
#         formatted_data[1] = left_right
#
#     if gun_left_right != 0.:
#         formatted_data[2] = gun_left_right
#
#     if fire != 0.:
#         formatted_data[3] = fire"""
#
#     #up_down = left_right = gun_left_right = fire = 0.
#
#     # keyboard.unhook_all()
#     formatted_data = np.array2string(formatted_data, precision=6, separator=",")
#     formatted_data = formatted_data.strip("[]").replace("\n", "").replace(" ", "")
#     # logging.error("akce:" + str(formatted_data))
#
#     # ------------------------AKCE z Neuronové sítě------------------------------------#
#     if output_data:
#         # Pošlete ... do Javy s končícím znakem "\n"
#         s.sendall((formatted_data + "\n").encode())
#
# # Uzavřeme socket
# s.close()
