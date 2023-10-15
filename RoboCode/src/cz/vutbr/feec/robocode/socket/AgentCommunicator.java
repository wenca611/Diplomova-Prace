package cz.vutbr.feec.robocode.socket;

import static java.lang.Math.abs;

import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.ObjectInputStream;
import java.util.Arrays;
import java.util.List;

import cz.vutbr.feec.robocode.data.ProcessedBattleData;
import cz.vutbr.feec.robocode.data.ProcessedTankData;
import cz.vutbr.feec.robocode.protocol.RobocodeRequest;
import cz.vutbr.feec.robocode.protocol.RobocodeResponse;

public class AgentCommunicator {

	private final String agentFilePath;

	public AgentCommunicator(String ageneFilename) {
		this.agentFilePath = "src/cz/vutbr/feec/robocode/studentRobot/" + ageneFilename;

	}

	public RobocodeResponse generateInstruction(RobocodeRequest request) throws IOException {

		ProcessedBattleData processedBattleData = convertBattleData(request);
		ProcessedTankData myTank = getMyTank(processedBattleData, request.getTankX(), request.getTankY());

		ProcessBuilder pb = new ProcessBuilder("python", agentFilePath,
				request.getInputStringForAgent(),
				myTank.toString(),
				processedBattleData.getListOfProcessedTanks().toString(),
				processedBattleData.getListOfProcessedBullets().toString());

		Process process = pb.start();

		BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));

		String output;

		while ((output = reader.readLine()) != null) {
			if (output.startsWith("RESPONSE:")) {
				break;
			}
		}

		List<String> params = Arrays.asList(output.substring(9).split(","));

		System.out.println(params);

		return new RobocodeResponse(Integer.parseInt(params.get(0)), Integer.parseInt(params.get(1)), Integer.parseInt(params.get(2)),
				Integer.parseInt(params.get(3)));
	}

	public ProcessedBattleData convertBattleData(RobocodeRequest request) {
		ProcessedBattleData processedBattleData;

		try {
			processedBattleData = convertByteArrayToListBattle((request.getBattlefieldData()));
		} catch (ClassNotFoundException | IOException e) {
			throw new RuntimeException(e);
		}

//		System.out.println("----------------------------------------------------");
//		System.out.println(request.toString());
//		System.out.println("----------Tanks---------------------------");
//		System.out.println(processedBattleData.getListOfProcessedTanks());
//		System.out.println("-----------Bullets---------------------------");
//		System.out.println(processedBattleData.getListOfProcessedBullets());

		return processedBattleData;

	}

	public ProcessedBattleData convertByteArrayToListBattle(byte[] byteArray) throws IOException, ClassNotFoundException {
		ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(byteArray);
		ObjectInputStream objectInputStream = new ObjectInputStream(byteArrayInputStream);
		ProcessedBattleData list = (ProcessedBattleData) objectInputStream.readObject();
		objectInputStream.close();
		return list;
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
}
