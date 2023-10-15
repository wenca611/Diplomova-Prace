package cz.vutbr.feec.robocode.protocol;

import it.rmarcello.protocol.annotation.NumericEncoding;
import it.rmarcello.protocol.annotation.ProtocolEntity;
import it.rmarcello.protocol.annotation.ProtocolField;
import it.rmarcello.protocol.engine.Engine;
import it.rmarcello.protocol.engine.EngineFactory;
import it.rmarcello.protocol.exception.ProtocolException;

@ProtocolEntity
public class RobocodeRequest implements RobocodePacket {

	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int screenWidth;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int screenHeight;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int tankX;
	@ProtocolField(size = 4, numericEncoding = NumericEncoding.BINARY)
	private int tankY;
	@ProtocolField(size = 30000, numericEncoding = NumericEncoding.BINARY)
	private byte[] battlefieldData;

	public RobocodeRequest() {
	}

	public RobocodeRequest(int screenWidth, int screenHeight, int tankX, int tankY, byte[] battlefieldData) {
		this.screenWidth = screenWidth;
		this.screenHeight = screenHeight;
		this.tankX = tankX;
		this.tankY = tankY;
		this.battlefieldData = battlefieldData;
	}

	public int getTankX() {
		return tankX;
	}

	public int getTankY() {
		return tankY;
	}

	public int getScreenWidth() {
		return screenWidth;
	}

	public int getScreenHeight() {
		return screenHeight;
	}

	public byte[] getBattlefieldData() {
		return battlefieldData;
	}

	@Override
	public byte[] toByteArray() throws ProtocolException {
		Engine engine = EngineFactory.create();
		return engine.toByte(this);
	}

	public static RobocodeRequest parse(byte[] data) throws ProtocolException {
		Engine engine = EngineFactory.create();
		return engine.fromByte(data, RobocodeRequest.class);
	}

	public String getInputStringForAgent() {
		return "[" + screenWidth +
				"," + screenHeight +
				"]";
	}

	@Override
	public String toString() {
		return "RobocodeRequest{" +
				", screenWidth=" + screenWidth +
				", screenHeight=" + screenHeight +
				", tankX=" + tankX +
				", tankY=" + tankY +
				", battlefieldData= longByteArray" +    //Arrays.toString(battlefieldData) +
				'}';
	}
}
