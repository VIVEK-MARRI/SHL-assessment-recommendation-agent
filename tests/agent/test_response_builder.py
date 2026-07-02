import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from agent.response_builder import ResponseBuilder
from agent.response_catalog import ResponseCatalog
from agent.response_models import ChatResponse, Recommendation
from agent.routing_models import RouteType, RoutingDecision
from agent.validator_models import ValidatedGenerationResult


@pytest.fixture
def mock_catalog(tmp_path: Path) -> ResponseCatalog:
    catalog_path = tmp_path / "catalog.json"
    data = [
        {
            "name": "Python Advanced",
            "link": "http://shl.com/python-adv",
            "keys": ["Knowledge & Skills"],
        },
        {
            "name": "Java Basics",
            "link": "http://shl.com/java-basics",
            "keys": ["Ability & Aptitude"],
        },
        {
            "name": "OPQ32r",
            "link": "http://shl.com/opq32r",
            "keys": ["Personality & Behavior"],
        },
    ]
    with catalog_path.open("w") as f:
        json.dump(data, f)
    return ResponseCatalog(catalog_path=catalog_path)


def make_validated(
    validated_names: list[str],
    reply: str = "Here are the results.",
    end_of_conversation: bool = False,
    validation_passed: bool = True,
) -> ValidatedGenerationResult:
    return ValidatedGenerationResult(
        reply=reply,
        validated_names=validated_names,
        invalid_names=[],
        end_of_conversation=end_of_conversation,
        validation_passed=validation_passed,
        validation_errors=[],
    )


def make_decision(route: RouteType) -> RoutingDecision:
    module_map = {
        RouteType.RECOMMEND: "query_builder",
        RouteType.REFINE: "query_builder",
        RouteType.COMPARE: "comparison_pipeline",
        RouteType.CLARIFY: "clarification",
        RouteType.REFUSE: "refusal",
    }
    return RoutingDecision(
        route=route,
        next_module=module_map[route],
        reason="test",
        confidence="HIGH",
    )


def test_recommend_route(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated(["Python Advanced", "Java Basics"])
    decision = make_decision(RouteType.RECOMMEND)

    response = builder.build(validated=validated, decision=decision)

    assert isinstance(response, ChatResponse)
    assert response.reply == "Here are the results."
    assert response.recommendations is not None
    assert len(response.recommendations) == 2
    assert response.recommendations[0].name == "Python Advanced"
    assert response.recommendations[0].url == "http://shl.com/python-adv/"  # catalog normalises to trailing slash
    assert response.recommendations[0].test_type == "K"
    assert response.recommendations[1].name == "Java Basics"


def test_refine_route(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated(["OPQ32r"])
    decision = make_decision(RouteType.REFINE)

    response = builder.build(validated=validated, decision=decision)

    assert response.recommendations is not None
    assert response.recommendations[0].name == "OPQ32r"
    assert response.recommendations[0].test_type == "P"


def test_compare_route(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated(["Python Advanced"])
    decision = make_decision(RouteType.COMPARE)

    response = builder.build(validated=validated, decision=decision)

    assert response.recommendations is not None
    assert len(response.recommendations) == 1


def test_clarify_route_returns_null(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated([], reply="Can you clarify?")
    decision = make_decision(RouteType.CLARIFY)

    response = builder.build(validated=validated, decision=decision)

    assert response.reply == "Can you clarify?"
    assert response.recommendations is None


def test_refuse_route_returns_null(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated([], reply="I cannot help with that.")
    decision = make_decision(RouteType.REFUSE)

    response = builder.build(validated=validated, decision=decision)

    assert response.reply == "I cannot help with that."
    assert response.recommendations is None


def test_empty_validated_names_returns_null(mock_catalog: ResponseCatalog) -> None:
    """Even on RECOMMEND route, zero validated names → null recommendations."""
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated([])
    decision = make_decision(RouteType.RECOMMEND)

    response = builder.build(validated=validated, decision=decision)

    assert response.recommendations is None


def test_ordering_preserved(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    validated = make_validated(["OPQ32r", "Python Advanced", "Java Basics"])
    decision = make_decision(RouteType.RECOMMEND)

    response = builder.build(validated=validated, decision=decision)

    names = [r.name for r in response.recommendations]
    assert names == ["OPQ32r", "Python Advanced", "Java Basics"]


def test_recommendation_limit(tmp_path: Path) -> None:
    """Max 10 recommendations enforced."""
    catalog_path = tmp_path / "catalog.json"
    data = [
        {
            "name": f"Assessment {i}",
            "link": f"http://shl.com/{i}",
            "keys": ["Knowledge & Skills"],
        }
        for i in range(1, 16)
    ]
    with catalog_path.open("w") as f:
        json.dump(data, f)
    catalog = ResponseCatalog(catalog_path=catalog_path)

    builder = ResponseBuilder(catalog=catalog)
    validated = make_validated([f"Assessment {i}" for i in range(1, 16)])
    decision = make_decision(RouteType.RECOMMEND)

    response = builder.build(validated=validated, decision=decision)

    assert response.recommendations is not None
    assert len(response.recommendations) == 10


def test_reply_never_modified(mock_catalog: ResponseCatalog) -> None:
    builder = ResponseBuilder(catalog=mock_catalog)
    original_reply = "This is the original reply."
    validated = make_validated(["Python Advanced"], reply=original_reply)
    decision = make_decision(RouteType.RECOMMEND)

    response = builder.build(validated=validated, decision=decision)

    assert response.reply == original_reply
