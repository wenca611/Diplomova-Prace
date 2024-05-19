package cz.vutbr.feec.robocode.battle;

import java.io.*;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.net.ServerSocket;

import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

import cz.vutbr.feec.robocode.socket.SocketsHolder;
import cz.vutbr.feec.robocode.socket.TCPClientSocket;
import net.sf.robocode.io.Logger;
import net.sf.robocode.io.RobocodeProperties;
import robocode.BattleResults;
import robocode.control.BattleSpecification;
import robocode.control.BattlefieldSpecification;
import robocode.control.RobocodeEngine;
import robocode.control.RobotSpecification;

public class RobocodeRunner {
	// Indicates whether the battle is for training purposes
	public static boolean isTrain = true;

	public static void main(String[] args) throws IOException {
		long start = System.currentTimeMillis();

		// Turn off Robocode's security
		System.setProperty("NOSECURITY", "true");
		System.out.println("SECURITY OFF: " + RobocodeProperties.isSecurityOff());
		//System.out.println("NOSECURITY "+System.getProperty("NOSECURITY", "false").equals("true"));

		// Load properties from the configuration file
		Properties prop = new Properties();
		try {
			prop.load(new FileInputStream("config/game.properties"));
		} catch (IOException e) {
			e.printStackTrace();
		}

		// Read configuration properties
		int numOfPlayers = Integer.parseInt(prop.getProperty("numOfPlayers", "0"));
		int numberOfRounds = Integer.parseInt(prop.getProperty("numberOfRounds", "10"));
		int gameWidth = Integer.parseInt(prop.getProperty("gameWidth", "800"));
		int gameHeight = Integer.parseInt(prop.getProperty("gameHeight", "600"));
		int trainingPort = Integer.parseInt(prop.getProperty("trainingPort", "0"));
		boolean isVisible = Boolean.parseBoolean(prop.getProperty("isVisible", "true"));
		String epsilon = prop.getProperty("epsilon", "0.0");
		String nnName = prop.getProperty("nnName", "");

		// Check if training port is set
		boolean isPortSet = true;
		if (trainingPort == 0) {
			isPortSet = false;
		}

//		----------------------------------SETTING UP AUTONOMOUS OPPONENTS-------------------------------
    	/*
    	"Corners, Crazy, Fire, Interactive, Interactive_v2, " +
		"MyFirstJuniorRobot, MyFirstRobot, PaintingRobot, RamFire, SittingDuck, " +
		"SpinBot, Target, Tracker, TrackFire, VelociRobot, Walls, PyRobotClient";
		*/
//		------------------------------------------------------------------------------------------------
		// List of enemies for the battle
		String listOfEnemies = prop.getProperty("listOfEnemies", "Crazy, Tracker, PyRobotClient");

		// Create a SocketsHolder instance
		SocketsHolder socketsHolder = new SocketsHolder();

		// Establish TCP connections for each player
		for (int i = 1; i <= numOfPlayers; i++) {
			int port = Integer.parseInt(prop.getProperty("robot." + i + ".port"));
			String ip = String.valueOf(prop.getProperty("robot." + i + ".ip"));

			//socketsHolder.addTCPClientToMap(port, new TCPClientSocket(ip, port));

			Thread thread = new Thread(() -> {
				try {
					socketsHolder.addTCPClientToMap(port, new TCPClientSocket(ip, port));
				} catch (IOException e) {
					throw new RuntimeException(e);
				}
			});

			thread.start();
		}

		// Read the content of the file into a list of lines
		List<String> lines = new ArrayList<>();
		try (BufferedReader reader = new BufferedReader(new FileReader("config/game.properties"))) {
			String line;
			while ((line = reader.readLine()) != null) {
				lines.add(line);
			}
		} catch (IOException e) {
			e.printStackTrace();
			return;
		}

		int freePort = findFreePort();  // Find a free port for training if needed
		// Update the training port line in the configuration file
		if (isPortSet) {
			for (int i = 0; i < lines.size(); i++) {
				String line = lines.get(i);
				if (line.startsWith("trainingPort")) {
					lines.set(i, "trainingPort=" + freePort);
					break;
				}
			}
		}

		// Write the updated lines back to the file
		try (BufferedWriter writer = new BufferedWriter(new FileWriter("config/game.properties"))) {
			for (String line : lines) {
				writer.write(line);
				writer.newLine();
			}
		} catch (IOException e) {
			e.printStackTrace();
		}

		Process pythonProcess = null;
		if (isTrain){
			// Turning on the Python agent on the specified server when the port is not zero, passing the port as a parameter
			if (isPortSet) {
				try {
					ServerSocket serverSocket = new ServerSocket(freePort);
					serverSocket.setSoTimeout(10000);

					String pythonPath = "src/cz/vutbr/feec/robocode/studentRobot/";
					String pythonScript = "RobotAI.py";
					String argument = Integer.toString(freePort); // port

					ProcessBuilder processBuilder = new ProcessBuilder("python", pythonPath+pythonScript,
							argument, epsilon, nnName);
					processBuilder.redirectOutput(ProcessBuilder.Redirect.DISCARD);
					processBuilder.redirectError(ProcessBuilder.Redirect.DISCARD);

					pythonProcess = processBuilder.start();
					Logger.logMessage("start python agenta pro trenovani");
					int MAX_MESSAGES = 3;
					int messageCount = 0;

					while (messageCount < MAX_MESSAGES) {
						Socket socket = serverSocket.accept();
						Logger.logMessage("Connection established with Python client.");

						try (BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
							PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {
							String message;
							while ((message = in.readLine()) != null) {
								Logger.logMessage("Received message from Python: " + message);
								messageCount++;

								// Sending acknowledgment message back to Python
								if (messageCount >= MAX_MESSAGES) {
									out.println("ACK");
									break; // If the maximum number of messages has been received, exit the loop
								}
							}
						} catch (Exception e) {
							e.printStackTrace();
						}
					}

					serverSocket.close();

				} catch (IOException e) {
					throw new RuntimeException(e);
				}
			}
		}

		runRobocode(numOfPlayers, listOfEnemies, numberOfRounds, gameWidth, gameHeight, isVisible);

		if (isTrain)
			if (isPortSet) {
                assert pythonProcess != null;
                pythonProcess.destroy();
				System.out.println("Python process terminován");
			}


		// Výpočet trvání v milisekundách
		long duration = System.currentTimeMillis() - start;

		// Výpis trvání
		System.out.println("Čas běhu arény: " + (int) (duration/1000) + " s");

		// Make sure that the Java VM is shut down properly
		System.exit(0);
	}

	public static void runRobocode(int numOfPlayers, String listOfEnemies, int numberOfRounds, int gameWidth,
								   int gameHeight, boolean isVisible) throws IOException {
		String nameOfRobotClassTCP = "RobotClient";
		// create src and dest path for compiling
		String src = "src/sample/" + nameOfRobotClassTCP + ".java";
		String dst = "robots/sample/" + nameOfRobotClassTCP + ".java";
		// compile our created robot and store it to robots/samples
		File source = new File(src);
		File dest = new File(dst);
		Files.copy(source.toPath(), dest.toPath(), StandardCopyOption.REPLACE_EXISTING);
		JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
		compiler.run(null, System.out, System.out, dst);

		// remove all whitespaces
		listOfEnemies = listOfEnemies.replaceAll("\\s", "");
		// create list of tanks to fight
		String tanks[] = listOfEnemies.split(",");
		String finalListOfTanks = "";
		for (String tankName : tanks) {
			tankName = "sample." + tankName + ",";
			finalListOfTanks += tankName;
		}

		// first player
		if (numOfPlayers > 0)
			finalListOfTanks += "sample." + nameOfRobotClassTCP;
		// next players
		for (int i = 1; i < numOfPlayers; i++) {
			finalListOfTanks += ",sample." + nameOfRobotClassTCP;
		}

		// Battle listener used for receiving battle events
		BattleObserver battleListener = new BattleObserver();

		// Create the RobocodeEngine
		RobocodeEngine engine = new RobocodeEngine(); // Run from current
		// working directory

		// Add battle listener to our RobocodeEngine
		engine.addBattleListener(battleListener);

		// Show the battles
		engine.setVisible(isVisible); // true

		// Setup the battle specification
		BattlefieldSpecification battlefield = new BattlefieldSpecification(gameWidth, gameHeight); // 800x600

		// engine.getLocalRepository("sample.Corners, sample.MujRobot");
		RobotSpecification[] selectedRobots = engine.getLocalRepository(finalListOfTanks);

		BattleSpecification battleSpec = new BattleSpecification(numberOfRounds, battlefield, selectedRobots); // 10
		// Run our specified battle and let it run till it's over

		// batle start
		engine.runBattle(battleSpec, true/* wait till the battle is over */);

		/*for (BattleResults result : battleListener.getResults()) {
			System.out.println(result.getTeamLeaderName() + " - " + result.getScore());
		}*/

		// Cleanup our RobocodeEngine
		engine.close();
	}

	public static int findFreePort() {
		int port;
		ServerSocket serverSocket = null;
		try {
			serverSocket = new ServerSocket(0); // Zero port causes the system to select a free port
			port = serverSocket.getLocalPort();
		} catch (IOException e) {
			throw new RuntimeException("Nepodařilo se najít volný port.");
		} finally {
			if (serverSocket != null) {
				try {
					serverSocket.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
		return port;
	}
}