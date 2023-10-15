package cz.vutbr.feec.robocode.battle;

import robocode.BattleResults;
import robocode.control.events.BattleAdaptor;
import robocode.control.events.BattleCompletedEvent;
import robocode.control.events.BattleErrorEvent;
import robocode.control.events.BattleFinishedEvent;
import robocode.control.events.BattleMessageEvent;
import robocode.control.events.BattleStartedEvent;
import robocode.control.events.RoundEndedEvent;
import sample.RobotClient;

public class BattleObserver extends BattleAdaptor {

	private BattleResults[] results;

	public void onBattleStarted(BattleStartedEvent e) {
		System.out.println("-- Battle was started --");
	}

	public void onBattleFinished(BattleFinishedEvent e) {
		if (e.isAborted()) {
			System.out.println("-- Battle was aborted --");
		} else {
			System.out.println("-- Battle was finished succesfully --");
		}
	}

	public void onBattleCompleted(BattleCompletedEvent e) {
		System.out.println("-- Battle has completed --");
		this.results = e.getSortedResults();
		// Print out the sorted results with the robot names
		System.out.println("\n-- Battle results --");
		for (BattleResults result : e.getSortedResults()) {
			System.out.println("  " + result.getTeamLeaderName() + ": " + result.getScore());
		}
		RobotClient.counter = 1; // reset counter
	}

	public void onBattleMessage(BattleMessageEvent e) {
		System.out.println("Msg> " + e.getMessage()); //TODO odstraneno
	}

	public void onBattleError(BattleErrorEvent e) {
		System.out.println("Err> " + e.getError());
	}

	@Override
	public void onRoundEnded(RoundEndedEvent event) {
		super.onRoundEnded(event);
		RobotClient.counter = 1; // reset tank counter each game
	}

	public BattleResults[] getResults() {
		return results;
	}

	public void setResults(BattleResults[] results) {
		this.results = results;
	}
}