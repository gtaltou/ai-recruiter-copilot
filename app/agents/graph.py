from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from app.schemas.cv import CV
from app.schemas.job_description import JobDescription
from app.schemas.evaluation_report import EvaluationReport
from app.agents.sourcing_agent import SourcingAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.report_agent import ReportAgent
import logging

logger = logging.getLogger(__name__)

# === État du graphe ===
class GraphState(TypedDict):
    cv: Optional[CV]
    jd: Optional[JobDescription]
    match_result: Optional[dict]
    evaluation_result: Optional[dict]
    report: Optional[dict]
    error: Optional[str]

# === Init agents ===
sourcing_agent = SourcingAgent()
evaluation_agent = EvaluationAgent()
report_agent = ReportAgent()

# === Noeuds du graphe ===
async def node_sourcing(state: GraphState) -> GraphState:
    """Étape 1 : Analyse du match CV ↔ JD."""
    logger.info("🔍 Agent Sourcing : analyse du match...")
    match = await sourcing_agent.evaluate_match(state["cv"], state["jd"])
    state["match_result"] = match
    return state

async def node_evaluation(state: GraphState) -> GraphState:
    """Étape 2 : Évaluation détaillée du candidat."""
    logger.info("📊 Agent Évaluation : évaluation en cours...")
    evaluation = await evaluation_agent.evaluate(
        state["cv"], state["jd"], state["match_result"]
    )
    state["evaluation_result"] = evaluation
    return state

async def node_report(state: GraphState) -> GraphState:
    """Étape 3 : Génération du rapport final."""
    logger.info("📝 Agent Rapport : génération du rapport...")
    report = await report_agent.generate_report(
        state["match_result"], state["evaluation_result"]
    )
    state["report"] = report
    return state

def should_continue(state: GraphState) -> str:
    """Vérifie s'il faut continuer ou arrêter en cas d'erreur."""
    if state.get("error"):
        return "end"
    return "continue"

# === Construction du graphe ===
workflow = StateGraph(GraphState)

workflow.add_node("sourcing", node_sourcing)
workflow.add_node("evaluation", node_evaluation)
workflow.add_node("report", node_report)

workflow.set_entry_point("sourcing")
workflow.add_conditional_edges(
    "sourcing",
    should_continue,
    {"continue": "evaluation", "end": END},
)
workflow.add_conditional_edges(
    "evaluation",
    should_continue,
    {"continue": "report", "end": END},
)
workflow.add_edge("report", END)

# Compilation
app_graph = workflow.compile()

async def run_pipeline(cv: CV, jd: JobDescription) -> dict:
    """Point d'entrée : exécute le pipeline complet."""
    initial_state: GraphState = {
        "cv": cv,
        "jd": jd,
        "match_result": None,
        "evaluation_result": None,
        "report": None,
        "error": None,
    }
    final_state = await app_graph.ainvoke(initial_state)

    if final_state.get("error"):
        raise RuntimeError(f"Pipeline échoué : {final_state['error']}")

    return report_agent.format_for_api(
        final_state["report"],
        cv_id=cv.email or "unknown",
        jd_id=jd.titre,
    )
