package cz.vutbr.feec.robocode.socket;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.Socket;

import cz.vutbr.feec.robocode.protocol.RobocodeRequest;
import cz.vutbr.feec.robocode.protocol.RobocodeResponse;
import it.rmarcello.protocol.exception.ProtocolException;

public class TCPClientSocket {

	private final Socket clientSocket;
	private final DataOutputStream outToServer;
	private final DataInputStream inFromServer;

	public TCPClientSocket(String address, int port) throws IOException {
		System.out.println("Connecting");
		clientSocket = new Socket(address, port);
		outToServer = new DataOutputStream(clientSocket.getOutputStream());
		inFromServer = new DataInputStream(clientSocket.getInputStream());
	}

	public void sendRequest(RobocodeRequest request) throws IOException, ProtocolException {
		outToServer.write(request.toByteArray());
		outToServer.flush();
	}

	public RobocodeResponse processResponse() throws IOException, ProtocolException {
		byte[] buffer = new byte[2048];
		inFromServer.read(buffer);
		RobocodeResponse response = RobocodeResponse.parse(buffer);
		return response;

	}

	public RobocodeResponse getAction(RobocodeRequest robocodeRequest) {
		RobocodeResponse response = new RobocodeResponse(0, 0, 0, 0);
		try {
			sendRequest(robocodeRequest);
			response = processResponse();

		} catch (Exception e) {
			e.printStackTrace();
		}

		return response;
	}

	public void close() throws IOException {
		clientSocket.close();
	}

	public static void main(String argv[]) throws IOException {
	}
}
