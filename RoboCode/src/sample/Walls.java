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
import robocode.Robot;

import java.awt.*;

// Walls -> WallsTrain for training model
import robocode.BattleRules;
import robocode.AdvancedRobot;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Stack;
import java.util.concurrent.CopyOnWriteArrayList;

import static java.lang.Math.abs;









/**/
import java.awt.Color;
import java.io.*;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Properties;
import java.util.concurrent.CopyOnWriteArrayList;

import cz.vutbr.feec.robocode.battle.BattleObserver;
import cz.vutbr.feec.robocode.data.ProcessedBattleData;
import cz.vutbr.feec.robocode.data.ProcessedBulletData;
import cz.vutbr.feec.robocode.data.ProcessedTankData;
import cz.vutbr.feec.robocode.protocol.RobocodeRequest;
import cz.vutbr.feec.robocode.protocol.RobocodeResponse;
import cz.vutbr.feec.robocode.socket.SocketsHolder;
import cz.vutbr.feec.robocode.socket.TCPClientSocket;
import net.sf.robocode.battle.Battle;
import net.sf.robocode.battle.peer.BulletPeer;
import net.sf.robocode.battle.peer.RobotPeer;
import net.sf.robocode.host.proxies.AdvancedRobotProxy;
import net.sf.robocode.io.Logger;
import robocode.AdvancedRobot;
import robocode.BattleRules;
import robocode.RoundEndedEvent;
import robocode.StatusEvent;
import robocode._RobotBase;
import robocode.BattleResults;

import static java.lang.Math.abs;
import static robocode.util.Utils.normalRelativeAngleDegrees;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
import java.net.ServerSocket;
import java.net.SocketTimeoutException;
import java.net.*;
import java.lang.ProcessBuilder.Redirect;
import java.util.List;
import java.nio.charset.StandardCharsets;
import robocode.HitByBulletEvent;
import robocode.HitRobotEvent;
import java.util.Stack;
/**/

/**
 * Walls - a sample robot by Mathew Nelson, and maintained by Flemming N. Larsen
 * <p>
 * Moves around the outer edge with the gun facing in.
 *
 * @author Mathew A. Nelson (original)
 * @author Flemming N. Larsen (contributor)
 */
public class Walls extends Robot {

	boolean peek; // Don't turn if there's a robot there
	double moveAmount; // How much to move

	/*  for training model    	*/
	private static final String FILE_NAME = "ModelGameData.txt";
	private static String states = "";
	private static double[] actions = new double[4];
	private static Stack<String> dataStack = new Stack<>();
	double aimX;
	double aimY;
	private ArrayList<RobotPeer> listOfRobots;
	private CopyOnWriteArrayList<BulletPeer> listOfBullets;
	private BattleRules battleRules;


	/**
	 * run: Move around the walls
	 */
	public void run() {
		// Set colors
		setBodyColor(Color.black);
		setGunColor(Color.black);
		setRadarColor(Color.orange);
		setBulletColor(Color.cyan);
		setScanColor(Color.cyan);

		/*  for training model */
		createFileIfNotExists(FILE_NAME);
		// Získání informací o bitevním poli
		//ProcessedBattleData processedBattleData = new ProcessedBattleData(getListOfProcessedBullets(), getListOfProcessedTanks());
		//ProcessedTankData myTank = getMyTank(processedBattleData, (int) aimX, (int) aimY);




		// Initialize moveAmount to the maximum possible for this battlefield.
		moveAmount = Math.max(getBattleFieldWidth(), getBattleFieldHeight());
		// Initialize peek to false
		peek = false;

		// turnLeft to face a wall.
		// getHeading() % 90 means the remainder of
		// getHeading() divided by 90.
		turnLeft(getHeading() % 90);
		ahead(moveAmount);
		// <----
		// Turn the gun to turn right 90 degrees.
		peek = true;
		turnGunRight(90);
		turnRight(90);
		// <----

		while (true) {
			// Look before we turn when ahead() completes.
			peek = true;
			// Move up the wall
			ahead(moveAmount);
			// <----
			// Don't look now
			peek = false;
			// Turn to the next wall
			turnRight(90);
			// <----
		}
	}

	/**
	 * onHitRobot:  Move away a bit.
	 */
	public void onHitRobot(HitRobotEvent e) {
		// If he's in front of us, set back up a bit.
		if (e.getBearing() > -90 && e.getBearing() < 90) {
			back(100);
		} // else he's in back of us, so set ahead a bit.
		else {
			ahead(100);
		}
		// <----
	}

	/**
	 * onScannedRobot:  Fire!
	 */
	public void onScannedRobot(ScannedRobotEvent e) {
		fire(2);
		// <----


		// Note that scan is called automatically when the robot is moving.
		// By calling it manually here, we make sure we generate another scan event if there's a robot on the next
		// wall, so that we do not start moving up it until it's gone.
		if (peek) {
			scan();
		}
	}

	/*  for training model */
	@Override
	public void onStatus(StatusEvent e) {
		this.aimX = e.getStatus().getX();
		this.aimY = e.getStatus().getY();
		if (listOfRobots == null) {
			setBattleDataPointers();
		}
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

	public ProcessedTankData getMyTank(ProcessedBattleData battleData, int x, int y) {
		for (ProcessedTankData tank : battleData.getListOfProcessedTanks()) {
			if (abs(tank.getX() - x) < 1 && (abs(tank.getY() - y) < 1)) {
				battleData.removeTank(tank);

				return tank;
			}
		}
		return new ProcessedTankData();
	}








	/* Setup file for Episodic memory */

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





	/*  for training model    	*/
	/*private static void clearFileContent(File file) {
		try (PrintWriter writer = new PrintWriter(file)) {
			// Vymaž obsah souboru
			writer.print("");
			System.out.println("Obsah souboru byl vymazán.");
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	private static void createFile(File file) {
		try {
			// Vytvoř soubor
			if (file.createNewFile()) {
				System.out.println("Soubor vytvořen: " + file.getName());
			} else {
				System.out.println("Soubor již existuje.");
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}*/

}


