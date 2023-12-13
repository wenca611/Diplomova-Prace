package cz.vutbr.feec.robocode.battle;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.Properties;

import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

import cz.vutbr.feec.robocode.socket.SocketsHolder;
import cz.vutbr.feec.robocode.socket.TCPClientSocket;
import net.sf.robocode.io.RobocodeProperties;
import robocode.BattleResults;
import robocode.control.BattleSpecification;
import robocode.control.BattlefieldSpecification;
import robocode.control.RobocodeEngine;
import robocode.control.RobotSpecification;

public class RobocodeRunner {

	public static void main(String[] args) throws IOException {
		long start = System.currentTimeMillis();

		System.setProperty("NOSECURITY", "true");
		System.out.println("SECURITY OFF: " + RobocodeProperties.isSecurityOff());
		//System.out.println("NOSECURITY "+System.getProperty("NOSECURITY", "false").equals("true"));

		Properties prop = new Properties();
		try {
			prop.load(new FileInputStream("config/game.properties"));
		} catch (IOException e) {
			e.printStackTrace();
		}

		int numOfPlayers = Integer.parseInt(prop.getProperty("numOfPlayers", "0"));
		int numberOfRounds = Integer.parseInt(prop.getProperty("numberOfRounds", "10"));
		int gameWidth = Integer.parseInt(prop.getProperty("gameWidth", "800"));
		int gameHeight = Integer.parseInt(prop.getProperty("gameHeight", "600"));
		boolean isVisible = Boolean.parseBoolean(prop.getProperty("isVisible", "true"));
//		----------------------------------SETTING UP AUTONOMOUS OPPONENTS-------------------------------
    	/*
    	"Corners, Crazy, Fire, Interactive, Interactive_v2, " +
		"MyFirstJuniorRobot, MyFirstRobot, PaintingRobot, RamFire, SittingDuck, " +
		"SpinBot, Target, Tracker, TrackFire, VelociRobot, Walls, PyRobotClient";
		*/
//		------------------------------------------------------------------------------------------------
		String listOfEnemies = prop.getProperty("listOfEnemies", "Crazy, Tracker, PyRobotClient");

		SocketsHolder socketsHolder = new SocketsHolder();

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

		runRobocode(numOfPlayers, listOfEnemies, numberOfRounds, gameWidth, gameHeight, isVisible);

		// Výpočet trvání v milisekundách
		long duration = System.currentTimeMillis() - start;

		// Výpis trvání
		System.out.println("Čas běhu kódu: " + (int) (duration/1000) + " s");

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
}