package cz.vutbr.feec.robocode.protocol;

import org.junit.Test;

import it.rmarcello.protocol.exception.ProtocolException;
import junit.framework.TestCase;

public class TestResponse extends TestCase {

	@Test
	public void testResponse() throws ProtocolException {
		// Convert to byte array
		RobocodeResponse p1 = new RobocodeResponse(1, 1, 1, 1, 1, 1, 1);
		byte[] data = p1.toByteArray();

		// Parsing back
		RobocodeResponse p2 = RobocodeResponse.parse(data);

		// Are they equal?
		assertEquals(p1.getTankMove(), p2.getTankMove());
		assertEquals(p1.getShotPower(), p2.getShotPower());
		assertEquals(p1.getTankTurn(), p2.getTankTurn());
		assertEquals(p1.getGunTurn(), p2.getGunTurn());
	}
}
