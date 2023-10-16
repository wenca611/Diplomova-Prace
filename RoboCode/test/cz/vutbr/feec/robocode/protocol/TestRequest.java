package cz.vutbr.feec.robocode.protocol;

import org.junit.Test;

import it.rmarcello.protocol.exception.ProtocolException;
import junit.framework.TestCase;

public class TestRequest extends TestCase {

	@Test
	public void testSerializeDeserialize() throws ProtocolException {

		byte[] screen = new byte[] { 1 };

		// Convert to byte array
		RobocodeRequest p1 = new RobocodeRequest(800, 800, 3, 3, screen);
		byte[] data = p1.toByteArray();

		// Parsing back
		RobocodeRequest p2 = RobocodeRequest.parse(data);

		// Are they equal?
		assertEquals(p1.getTankX(), p2.getTankX());
		assertEquals(p1.getScreenHeight(), p2.getScreenHeight());
		assertEquals(p1.getScreenWidth(), p2.getScreenWidth());
		assertEquals(p1.getBattlefieldData()[0], p2.getBattlefieldData()[0]);
		//assertEquals(p1.getScreenT1()[0], p2.getScreenT1()[0]);
	}
}