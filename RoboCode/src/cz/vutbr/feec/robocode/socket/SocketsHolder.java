package cz.vutbr.feec.robocode.socket;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class SocketsHolder {

	/**private static Map<Integer, TCPClientSocket> mapOfTCPClientSockets = new HashMap<>();

	public void addTCPClientToMap(int port, TCPClientSocket tcpClientSocket) {
		mapOfTCPClientSockets.put(port, tcpClientSocket);
	}

	public static TCPClientSocket getClientSocketByPort(int port) {
		return mapOfTCPClientSockets.get(port);
	}**/

	// Použijeme ConcurrentHashMap místo HashMap pro více vláken
	private static ConcurrentHashMap<Integer, TCPClientSocket> mapOfTCPClientSockets = new ConcurrentHashMap<>();

	public void addTCPClientToMap(int port, TCPClientSocket tcpClientSocket) {
		mapOfTCPClientSockets.put(port, tcpClientSocket);
	}

	public static TCPClientSocket getClientSocketByPort(int port) {
		return mapOfTCPClientSockets.get(port);
	}
}
