package sample;

import java.awt.Color;
import java.io.*;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Properties;
import java.util.concurrent.CopyOnWriteArrayList;

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

import static java.lang.Math.abs;

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

@SuppressWarnings("ALL")
public class PyRobotClient extends AdvancedRobot {

	public static int counter = 1;
	private int id = -1;
	private String address = "";
	private int port = -1;
	private String password = "";
	// Turn direction: 1 = turn right, 0 = no turning, -1 = turn left
	double tankTurn;
	double gunTurn;
	// Amount of pixels/units to move
	double moveAmount;
	// The coordinate of the aim (x,y)
	double aimX;
	double aimY;
	// Fire power, where 0 = don't fire
	double firePower;
	private Properties prop;
	private ArrayList<RobotPeer> listOfRobots;
	private CopyOnWriteArrayList<BulletPeer> listOfBullets;
	private BattleRules battleRules;
	private TCPClientSocket tcpClientSocket;
	private boolean isFirstCall = true; // Definice členské proměnné

	public Color bodyColor = Color.decode("#003387");//Color.decode("#008733");
	public Color gunColor = Color.decode("#22EE22");//Color.decode("#FF0000");
	public Color radarColor = Color.decode("#00FFFF");//Color.decode("#66B0F2");

	public PyRobotClient() {
		id = counter; //zmena ++ na nic

		this.prop = new Properties();
		//Logger.logError("*************************************************************");
		//Logger.logError("      ID: " + id);
		try {
			prop.load(new FileInputStream("config/game.properties"));
			//this.address = prop.getProperty("robot." + id + ".ip");
			//this.port = Integer.parseInt(prop.getProperty("robot." + id + ".port"));
			//this.password = prop.getProperty("robot." + id + ".password");

			//this.tcpClientSocket = SocketsHolder.getClientSocketByPort(port);

		} catch (IOException e) {
			e.printStackTrace();
		}
		//Logger.logError("     CONNECTING TO ADDRESS " + address);
		//Logger.logError("     CONNECTING TO PORT    " + port);
		//Logger.logError("     CONNECTING PSWD       " + password);
		//Logger.logError("*************************************************************");
	}

	@Override
	public void run() {
		// some colors:
		// 	https://htmlcolorcodes.com/
		// 	https://www.w3schools.com/colors/default.asp
		//Color bodyColor = Color.decode("#003387");//Color.decode("#008733");
		//Color gunColor = Color.decode("#22EE22");//Color.decode("#FF0000");
		//Color radarColor = Color.decode("#00FFFF");//Color.decode("#66B0F2");
		setColors(bodyColor, gunColor, radarColor);

		int freePort = findFreePort();

		try {
			ServerSocket serverSocket = new ServerSocket(freePort);
			serverSocket.setSoTimeout(2500);

			String pythonPath = "src/cz/vutbr/feec/robocode/studentRobot/";
			String pythonScript = "NeuralTank.py";
			String argument = Integer.toString(freePort); // port

			ProcessBuilder processBuilder = new ProcessBuilder("python", pythonPath+pythonScript, argument);
			processBuilder.redirectOutput(Redirect.DISCARD);
			processBuilder.redirectError(Redirect.DISCARD);

			Process process = processBuilder.start();

			/*try {
				// Počkej 3 sekundy
				Thread.sleep(10000);
			} catch (InterruptedException e) {
				Thread.currentThread().interrupt();
			}*/

			Socket clientSocket = serverSocket.accept();

			serverSocket.setSoTimeout(500);

			// Loop forever
			//noinspection InfiniteLoopStatement
			while (true) {
				try {
					//updateActionsFromRobotServer();
					updateActionsWithPython(clientSocket);
				} catch (IOException e) {
					throw new RuntimeException(e);
				}

				// Sets the robot to move forward, backward or stop moving depending
				// on the move direction and amount of pixels to move
				setAhead(moveAmount);

				// Sets robot rotation in degrees turn:
				// right > 0;
				// left < negative;
				// none = 0
				setTurnRight(tankTurn);

				// Sets gun rotation in degrees turn:
				// right > 0;
				// left < negative;
				// none = 0
				setTurnGunRight(gunTurn);

				// Fire the gun with the specified fire power, unless the fire power = 0
				if (firePower > 0) {
					setFire(firePower);
				}

				// Execute all pending set-statements
				execute();
			}

		} catch (IOException e) {
			throw new RuntimeException(e);
		}
    }

	@Override
	public void onStatus(StatusEvent e) {
		this.aimX = e.getStatus().getX();
		this.aimY = e.getStatus().getY();
		if (listOfRobots == null) {
			setBattleDataPointers();
		}
	}

