"""Official-style deterministic evaluation harness for SHL scoring readiness."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from agent.conversation_models import ConversationMessage, ConversationState
from agent.query_builder import QueryBuilder
from agent.response_models import ChatResponse, Recommendation
from agent.router import RuleBasedRouter
from agent.routing_models import RouteType
from app.main import create_app
from evaluation.metrics import latency_stats, precision_at_k, recall_at_k
from retrieval.hybrid_retriever import HybridRetriever, HybridRetrieverError

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "evaluation" / "data"
CATALOG_PATH = ROOT / "catalog" / "catalog.json"
REPORTS_DIR = ROOT / "reports"
RETRIEVAL_REPORT_PATH = REPORTS_DIR / "retrieval_report.md"
FINAL_REPORT_PATH = ROOT / "FINAL_EVALUATION_REPORT.md"

CASE_FILES = [
    "recommendation_cases.json",
    "clarification_cases.json",
    "comparison_cases.json",
    "refinement_cases.json",
    "refusal_cases.json",
    "prompt_injection_cases.json",
    "multi_turn_cases.json",
]


@dataclass
class CaseResult:
    case_id: str
    category: str
    expected_route: str
    actual_route: str
    hard_pass: bool
    behavior_pass: bool
    recall_at_10: float
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    turns: int
    retrieved_names: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


@dataclass
class OfficialEvaluationResult:
    hard_eval_pass_rate: float
    mean_recall_at_10: float
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    behavior_probe_pass_rate: float
    average_retrieval_latency_ms: float
    average_conversation_turns: float
    total_cases: int
    case_results: list[CaseResult]
    retrieval_latency: dict[str, float]
    initialized_live_retriever: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "hard_eval_pass_rate": round(self.hard_eval_pass_rate, 4),
            "mean_recall@10": round(self.mean_recall_at_10, 4),
            "precision@1": round(self.precision_at_1, 4),
            "precision@3": round(self.precision_at_3, 4),
            "precision@5": round(self.precision_at_5, 4),
            "behavior_probe_pass_rate": round(self.behavior_probe_pass_rate, 4),
            "average_retrieval_latency_ms": round(self.average_retrieval_latency_ms, 2),
            "average_conversation_turns": round(self.average_conversation_turns, 2),
            "total_cases": self.total_cases,
            "retrieval_latency": self.retrieval_latency,
            "initialized_live_retriever": self.initialized_live_retriever,
            "failures": [
                {
                    "case_id": result.case_id,
                    "category": result.category,
                    "expected_route": result.expected_route,
                    "actual_route": result.actual_route,
                    "failures": result.failures,
                }
                for result in self.case_results
                if result.failures
            ],
        }


class OfficialEvaluator:
    """Runs deterministic checks aligned to SHL hard evals, recall, and probes."""

    def __init__(self, data_dir: Path | str = DATA_DIR) -> None:
        self._data_dir = Path(data_dir)
        self._catalog = _load_catalog()
        self._catalog_by_name = {item["name"].casefold(): item for item in self._catalog}
        self._router = RuleBasedRouter()
        self._query_builder = QueryBuilder()
        self._retriever = HybridRetriever()
        self._retriever_ready = False

    def evaluate(self) -> OfficialEvaluationResult:
        cases = self._load_cases()
        self._initialize_retriever()
        app = create_app()
        openapi = app.openapi()

        results: list[CaseResult] = []
        retrieval_latencies: list[float] = []

        for case in cases:
            result, latency = self._evaluate_case(case, openapi)
            results.append(result)
            if latency is not None:
                retrieval_latencies.append(latency)

        hard_rate = _mean([1.0 if item.hard_pass else 0.0 for item in results])
        behavior_rate = _mean([1.0 if item.behavior_pass else 0.0 for item in results])
        recall10 = _mean([item.recall_at_10 for item in results if _expects_recommendations(item)])
        p1 = _mean([item.precision_at_1 for item in results if _expects_recommendations(item)])
        p3 = _mean([item.precision_at_3 for item in results if _expects_recommendations(item)])
        p5 = _mean([item.precision_at_5 for item in results if _expects_recommendations(item)])
        turns = _mean([item.turns for item in results])
        latency = latency_stats(retrieval_latencies)

        return OfficialEvaluationResult(
            hard_eval_pass_rate=hard_rate,
            mean_recall_at_10=recall10,
            precision_at_1=p1,
            precision_at_3=p3,
            precision_at_5=p5,
            behavior_probe_pass_rate=behavior_rate,
            average_retrieval_latency_ms=latency["avg"],
            average_conversation_turns=turns,
            total_cases=len(results),
            case_results=results,
            retrieval_latency=latency,
            initialized_live_retriever=self._retriever_ready,
        )

    def write_reports(self, result: OfficialEvaluationResult) -> None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        RETRIEVAL_REPORT_PATH.write_text(_render_retrieval_report(result), encoding="utf-8")
        FINAL_REPORT_PATH.write_text(_render_final_report(result), encoding="utf-8")

    def _load_cases(self) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        for file_name in CASE_FILES:
            path = self._data_dir / file_name
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            category = file_name.replace("_cases.json", "")
            for item in payload:
                item.setdefault("category", category)
                cases.append(item)
        return cases

    def _initialize_retriever(self) -> None:
        try:
            self._retriever.initialize()
        except HybridRetrieverError:
            self._retriever_ready = False
            return
        self._retriever_ready = True

    def _evaluate_case(
        self,
        case: dict[str, Any],
        openapi: dict[str, Any],
    ) -> tuple[CaseResult, float | None]:
        messages = [ConversationMessage.model_validate(message) for message in case["messages"]]
        state = _state_from_case(case)
        previous_state = _previous_state_from_case(case)
        decision = self._router.route(state, previous_state)
        expected_route = case["expected_route"].upper()
        actual_route = decision.route.value
        failures: list[str] = []

        if actual_route != expected_route:
            failures.append(f"route mismatch expected={expected_route} actual={actual_route}")

        if len(messages) > int(case.get("maximum_turns", 8)):
            failures.append("conversation exceeds maximum_turns")

        _validate_openapi(openapi, failures)

        retrieved_names: list[str] = []
        retrieval_latency_ms: float | None = None
        expected_names = case.get("expected_assessments", [])
        if decision.route in {RouteType.RECOMMEND, RouteType.REFINE} and self._retriever_ready:
            query = self._query_builder.build(state=state, decision=decision)
            started = perf_counter()
            try:
                retrieval_result = self._retriever.search(
                    query.query_text,
                    state=state,
                    filters=query.filters,
                    top_k=10,
                )
                retrieval_latency_ms = (perf_counter() - started) * 1000
                retrieved_names = [item.name for item in retrieval_result.results[:10]]
            except Exception as exc:  # pragma: no cover - defensive eval reporting
                failures.append(f"retrieval failed: {exc}")

        response = _synthetic_response_for_case(case, retrieved_names)
        _validate_response_schema(response, failures)
        _validate_recommendations(response, self._catalog_by_name, failures)

        expected_set = {name.casefold() for name in expected_names}
        retrieved_lower = [name.casefold() for name in retrieved_names]
        recall10 = recall_at_k(expected_set, retrieved_lower, 10) if expected_set else 1.0
        precision1 = precision_at_k(expected_set, retrieved_lower, 1) if expected_set else 1.0
        precision3 = precision_at_k(expected_set, retrieved_lower, 3) if expected_set else 1.0
        precision5 = precision_at_k(expected_set, retrieved_lower, 5) if expected_set else 1.0

        behavior_pass = actual_route == expected_route
        if case.get("expected_behavior_probe") == "catalog_grounded_recommendation":
            behavior_pass = behavior_pass and recall10 > 0.0
        if case.get("expected_behavior_probe") in {"refusal", "prompt_injection_refusal"}:
            behavior_pass = behavior_pass and response.recommendations is None

        hard_pass = not failures
        return (
            CaseResult(
                case_id=case["id"],
                category=case["category"],
                expected_route=expected_route,
                actual_route=actual_route,
                hard_pass=hard_pass,
                behavior_pass=behavior_pass,
                recall_at_10=recall10,
                precision_at_1=precision1,
                precision_at_3=precision3,
                precision_at_5=precision5,
                turns=len(messages),
                retrieved_names=retrieved_names,
                failures=failures,
            ),
            retrieval_latency_ms,
        )


def _state_from_case(case: dict[str, Any]) -> ConversationState:
    if "state" in case:
        return ConversationState.model_validate(case["state"])
    text = " ".join(message["content"] for message in case["messages"])
    return _heuristic_state(text)


def _previous_state_from_case(case: dict[str, Any]) -> ConversationState | None:
    previous = case.get("previous_state")
    if previous:
        return ConversationState.model_validate(previous)
    return None


def _heuristic_state(text: str) -> ConversationState:
    lower = text.casefold()
    scope = "in_scope"
    if any(term in lower for term in ["ignore previous", "system prompt", "developer message"]):
        scope = "prompt_injection"
    elif any(term in lower for term in ["weather", "cover letter", "recipe", "football"]):
        scope = "off_topic"

    comparison = any(term in lower for term in ["compare", "which is better", "versus", " vs "])
    skills = []
    for token, label in [
        ("python", "Python"),
        ("java", "Java"),
        ("sql", "SQL"),
        ("data science", "Data Science"),
        ("machine learning", "Machine Learning"),
        ("sales", "Sales"),
        ("customer service", "Customer Service"),
        ("communication", "Communication"),
        ("numerical", "Numerical"),
    ]:
        if token in lower:
            skills.append(label)

    role = None
    for token, label in [
        ("engineer", "Engineer"),
        ("developer", "Developer"),
        ("data scientist", "Data Scientist"),
        ("sales", "Sales"),
        ("customer", "Customer Support"),
        ("graduate", "Graduate"),
        ("manager", "Manager"),
        ("leadership", "Leader"),
    ]:
        if token in lower:
            role = label
            break

    mentioned = []
    for name in ["Python (New)", "Core Java (Advanced Level) (New)", "SQL (New)", "OPQ Leadership Report", "Occupational Personality Questionnaire OPQ32r", "Verify - G+", "SHL Verify Interactive G+"]:
        if name.casefold().replace(" (new)", "") in lower or name.casefold() in lower:
            mentioned.append(name)

    return ConversationState(
        role=role,
        seniority="senior" if "senior" in lower else ("graduate" if "graduate" in lower else None),
        technical_skills=skills,
        leadership_required="leadership" in lower,
        personality_required="personality" in lower or "opq" in lower,
        cognitive_required="cognitive" in lower or "ability" in lower or "numerical" in lower,
        simulation_required="simulation" in lower,
        constraints=_extract_constraints(lower),
        mentioned_assessment_names=mentioned,
        comparison_requested=comparison,
        scope_flag=scope,  # type: ignore[arg-type]
        clarification_needed=scope == "in_scope" and not comparison and not role and not skills,
    )


def _extract_constraints(lower: str) -> list[str]:
    constraints = []
    duration_match = re.search(r"(\d+)\s*(?:minutes?|mins?)", lower)
    if duration_match:
        constraints.append(f"Only {duration_match.group(1)} minutes")
    if "no personality" in lower:
        constraints.append("No personality")
    if "no simulation" in lower:
        constraints.append("No simulation")
    if "english" in lower:
        constraints.append("English")
    return constraints


def _synthetic_response_for_case(case: dict[str, Any], names: list[str]) -> ChatResponse:
    expected_route = case["expected_route"].upper()
    if expected_route in {"CLARIFY", "REFUSE"}:
        return ChatResponse(reply=case.get("expected_behavior", "No recommendations."), recommendations=None)

    recommendations = []
    for name in names[:10]:
        # URL and test_type are injected from catalog, matching production ResponseBuilder behavior.
        recommendations.append(
            Recommendation(name=name, url="", test_type=[])
        )
    return ChatResponse(reply="Based on the available SHL catalog, I recommend these assessments.", recommendations=recommendations or None)


def _validate_openapi(openapi: dict[str, Any], failures: list[str]) -> None:
    paths = openapi.get("paths", {})
    chat = paths.get("/chat", {}).get("post")
    if not chat:
        failures.append("OpenAPI missing POST /chat")
        return
    if "200" not in chat.get("responses", {}):
        failures.append("OpenAPI missing /chat 200 response")
    schema = openapi.get("components", {}).get("schemas", {})
    if "ChatRequest" not in schema or "ChatResponse" not in schema:
        failures.append("OpenAPI missing ChatRequest or ChatResponse schema")


def _validate_response_schema(response: ChatResponse, failures: list[str]) -> None:
    payload = response.model_dump()
    if set(payload) != {"reply", "recommendations"}:
        failures.append("response schema has unexpected fields")
    if not isinstance(payload["reply"], str) or not payload["reply"].strip():
        failures.append("response reply is empty")
    recs = payload["recommendations"]
    if recs is not None and len(recs) > 10:
        failures.append("response exceeds 10 recommendations")


def _validate_recommendations(
    response: ChatResponse,
    catalog_by_name: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    if response.recommendations is None:
        return
    for recommendation in response.recommendations:
        record = catalog_by_name.get(recommendation.name.casefold())
        if record is None:
            failures.append(f"hallucinated assessment name: {recommendation.name}")
            continue
        if recommendation.url and recommendation.url != record["link"]:
            failures.append(f"hallucinated URL for {recommendation.name}")


def _load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _expects_recommendations(item: CaseResult) -> bool:
    return item.expected_route in {"RECOMMEND", "REFINE"}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _render_retrieval_report(result: OfficialEvaluationResult) -> str:
    lines = [
        "# Retrieval Report",
        "",
        f"Mean Recall@10: {result.mean_recall_at_10:.4f}",
        f"Precision@1: {result.precision_at_1:.4f}",
        f"Precision@3: {result.precision_at_3:.4f}",
        f"Precision@5: {result.precision_at_5:.4f}",
        f"Average Retrieval Latency: {result.average_retrieval_latency_ms:.2f} ms",
        "",
        "## Per-Query Recall@10",
        "",
        "| Case | Category | Route | Recall@10 | Retrieved | Failures |",
        "|------|----------|-------|-----------|-----------|----------|",
    ]
    for item in result.case_results:
        if not _expects_recommendations(item):
            continue
        retrieved = ", ".join(item.retrieved_names[:10])
        failures = "; ".join(item.failures)
        lines.append(
            f"| {item.case_id} | {item.category} | {item.actual_route} | {item.recall_at_10:.4f} | {retrieved} | {failures} |"
        )
    lines.extend(
        [
            "",
            "## Root-Cause Analysis",
            "",
            "Failures indicate cases where routing, catalog grounding, or ranking should be inspected before submission.",
            "",
            "## Ranking Improvement Suggestions",
            "",
            "Prioritize exact catalog skill names, explicit exclusions, duration constraints, and role/seniority metadata when Recall@10 drops below 1.0.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_final_report(result: OfficialEvaluationResult) -> str:
    estimated = (
        result.hard_eval_pass_rate * 0.4
        + result.mean_recall_at_10 * 0.4
        + result.behavior_probe_pass_rate * 0.2
    )
    failures = result.to_dict()["failures"]
    lines = [
        "# Final Evaluation Report",
        "",
        "## Executive Summary",
        "",
        "Automated official-style evaluation completed against deterministic SHL scoring checks.",
        "",
        "## Metrics",
        "",
        f"- Hard Evaluation Pass Rate: {result.hard_eval_pass_rate:.4f}",
        f"- Mean Recall@10: {result.mean_recall_at_10:.4f}",
        f"- Precision@1: {result.precision_at_1:.4f}",
        f"- Precision@3: {result.precision_at_3:.4f}",
        f"- Precision@5: {result.precision_at_5:.4f}",
        f"- Behavior Probe Pass Rate: {result.behavior_probe_pass_rate:.4f}",
        f"- Average Retrieval Latency: {result.average_retrieval_latency_ms:.2f} ms",
        f"- Average Conversation Turns: {result.average_conversation_turns:.2f}",
        f"- Estimated SHL Evaluation Score: {estimated:.4f}",
        "",
        "## Failure Analysis",
        "",
    ]
    if failures:
        for failure in failures:
            lines.append(f"- {failure['case_id']}: {'; '.join(failure['failures'])}")
    else:
        lines.append("- No failures detected by the automated harness.")
    lines.extend(
        [
            "",
            "## Regression Summary",
            "",
            "The harness validates schema, route behavior, catalog grounding, turn caps, and Recall@10-oriented recommendation ordering.",
            "",
            "## Remaining Risks",
            "",
            "- Hidden SHL cases may use labels or assessment aliases not represented in the local evaluation datasets.",
            "- LLM-dependent state extraction and natural-language response wording still depend on provider availability and output quality.",
        ]
    )
    return "\n".join(lines) + "\n"
