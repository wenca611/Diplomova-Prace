/**
 * Copyright (c) 2001-2017 Mathew A. Nelson and Robocode contributors
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * which accompanies this distribution, and is available at
 * http://robocode.sourceforge.net/license/epl-v10.html
 */
package sample;


import cz.vutbr.feec.robocode.data.ProcessedBattleData;
import cz.vutbr.feec.robocode.data.ProcessedBulletData;
import cz.vutbr.feec.robocode.data.ProcessedTankData;
import net.sf.robocode.battle.Battle;
import net.sf.robocode.battle.peer.BulletPeer;
import net.sf.robocode.battle.peer.RobotPeer;
import net.sf.robocode.host.proxies.AdvancedRobotProxy;
import robocode.*;

import java.awt.*;
import java.io.*;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.Stack;
import java.util.concurrent.CopyOnWriteArrayList;

import static java.lang.Math.abs;

/*  for training model    	*/
import net.sf.robocode.io.Logger;
import java.util.Stack;


/**
 * SpinBot - a sample robot by Mathew Nelson.
 * <p>
 * Moves in a circle, firing hard when an enemy is detected.
 *
 * @author Mathew A. Nelson (original)
 * @author Flemming N. Larsen (contributor)
 */
public class SpinBot extends AdvancedRobot {

	/*  for training model    	*/
	private static final String FILE_NAME = "ModelGameData.txt";
	private static Stack<String> dataStack = new Stack<>();
	private Properties prop;
	private ArrayList<RobotPeer> listOfRobots;
	private CopyOnWriteArrayList<BulletPeer> listOfBullets;
	private BattleRules battleRules;

	double aimX;
	double aimY;

	private String states = "";

	private double[] actions = new double[4];
	private String actionsString = "";



	/**
	 * SpinBot's run method - Circle
	 */
	public void run() {
		// Set colors
		setBodyColor(Color.blue);
		setGunColor(Color.blue);
		setRadarColor(Color.black);
		setScanColor(Color.yellow);

		createFileIfNotExists(FILE_NAME);
		// Loop forever
		while (true) {
			ProcessedBattleData processedBattleData = new ProcessedBattleData(getListOfProcessedBullets(), getListOfProcessedTanks());
			ProcessedTankData myTank = getMyTank(processedBattleData, (int) aimX, (int) aimY);

			/*--------------------------------------STAVY-------------------------------------*/
			// poslání stavů do neuronky
			String networkStates = "";

			// Tanks:
			java.util.List<ProcessedTankData> allTanks = new ArrayList<>(processedBattleData.getListOfProcessedTanks());
			allTanks.add(0, myTank);

			if (allTanks.size() > 10) {
				allTanks = allTanks.subList(0, 10);
			}

			// Vytvoření řetězce stavů přímo v cyklu
			for (ProcessedTankData tank : allTanks) { // 10 or less
				networkStates += tank.toString() + " ";
			}

			if (allTanks.size() < 10) {
				java.util.List<Object> deathTank = new ArrayList<>();
				for (int i = 0; i < 7; i++) {
					deathTank.add(0.0);
				}
				deathTank.add(3);

				int additionalTanks = 10 - allTanks.size();
				// Přidej čísla z objektu `deathTank` na konec `networkStates` v závislosti na velikosti `additionalTanks`
				for (int i = 0; i < additionalTanks; i++) {
					for (Object value : deathTank) {
						networkStates += value.toString() + " ";
					}
				}
			}

			// Bullets:
			java.util.List<ProcessedBulletData> allBullets = new ArrayList<>(processedBattleData.getListOfProcessedBullets());

			if (allBullets.size() > 20) {
				allBullets = allBullets.subList(0, 10);
			}

			// Vytvoření řetězce stavů přímo v cyklu
			for (ProcessedBulletData bullet : allBullets) { // 20 or less
				networkStates += bullet.toString() + " ";
			}

			if (allBullets.size() < 20) {
				List<Object> noBullet = new ArrayList<>();
				for (int i = 0; i < 4; i++) {
					noBullet.add(0.0);
				}

				int additionalBullets = 20 - allBullets.size();
				// Přidej čísla z objektu `deathTank` na konec `networkStates` v závislosti na velikosti `additionalTanks`
				for (int i = 0; i < additionalBullets; i++) {
					for (Object value : noBullet) {
						networkStates += value.toString() + " ";
					}
				}
			}

			networkStates = networkStates.replaceAll("[\\[\\]]", "").replaceAll(",", " ");

			if (networkStates.length() > 0) {
				networkStates = networkStates.substring(0, networkStates.length() - 1);
			}

			states = networkStates;

			//Logger.logMessage("stavy:" + networkStates);

			/*--------------------------------------AKCE-------------------------------------*/
			// Tank move 10 <>
			// Tank turn  30° <>
			// Gun turn 45° <>
			// Shot power  2 <>

			// Tell the game that when we take move,
			// we'll also want to turn right... a lot.
			setTurnRight(10000);
			// Limit our speed to 5
			setMaxVelocity(5);
			// Start moving (and turning)
			ahead(10000);
			// Repeat.
			//<----
			actions = new double[]{10000., 10000., 0., 0.};
			createActionsString();
//			saveToFile(FILE_NAME, states + "|" + actionsString);


		}
	}