	private void updateActionsWithPython(Socket clientSocket) throws IOException {
		// Získání informací o bitevním poli
		ProcessedBattleData processedBattleData = new ProcessedBattleData(getListOfProcessedBullets(), getListOfProcessedTanks());

		//Logger.logMessage("tanky: " + processedBattleData.getListOfProcessedTanks());
		ProcessedTankData myTank = getMyTank(processedBattleData, (int) aimX, (int) aimY);
		//Logger.logMessage("size: " + battleRules.getBattlefieldWidth() + " " + battleRules.getBattlefieldHeight());
		//Logger.logMessage("Muj tank: " + myTank);
		//Logger.logMessage("Ostatni tanky: " + processedBattleData.getListOfProcessedTanks());
		//Logger.logMessage("strely: " + processedBattleData.getListOfProcessedBullets());

		//Random color RGB
		//Color bodyColor = generateRandomColor();
		//Color gunColor = generateRandomColor();
		Color radarColor = generateRandomColor();
		setColors(bodyColor, gunColor, radarColor);

		// Input for Tank
		// map size [x, y] [800, 600] skip
		// my tank [_ _ _ _ _ _ _ _]
		// other tanks [[_ _ _ _ _ _ _ _], ...] = tanks - my tank
		// bullets [[_ _ _ _], ...]

		//Tank:
		//this.energy = robot.getEnergy();
		//this.velocity = robot.getVelocity();
		//this.bodyHeading = robot.getBodyHeading();
		//this.gunHeading = robot.getGunHeading();
		//this.gunHeat = robot.getGunHeat();
		//this.x = robot.getX();
		//this.y = robot.getY();
		//this.state = robot.getState().getValue(); INT
		///** The robot is active on the battlefield and has not hit the wall or a robot at this turn. */
		//ACTIVE(0),
		//
		///** The robot has hit a wall, i.e. one of the four borders, at this turn. This state only last one turn. */
		//HIT_WALL(1),
		//
		///** The robot has hit another robot at this turn. This state only last one turn. */
		//HIT_ROBOT(2),
		//
		///** The robot is dead. */
		//DEAD(3);

		//Bullet:
		//this.heading = bullet.getHeading();
		//this.x = bullet.getX();
		//this.y = bullet.getY();
		//this.power = bullet.getPower();

		/*--------------------------------------STAVY do Neuronové sítě-------------------------------------*/
		// poslání stavů do neuronky
		String networkStates = "";

		// Tanks:
		List<ProcessedTankData> allTanks = new ArrayList<>(processedBattleData.getListOfProcessedTanks());
		allTanks.add(0, myTank);

		if (allTanks.size() > 10) {
			allTanks = allTanks.subList(0, 10);
		}

		// Vytvoření řetězce stavů přímo v cyklu
		for (ProcessedTankData tank : allTanks) { // 10 or less
			networkStates += tank.toString() + " ";
		}

		if (allTanks.size() < 10) {
			List<Object> deathTank = new ArrayList<>();
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
		List<ProcessedBulletData> allBullets = new ArrayList<>(processedBattleData.getListOfProcessedBullets());

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

		//Logger.logMessage("string stavu: " + networkStates);

		/*byte[] bytes = networkStates.getBytes(StandardCharsets.UTF_8);

		// velikost bajtů
		int sizeInBytes = bytes.length;
		Logger.logMessage("počet bytů: " + Integer.toString(sizeInBytes));*/


		PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
		out.println(networkStates);

		// získání akcí z neuronky
		BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
		String receivedActionStr = in.readLine();

		// Oddělení hodnot pomocí mezer
		String[] actionValues = receivedActionStr.replaceAll("[\\[\\]]", "").split("\\s+");

		// Kontrola, zda bylo získáno správné množství hodnot
		if (actionValues.length == 4) {
			// Output from Tank
			// Tank move 10 <>
			// Tank turn  30° <>
			// Shot power  2 <>
			// Gun turn 45° <>
			double simulatedTankMove = Double.parseDouble(actionValues[0]);
			double simulatedTankTurn = Double.parseDouble(actionValues[1]);
			double simulatedShotPower = Double.parseDouble(actionValues[2]);
			double simulatedGunTurn = Double.parseDouble(actionValues[3]);

			moveAmount = simulatedTankMove;
			tankTurn = simulatedTankTurn;
			firePower = simulatedShotPower;
			gunTurn = simulatedGunTurn;

		} else {
			// Chyba ve formátu vstupního řetězce
			//.err.println("Chybný formát vstupního řetězce: " + receivedActionStr);
			// na konci už nic
		}


		// Uložení stavů a akcí do souboru
		/*try (FileWriter writer = new FileWriter("data.txt", true)) {
			writer.write(myTank+"+"); // muj tank
			writer.write(processedBattleData.getListOfProcessedTanks()+"+"); // ostatni tanky
			writer.write(processedBattleData.getListOfProcessedBullets()+"+"); // strely
			writer.write(Arrays.toString(qTable[state])+"\n");

		} catch (IOException e) {
			e.printStackTrace();
		}*/

		// Nastavení akcí na základě simulovaných dat

	}

	private void updateActionsFromRobotServer() throws IOException {
		ProcessedBattleData processedBattleData = new ProcessedBattleData(getListOfProcessedBullets(), getListOfProcessedTanks());

		RobocodeRequest robocodeRequest = new RobocodeRequest(battleRules.getBattlefieldWidth(),
				battleRules.getBattlefieldHeight(), (int) aimX, (int) aimY, convertBattleDataToByteArray(processedBattleData));

		RobocodeResponse robocodeResponse = tcpClientSocket.getAction(robocodeRequest);

		moveAmount = robocodeResponse.getTankMove();
		tankTurn = robocodeResponse.getTankTurn();
		firePower = robocodeResponse.getShotPower();
		gunTurn = robocodeResponse.getGunTurn();
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
	public void onRoundEnded(RoundEndedEvent event) {
		RobotClient.counter = 1; // reset counter
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

	public byte[] convertBattleDataToByteArray(ProcessedBattleData list) throws IOException {
		ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
		ObjectOutputStream objectOutputStream = new ObjectOutputStream(byteArrayOutputStream);
		objectOutputStream.writeObject(list);
		objectOutputStream.close();
		return byteArrayOutputStream.toByteArray();
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

	public static int findFreePort() {
		int port;
		ServerSocket serverSocket = null;
		try {
			serverSocket = new ServerSocket(0); // Nulový port způsobí, že systém vybere volný port
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

	public static Color generateRandomColor() {
		int red = (int) (Math.random() * 256);
		int green = (int) (Math.random() * 256);
		int blue = (int) (Math.random() * 256);
		return new Color(red, green, blue);
	}
}