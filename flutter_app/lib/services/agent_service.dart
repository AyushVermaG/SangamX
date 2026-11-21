import '../models/agent.dart';

abstract class AgentService {
  List<AgentInfo> getInitialAgents();
  Stream<List<AgentInfo>> runAnalysisSimulation(String problem);
  String getFinalSynthesis(String problem);
}
