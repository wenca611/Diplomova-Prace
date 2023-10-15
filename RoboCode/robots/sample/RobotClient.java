package sample;

import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.lang.reflect.Field;
import java.util.ArrayList;
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

public class RobotClient extends AdvancedRobot {

	public static int counter = 1;
	private int id = -1;
	private String address = "";
	private int port = -1;
	private String password = "";
	// Turn direction: 1 = turn right, 0 = no turning, -1 = turn left
	int tankTurn;
	int gunTurn;
	// Amount of pixels/units to move
	int moveAmount;
	// The coordinate of the aim (x,y)
	double aimX;
	double aimY;
	// Fire power, where 0 = don't fire
	int firePower;
	private Properties prop;
	private ArrayList<RobotPeer> listOfRobots;
	private CopyOnWriteArrayList<BulletPeer> listOfBullets;
	private BattleRules battleRules;
	private TCPClientSocket tcpClientSocket;

	public RobotClient() {
		id = counter++;

		this.prop = new Properties();
		Logger.logError("*************************************************************");
		Logger.logError("      ID: " + id);
		try {
			prop.load(new FileInputStream("config/game.properties"));
			this.address = prop.getProperty("robot." + id + ".ip");
			this.port = Integer.parseInt(prop.getProperty("robot." + id + ".port"));
			this.password = prop.getProperty("robot." + id + ".password");

			this.tcpClientSocket = SocketsHolder.getClientSocketByPort(port);

		} catch (IOException e) {
			e.printStackTrace();
		}
		Logger.logError("     CONNECTING TO ADDRESS " + address);
		Logger.logError("     CONNECTING TO PORT    " + port);
		Logger.logError("     CONNECTING PSWD       " + password);
		Logger.logError("*************************************************************");
	}

	@Override
	public void run() {
		Color bodyColor = Color.decode(prop.getProperty("robot." + id + ".color.body"));
		Color gunColor = Color.decode(prop.getProperty("robot." + id + ".color.gun"));
		Color radarColor = Color.decode(prop.getProperty("robot." + id + ".color.radar"));
		setColors(bodyColor, gunColor, radarColor);

		// Loop forever
		for (; ; ) {
			try {
				updateActionsFromRobotServer();
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
	}

	@Override
	public void onStatus(StatusEvent e) {
		this.aimX = e.getStatus().getX();
		this.aimY = e.getStatus().getY();
		if (listOfRobots == null) {
			setBattleDataPointers();
		}
	}

	private void updateActionsFromRobotServer() throws IOException {
		ProcessedBattleData processedBattleData = new ProcessedBattleData(getListOfProcessedBullets(), getListOfProcessedTanks());
		Logger.logMessage("tanky: " + processedBattleData.getListOfProcessedTanks());
		Logger.logMessage("strely: " + processedBattleData.getListOfProcessedBullets());


		RobocodeRequest robocodeRequest = new RobocodeRequest(battleRules.getBattlefieldWidth(),
				battleRules.getBattlefieldHeight(), (int) aimX, (int) aimY, convertBattleDataToByteArray(processedBattleData));

		RobocodeResponse robocodeResponse = tcpClientSocket.getAction(robocodeRequest);

		moveAmount = robocodeResponse.getTankMove();
		tankTurn = robocodeResponse.getTankTurn();
		firePower = robocodeResponse.getShotPower();
		gunTurn = robocodeResponse.getGunTurn();

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
}