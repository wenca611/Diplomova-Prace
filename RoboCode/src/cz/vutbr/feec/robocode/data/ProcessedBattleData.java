package cz.vutbr.feec.robocode.data;

import java.io.Serializable;
import java.util.ArrayList;

public class ProcessedBattleData implements Serializable {

	private ArrayList<ProcessedBulletData> listOfProcessedBullets;
	private ArrayList<ProcessedTankData> listOfProcessedTanks;

	public ProcessedBattleData() {
	}

	public ProcessedBattleData(ArrayList<ProcessedBulletData> listOfProcessedBullets, ArrayList<ProcessedTankData> listOfProcessedTanks) {
		this.listOfProcessedTanks = listOfProcessedTanks;
		this.listOfProcessedBullets = listOfProcessedBullets;
	}

	public ArrayList<ProcessedTankData> getListOfProcessedTanks() {
		return listOfProcessedTanks;
	}

	public ArrayList<ProcessedBulletData> getListOfProcessedBullets() {
		return listOfProcessedBullets;
	}

	public void removeTank(ProcessedTankData tank){
		listOfProcessedTanks.remove(tank);
	}

	@Override
	public String toString() {
		return "ProcessedBattleData{" +
				"listOfProcessedBullets=" + listOfProcessedBullets +
				", listOfProcessedTanks=" + listOfProcessedTanks +
				'}';
	}
}
