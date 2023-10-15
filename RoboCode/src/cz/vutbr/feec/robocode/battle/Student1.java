package cz.vutbr.feec.robocode.battle;

import java.io.IOException;

import cz.vutbr.feec.robocode.socket.TCPServerSocket;

public class Student1 {

	public static void main(String argv[]) throws IOException {

		//Student sets his port to connect Client Server
		int port = 5001;

		//Insert name of Python file with your model "NAME.py"
		String agentFilename = "agent.py";
		//String agentFilename = "default.py";
		//String agentFilename = "practice.py";


		TCPServerSocket tcpServerSocket = new TCPServerSocket(port, agentFilename);

		for (; ; ) {
			tcpServerSocket.getAction();
		}

	}
}
