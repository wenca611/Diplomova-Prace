package cz.vutbr.feec.robocode.battle;

import java.io.IOException;

import cz.vutbr.feec.robocode.socket.TCPServerSocket;

public class Student9 {

	public static void main(String argv[]) throws IOException {

		//Student sets his port to connect Client Server
		int port = 5009;

		String agentFilename = "agent.py";

		TCPServerSocket tcpServerSocket = new TCPServerSocket(port, agentFilename);

		for (; ; ) {
			tcpServerSocket.getAction();
		}
	}
}
