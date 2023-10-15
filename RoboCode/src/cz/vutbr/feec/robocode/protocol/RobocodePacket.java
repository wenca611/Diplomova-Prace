package cz.vutbr.feec.robocode.protocol;

import it.rmarcello.protocol.exception.ProtocolException;

public interface RobocodePacket {
	public byte[] toByteArray() throws ProtocolException;
}
