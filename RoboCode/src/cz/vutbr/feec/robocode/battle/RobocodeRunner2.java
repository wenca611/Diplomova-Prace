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

public class RobocodeRunner2 {

	public static void main(String[] args) throws IOException {
		System.setProperty("NOSECURITY", "true");
		System.out.println("SECURITY OFF: " + RobocodeProperties.isSecurityOff());
		//System.out.println("NOSECURITY "+System.getProperty("NOSECURITY", "false").equals("true"));

		Properties prop = new Properties();
		try {
			prop.load(new FileInputStream("config/game.properties"));
		} catch (IOException e) {
			e.printStackTrace();
		}

		int pocetRobotu = Integer.parseInt(prop.getProperty("numOfPlayers"));

//		----------------------NASTAVENÍ AUTONOMNÍCH PROTIVNÍKŮ----------------------

		String seznamProtivniku = "PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient, PyRobotClient";
    	/*""Corners, Crazy, Fire, Interactive, Interactive_v2, " +
				"MyFirstJuniorRobot, MyFirstRobot, PaintingRobot, RamFire, SittingDuck, " +
				"SpinBot, Target, Tracker, TrackFire, VelociRobot, Walls, PyRobotClient";*/

//		----------------------------------------------------------------------------

		SocketsHolder socketsHolder = new SocketsHolder();

		for (int i = 1; i <= pocetRobotu; i++) {
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

		runRobocode(pocetRobotu, seznamProtivniku);
	}

	public static void runRobocode(int pocetRobotu, String seznamProtivniku) throws IOException {
		String nazevTridyRobotaTCP = "RobotClient";
		// create src and dest path for compiling
		String src = "src/sample/" + nazevTridyRobotaTCP + ".java";
		String dst = "robots/sample/" + nazevTridyRobotaTCP + ".java";
		// compile our created robot and store it to robots/samples
		File source = new File(src);
		File dest = new File(dst);
		Files.copy(source.toPath(), dest.toPath(), StandardCopyOption.REPLACE_EXISTING);
		JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
		compiler.run(null, System.out, System.out, dst);

		// remove all whitespaces
		seznamProtivniku = seznamProtivniku.replaceAll("\\s", "");
		// create list of tanks to fight

		String tanks[] = seznamProtivniku.split(",");
		String finalListOfTanks = "";
		for (String tankName : tanks) {
			tankName = "sample." + tankName + ",";
			finalListOfTanks += tankName;
		}

		// alespon jeden robot
		if (pocetRobotu > 0)
			finalListOfTanks += "sample." + nazevTridyRobotaTCP;
		// dalsi roboti
		for (int i = 1; i < pocetRobotu; i++) {
			finalListOfTanks += ",sample." + nazevTridyRobotaTCP;
		}

		// ("sample.Corners, sample.MujRobot"

		// Battle listener used for receiving battle events
		BattleObserver battleListener = new BattleObserver();

		// Create the RobocodeEngine
		RobocodeEngine engine = new RobocodeEngine(); // Run from current
		// working directory

		// Add battle listener to our RobocodeEngine
		engine.addBattleListener(battleListener);

		// Show the battles
		engine.setVisible(true);

		// Setup the battle specification
		int numberOfRounds = 5000;
		BattlefieldSpecification battlefield = new BattlefieldSpecification(800, 600); // 800x600
		// RobotSpecification[] selectedRobots =
		// engine.getLocalRepository("sample.Corners, sample.MujRobot");
		RobotSpecification[] selectedRobots = engine.getLocalRepository(finalListOfTanks);

		BattleSpecification battleSpec = new BattleSpecification(numberOfRounds, battlefield, selectedRobots);
		// Run our specified battle and let it run till it's over

		engine.runBattle(battleSpec, true/* wait till the battle is over */);

		for (BattleResults result : battleListener.getResults()) {
			System.out.println(result.getTeamLeaderName() + " - " + result.getScore());
		}

		// Cleanup our RobocodeEngine
		engine.close();

		// Make sure that the Java VM is shut down properly
		System.exit(0);
	}
}