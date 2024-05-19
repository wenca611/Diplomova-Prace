package sample;

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

//@SuppressWarnings("ALL")
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

	private static final String FILE_NAME = "ModelGameData.txt";

	public Color bodyColor = Color.decode("#003387");//Color.decode("#008733");
	public Color gunColor = Color.decode("#22EE22");//Color.decode("#FF0000");
	public Color radarColor = Color.decode("#00FFFF");//Color.decode("#66B0F2");

	private Stack<String> eventStack;
	public PyRobotClient() {
	}

	@Override
	public void run() {
		//this.eventStack = new Stack<>();
		Logger.logMessage("Java jede.");
		//	some colors:
		//		https://htmlcolorcodes.com/
		//		https://www.w3schools.com/colors/default.asp
		// Color bodyColor = Color.decode("#003387");
		// Color gunColor = Color.decode("#22EE22");
		// Color radarColor = Color.decode("#00FFFF");
		setColors(bodyColor, gunColor, radarColor);

		Properties prop = new Properties();
		try {
			prop.load(new FileInputStream("config/game.properties"));
		} catch (IOException e) {
			e.printStackTrace();
		}

		int trainingPort = Integer.parseInt(prop.getProperty("trainingPort", "0"));

//		try {
//			Thread.sleep(1000); // Uspí vlákno na 1 sekundu (1000 milisekund)
//		} catch (InterruptedException e) {
//			e.printStackTrace();
//		}

		try {
			Logger.logMessage("Pokus o pripojeni na port: "+trainingPort);
			Socket clientSocket = new Socket("localhost", trainingPort);
			clientSocket.setSoTimeout(200); // Nastavení časového limitu pro příjem dat na 10 sekund
			Logger.logMessage("TCP/IP je aktivní");


			// Kontrola existence souboru
			File file = new File(FILE_NAME);


			//saveToFile(file, "round");
			// Loop forever
			//noinspection InfiniteLoopStatement
			while (true) {
				try {
					//updateActionsFromRobotServer();
					updateActionsWithPython(clientSocket, file);
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

	private void updateActionsWithPython(Socket clientSocket, File file) throws IOException {
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
		/* The robot is active on the battlefield and has not hit the wall or a robot at this turn. */
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

		if (!networkStates.isEmpty()) {
			networkStates = networkStates.substring(0, networkStates.length() - 1);
		}

		//Logger.logMessage("string stavu: " + networkStates);

		/*byte[] bytes = networkStates.getBytes(StandardCharsets.UTF_8);

		// velikost bajtů
		int sizeInBytes = bytes.length;
		Logger.logMessage("počet bytů: " + Integer.toString(sizeInBytes));*/


		PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
		out.println(networkStates);

		/*--------------------------------------AKCE z Neuronové sítě-------------------------------------*/
		// získání akcí z neuronky
		BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
		String receivedActionStr = in.readLine();
        //Logger.logMessage("akce: " + receivedActionStr);
		// Oddělení hodnot pomocí mezer
		String actionValuesStr = receivedActionStr.replaceAll("\\s+", "");
		String[] actionValues = actionValuesStr.split(",");

		/*Logger.logMessage("delka akcí: " + actionValues.length);
		Logger.logMessage("Akce: " + receivedActionStr);
		Logger.logMessage("Akce2: " + String.join(" ", actionValues));*/

		// Získání indexu největšího čísla
		int indexOfMaxAction = getIndexOfMaxValue(actionValues);



		// Kontrola, zda bylo získáno správné množství hodnot
		if (actionValues.length == 44) {
			// Output from Tank
			// Tank move 10 <>
			// Tank turn  30° <>
			// Gun turn 45° <>
			// Shot power  2 <>


			List<List<Integer>> actions2D = new ArrayList<>();

			// První část
			for (int i = 0; i < 5; i++) {
				for (int j = 0; j < 5; j++) {
					List<Integer> sublist = new ArrayList<>();
					sublist.add(i);
					sublist.add(j);
					sublist.add(0);
					sublist.add(2);
					actions2D.add(sublist);
				}
			}

			// Druhá část
			for (int i = 0; i < 4; i++) {
				for (int j = 0; j < 5; j++) {
					if (!(i == 0 && j == 2)) {  // Přidat pouze pokud není (0, 2)
						List<Integer> sublist = new ArrayList<>();
						sublist.add(2);
						sublist.add(2);
						sublist.add(i);
						sublist.add(j);
						actions2D.add(sublist);
					}
				}
			}

			// Výpis výsledného pole polí čtveřic
			/*for (List<Integer> sublist : actions2D) {
				System.out.println(sublist+"\n");
			}*/
			

			List<Float> action1 = Arrays.asList(-10.0f, -5.0f, 0.0f, 5.0f, 10.0f);
			List<Float> action2 = Arrays.asList(-10.0f, -5.0f, 0.0f, 5.0f, 10.0f);
			List<Float> action3 = Arrays.asList(0.0f, 1.0f, 2.0f, 3.0f);
			List<Float> action4 = Arrays.asList(-5.0f, -1.0f, 0.0f, 1.0f, 5.0f);
			//Logger.logMessage(""+action1+" "+action2+" "+action3+" "+action4);


			//Logger.logMessage(""+actions2D);
			//Logger.logMessage(""+actions2D.size());
			//Logger.logMessage(""+actions2D.get(0).size());
			//Logger.logMessage("Index největšího čísla: " + indexOfMaxAction);
			//Logger.logMessage("Akce1: "+action1.get(actions2D.get(indexOfMaxAction).get(0)));
			//Logger.logMessage("Akce2: "+action2.get(actions2D.get(indexOfMaxAction).get(1)));
			//Logger.logMessage("Akce3: "+action3.get(actions2D.get(indexOfMaxAction).get(2)));
			//Logger.logMessage("Akce4: "+action4.get(actions2D.get(indexOfMaxAction).get(3)));


			/*double simulatedTankMove = parseDoubleWithDefault(actionValues[0], 0.0);
			double simulatedTankTurn = parseDoubleWithDefault(actionValues[1], 0.0);
			double simulatedGunTurn = parseDoubleWithDefault(actionValues[2], 0.0);
			double simulatedShotPower = parseDoubleWithDefault(actionValues[3], 0.0);*/


			double simulatedTankMove = (double) action1.get(actions2D.get(indexOfMaxAction).get(0));
			double simulatedTankTurn = (double) action1.get(actions2D.get(indexOfMaxAction).get(1));
			double simulatedGunTurn = (double) action1.get(actions2D.get(indexOfMaxAction).get(2));
			double simulatedShotPower = (double) action1.get(actions2D.get(indexOfMaxAction).get(3));

//			Logger.logMessage("log akce:" + simulatedTankMove + " " + simulatedTankTurn + " " +
//					simulatedGunTurn + " " + simulatedShotPower);

			setMaxVelocity(5);

			moveAmount = simulatedTankMove;
			tankTurn = simulatedTankTurn;
			gunTurn = simulatedGunTurn;
			firePower = simulatedShotPower;
		} else {
			return;
		}

		// Spojení stavu a akce
		String combinedData = networkStates + "|" + indexOfMaxAction;

		// Uložení do souboru
		saveToFile(file, combinedData);
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

	private static void clearFileContent(File file) {
		try (PrintWriter writer = new PrintWriter(file)) {
			// Vymaž obsah souboru
			writer.print("");
			//System.out.println("Obsah souboru byl vymazán.");
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
	}

	private static void saveToFile(File file, String data) {
		try (FileWriter writer = new FileWriter(file, true);
			 BufferedWriter bufferedWriter = new BufferedWriter(writer);
			 PrintWriter printWriter = new PrintWriter(bufferedWriter)) {
			// Uložení dat na poslední řádek
			printWriter.println(data+"");
			//System.out.println("Data byla uložena do souboru.");
		} catch (IOException e) {
			e.printStackTrace();
		}

		/*try {
			FileWriter writer = new FileWriter(file, true); // Otevření souboru pro přidání na konec
			writer.write(data+""); // Zápis nových dat
			writer.close(); // Uzavření souboru
		} catch (IOException e) {
			System.out.println("Nastala chyba při zápisu do souboru: " + e.getMessage());
		}*/


	}

	// Metoda pro převod na Double s výchozí hodnotou pro případ NaN
	private static double parseDoubleWithDefault(String value, double defaultValue) {
		try {
			return Double.parseDouble(value);
		} catch (NumberFormatException | NullPointerException e) {
			return defaultValue;
		}
	}

	public static int getIndexOfMaxValue(String[] actionValues) {
		int indexOfMaxValue = 0;
		float maxValue = Float.MIN_VALUE;

		for (int i = 0; i < actionValues.length; i++) {
			float value = Float.parseFloat(actionValues[i]);
			if (value > maxValue) {
				maxValue = value;
				indexOfMaxValue = i;
			}
		}

		return indexOfMaxValue;
	}

	/**
	 * onHitByBullet:  Turn perpendicular to the bullet, and move a bit.
	 */
	public void onHitByBullet(HitByBulletEvent e) {
		/*String eventMessage = "onHitByBullet";
		String FILE_NAME2 = "ClientError.txt";

		File file = new File(FILE_NAME2);

		if (file.exists()) {
			// Soubor existuje, načti jeho obsah
			try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
				String line;
				while ((line = reader.readLine()) != null) {
					// Zpracování načteného obsahu (pokud je to potřeba)
					// V tomto příkladu zatím jen vypíšeme obsah
					System.out.println("Obsah souboru: " + line);
				}
			} catch (IOException ex) {
				ex.printStackTrace();
			}
		} else {
			// Soubor neexistuje, vytvoř ho
			try {
				file.createNewFile();
			} catch (IOException ex) {
				ex.printStackTrace();
			}
		}

		// Uložení do souboru na zásobník
		try (PrintWriter writer = new PrintWriter(new FileWriter(file, true))) {
			writer.println(eventMessage);
		} catch (IOException ex) {
			ex.printStackTrace();
		}
		eventStack.push(eventMessage);*/
	}

	/**
	 * onHitRobot:  Aim at it.  Fire Hard!
	 */
	public void onHitRobot(HitRobotEvent e) {
		/*String eventMessage = "HitRobotEvent";
		String FILE_NAME2 = "ClientError2.txt";

		File file = new File(FILE_NAME2);

		if (file.exists()) {
			// Soubor existuje, načti jeho obsah
			try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
				String line;
				while ((line = reader.readLine()) != null) {
					// Zpracování načteného obsahu (pokud je to potřeba)
					// V tomto příkladu zatím jen vypíšeme obsah
					System.out.println("Obsah souboru: " + line);
				}
			} catch (IOException ex) {
				ex.printStackTrace();
			}
		} else {
			// Soubor neexistuje, vytvoř ho
			try {
				file.createNewFile();
			} catch (IOException ex) {
				ex.printStackTrace();
			}
		}

		// Uložení do souboru na zásobník
		try (PrintWriter writer = new PrintWriter(new FileWriter(file, true))) {
			writer.println(eventMessage);
		} catch (IOException ex) {
			ex.printStackTrace();
		}
		eventStack.push(eventMessage);*/
	}
}