	/**
	 * onScannedRobot: Fire hard!
	 */
	public void onScannedRobot(ScannedRobotEvent e) {
		fire(3);
		//<----
		actions = new double[]{0., 0., 0., 3.};
		createActionsString();
//		saveToFile(FILE_NAME, states + "|" + actionsString);
	}

	/**
	 * onHitRobot:  If it's our fault, we'll stop turning and moving,
	 * so we need to turn again to keep spinning.
	 */
	public void onHitRobot(HitRobotEvent e) {
		if (e.getBearing() > -10 && e.getBearing() < 10) {
			fire(3);
			//<----
			actions = new double[]{0., 0., 0., 3.};
			createActionsString();
//			saveToFile(FILE_NAME, states + "|" + actionsString);
		}
		if (e.isMyFault()) {
			turnRight(10);
			//<----
			actions = new double[]{0., 10., 0., 0.};
			createActionsString();
//			saveToFile(FILE_NAME, states + "|" + actionsString);
		}
	}

	/*  for training model */
	private static void saveToFile(String fileName, String message) {
		try (PrintWriter writer = new PrintWriter(new FileWriter(fileName, true))) {
			writer.println(message);
		} catch (IOException e) {
			e.printStackTrace();
		}
		dataStack.push(message);
	}

	private static void createFileIfNotExists(String fileName) {
		File file = new File(fileName);

		if (file.exists()) {
			// Pokud soubor existuje, smažeme jeho obsah
			try (PrintWriter writer = new PrintWriter(file)) {
				writer.print(""); // Tímto smažeme obsah souboru
			} catch (IOException e) {
				e.printStackTrace();
			}
		} else {
			// Pokud soubor neexistuje, vytvoříme nový
			try {
				file.createNewFile();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}

	private void createActionsString() {
		actionsString = "";
		for (int i = 0; i < actions.length; i++) {
			actionsString += actions[i];

			// Přidání mezery, pokud to není poslední číslo v poli
			if (i < actions.length - 1) {
				actionsString += " ";
			}
		}
	}

	public ArrayList<ProcessedTankData> getListOfProcessedTanks() {
		ArrayList<ProcessedTankData> listOfProcessedTanks = new ArrayList<ProcessedTankData>();
		for (RobotPeer tank : listOfRobots) {
			listOfProcessedTanks.add(new ProcessedTankData(tank));
		}
		return listOfProcessedTanks;
	}

	public ArrayList<ProcessedBulletData> getListOfProcessedBullets() {
		ArrayList<ProcessedBulletData> listOfProcessedBullets = new ArrayList<ProcessedBulletData>();
		for (BulletPeer bullet : listOfBullets) {
			listOfProcessedBullets.add(new ProcessedBulletData(bullet));
		}
		return listOfProcessedBullets;
	}

	public void setBattleDataPointers() {
		try {
			Field robotClientPeer = _RobotBase.class.getDeclaredField("peer");
			robotClientPeer.setAccessible(true);
			AdvancedRobotProxy robotClientProxy = (AdvancedRobotProxy) robotClientPeer.get(this);

			Class<?> abstractClass = Class.forName("net.sf.robocode.host.proxies.HostingRobotProxy");
			Field robotClientProxyPeer = abstractClass.getDeclaredField("peer");
			robotClientProxyPeer.setAccessible(true);
			RobotPeer robotPeer = (RobotPeer) robotClientProxyPeer.get(robotClientProxy);

			Field fieldOfBattle = RobotPeer.class.getDeclaredField("battle");
			fieldOfBattle.setAccessible(true);
			Battle battle = (Battle) fieldOfBattle.get(robotPeer);

			Field fieldOfRobots = Battle.class.getDeclaredField("robots");
			fieldOfRobots.setAccessible(true);
			listOfRobots = (ArrayList<RobotPeer>) fieldOfRobots.get(battle);

			Field fieldOfBullets = Battle.class.getDeclaredField("bullets");
			fieldOfBullets.setAccessible(true);
			listOfBullets = (CopyOnWriteArrayList<BulletPeer>) fieldOfBullets.get(battle);

			battleRules = battle.getBattleRules();

		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public ProcessedTankData getMyTank(ProcessedBattleData battleData, int x, int y) {
		for (ProcessedTankData tank : battleData.getListOfProcessedTanks()) {
			if (abs(tank.getX() - x) < 1 && (abs(tank.getY() - y) < 1)) {
				battleData.removeTank(tank);

				return tank;
			}
		}
		return new ProcessedTankData();
	}

	@Override
	public void onStatus(StatusEvent e) {
		this.aimX = e.getStatus().getX();
		this.aimY = e.getStatus().getY();
		if (listOfRobots == null) {
			setBattleDataPointers();
		}
	}

}
