package cz.vutbr.feec.robocode.protocol;

import static java.lang.Math.abs;

import it.rmarcello.protocol.annotation.NumericEncoding;
import it.rmarcello.protocol.annotation.ProtocolEntity;
import it.rmarcello.protocol.annotation.ProtocolField;
import it.rmarcello.protocol.engine.Engine;
import it.rmarcello.protocol.engine.EngineFactory;
import it.rmarcello.protocol.exception.ProtocolException;

@ProtocolEntity
public class RobocodeResponse implements RobocodePacket {

	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int tankMoveAhead;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int tankMoveBack;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int tankTurnRight;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int tankTurnLeft;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int shotPower;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int gunTurnRight;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int gunTurnLeft;

	public RobocodeResponse() {
	}

	public RobocodeResponse(int tankMoveAhead, int tankMoveBack, int tankTurnRight, int tankTurnLeft, int shotPower, int gunTurnRight,
			int gunTurnLeft) {
		this.tankMoveAhead = tankMoveAhead;
		this.tankMoveBack = tankMoveBack;
		this.tankTurnRight = tankTurnRight;
		this.tankTurnLeft = tankTurnLeft;
		this.shotPower = shotPower;
		this.gunTurnRight = gunTurnRight;
		this.gunTurnLeft = gunTurnLeft;
	}

	public RobocodeResponse(int tankMoveAhead, int tankTurnRight, int shotPower, int gunTurnRight) {
		if (tankMoveAhead >= 0) {
			this.tankMoveAhead = tankMoveAhead;
		} else {
			this.tankMoveBack = abs(tankMoveAhead);
		}

		if (tankTurnRight >= 0) {
			this.tankTurnRight = tankTurnRight;
		} else {
			this.tankTurnLeft = abs(tankTurnRight);
		}

		if (gunTurnRight >= 0) {
			this.gunTurnRight = gunTurnRight;
		} else {
			this.gunTurnLeft = abs(gunTurnRight);
		}

		this.shotPower = shotPower;

	}

	public int getTankMove() {
		return tankMoveAhead - tankMoveBack;
	}

	public int getTankTurn() {
		return tankTurnRight - tankTurnLeft;
	}

	public int getShotPower() {
		return shotPower;
	}

	public int getGunTurn() {
		return gunTurnRight - gunTurnLeft;
	}

	@Override
	public byte[] toByteArray() throws ProtocolException {
		Engine engine = EngineFactory.create();
		return engine.toByte(this);
	}

	public static RobocodeResponse parse(byte[] data) throws ProtocolException {
		Engine engine = EngineFactory.create();
		return engine.fromByte(data, RobocodeResponse.class);
	}

	@Override
	public String toString() {
		return "RobocodeResponse{" +
				"tankMoveAhead=" + tankMoveAhead +
				", tankMoveBack=" + tankMoveBack +
				", tankTurnRight=" + tankTurnRight +
				", tankTurnLeft=" + tankTurnLeft +
				", shotPower=" + shotPower +
				", gunTurnRight=" + gunTurnRight +
				", gunTurnLeft=" + gunTurnLeft +
				'}';
	}
}
