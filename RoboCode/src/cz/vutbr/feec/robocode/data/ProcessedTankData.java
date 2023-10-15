package cz.vutbr.feec.robocode.data;

import java.io.Serializable;

import net.sf.robocode.battle.peer.RobotPeer;

public class ProcessedTankData implements Serializable {

	private double energy;
	private double velocity;
	private double bodyHeading;
	private double gunHeading;
	private double gunHeat;
	private double x;
	private double y;
	private int state;

	public ProcessedTankData(){}

	public ProcessedTankData(RobotPeer robot) {
		this.energy = robot.getEnergy();
		this.velocity = robot.getVelocity();
		this.bodyHeading = robot.getBodyHeading();
		this.gunHeading = robot.getGunHeading();
		this.gunHeat = robot.getGunHeat();
		this.x = robot.getX();
		this.y = robot.getY();
		this.state = robot.getState().getValue();
	}

	public double getEnergy() {
		return energy;
	}

	public double getVelocity() {
		return velocity;
	}

	public double getBodyHeading() {
		return bodyHeading;
	}

	public double getGunHeading() {
		return gunHeading;
	}

	public double getGunHeat() {
		return gunHeat;
	}

	public double getX() {
		return x;
	}

	public double getY() {
		return y;
	}

	public int getState() {
		return state;
	}

	@Override
	public String toString() {
		return "[" + energy +
				"," + velocity +
				"," + bodyHeading +
				"," + gunHeading +
				"," + gunHeat +
				"," + x +
				"," + y +
				"," + state +
				"]";
	}

	public String toStringNo2() {
		return "ProcessedTankData{" +
				"energy=" + energy +
				", velocity=" + velocity +
				", bodyHeading=" + bodyHeading +
				", gunHeading=" + gunHeading +
				", gunHeat=" + gunHeat +
				", x=" + x +
				", y=" + y +
				", state=" + state +
				'}';
	}
}
