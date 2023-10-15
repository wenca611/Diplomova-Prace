package cz.vutbr.feec.robocode.socket;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;

import cz.vutbr.feec.robocode.protocol.RobocodeRequest;
import cz.vutbr.feec.robocode.protocol.RobocodeResponse;
import it.rmarcello.protocol.exception.ProtocolException;

public class TCPServerSocket {

	private final ServerSocket welcomeSocket;
	private final Socket connectionSocket;
	private final DataInputStream inFromClient;
	private final DataOutputStream outToClient;
	private final AgentCommunicator agentCommunicator;

	// Constructor to initialize the server socket, connection, and communication streams.
	public TCPServerSocket(int port, String agentFilename) throws IOException {
		System.out.println("waiting for connections");
		welcomeSocket = new ServerSocket(port);
		connectionSocket = welcomeSocket.accept();
		inFromClient = new DataInputStream(connectionSocket.getInputStream());
		outToClient = new DataOutputStream(connectionSocket.getOutputStream());
		agentCommunicator = new AgentCommunicator(agentFilename);
	}

	// Sends a response to the connected client.
	public void sendResponse(RobocodeResponse response) throws IOException, ProtocolException {
		System.out.println(response.toString());
		outToClient.write(response.toByteArray());
		outToClient.flush();
	}

	// Reads and processes a request from the connected client.
	public RobocodeRequest processRequest() throws IOException, ProtocolException {
		byte[] buffer = new byte[50000];
		inFromClient.read(buffer);

		RobocodeRequest request = RobocodeRequest.parse(buffer);

		return request;
	}

	// Main method for handling actions from the client.
	public void getAction() {
		try {
			RobocodeRequest request = processRequest();
			sendResponse(agentCommunicator.generateInstruction(request));

		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	// Closes the server socket.
	public void close() throws IOException {
		welcomeSocket.close();
	}

	// The main method can be used for any additional logic if needed.
	public static void main(String argv[]) throws IOException, InterruptedException {
	}
}
