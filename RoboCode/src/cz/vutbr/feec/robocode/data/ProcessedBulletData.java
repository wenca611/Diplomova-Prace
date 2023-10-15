package cz.vutbr.feec.robocode.data;

import java.io.Serializable;

import net.sf.robocode.battle.peer.BulletPeer;

public class ProcessedBulletData implements Serializable {

	private double heading;
	private double x;
	private double y;
	private double power;

	public ProcessedBulletData(BulletPeer bullet) {
		this.heading = bullet.getHeading();
		this.x = bullet.getX();
		this.y = bullet.getY();
		this.power = bullet.getPower();
	}

	public double getHeading() {
		return heading;
	}

	public double getX() {
		return x;
	}

	public double getY() {
		return y;
	}

	public double getPower() {
		return power;
	}

	@Override
	public String toString() {
		return "[" + heading +
				"," + x +
				"," + y +
				"," + power +
				"]";
	}

	public String toStringNo2() {
		return "ProcessedBulletData{" +
				"heading=" + heading +
				", x=" + x +
				", y=" + y +
				", power=" + power +
				'}';
	}
}
