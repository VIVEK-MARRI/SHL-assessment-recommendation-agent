import pytest
from agent.router import RuleBasedRouter, InvalidConversationState
from agent.conversation_models import ConversationState
from agent.routing_models import RouteType

@pytest.fixture
def router():
    return RuleBasedRouter()

def test_invalid_conversation_state(router):
    with pytest.raises(InvalidConversationState):
        router.route("Not a state")

def test_refuse_prompt_injection(router):
    state = ConversationState(
        scope_flag="prompt_injection"
    )
    decision = router.route(state)
    assert decision.route == RouteType.REFUSE
    assert decision.next_module == "refusal"
    assert decision.confidence == "HIGH"

def test_refuse_off_topic(router):
    state = ConversationState(
        scope_flag="off_topic"
    )
    decision = router.route(state)
    assert decision.route == RouteType.REFUSE
    assert decision.next_module == "refusal"
    assert decision.confidence == "LOW"

def test_compare(router):
    state = ConversationState(
        comparison_requested=True,
        mentioned_assessment_names=["Test A"]
    )
    decision = router.route(state)
    assert decision.route == RouteType.COMPARE
    assert decision.next_module == "comparison_pipeline"
    assert decision.confidence == "HIGH"

def test_compare_without_assessments_falls_back(router):
    state = ConversationState(
        comparison_requested=True,
        mentioned_assessment_names=[]
    )
    decision = router.route(state)
    # Falls back to CLARIFY because role is missing
    assert decision.route == RouteType.CLARIFY
    assert decision.next_module == "clarification"

def test_clarify_explicit(router):
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python"],
        clarification_needed=True
    )
    decision = router.route(state)
    assert decision.route == RouteType.CLARIFY
    assert decision.next_module == "clarification"
    assert decision.clarification_field == "seniority" # 2nd priority since role is present

def test_clarify_missing_role(router):
    state = ConversationState(
        technical_skills=["Python"]
    )
    decision = router.route(state)
    assert decision.route == RouteType.CLARIFY
    assert decision.next_module == "clarification"
    assert decision.clarification_field == "role"

def test_clarify_missing_skills(router):
    state = ConversationState(
        role="Engineer"
    )
    decision = router.route(state)
    assert decision.route == RouteType.CLARIFY
    assert decision.next_module == "clarification"
    assert decision.clarification_field == "seniority" # priority: role, seniority, tech skills

def test_recommend(router):
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python"]
    )
    decision = router.route(state)
    assert decision.route == RouteType.RECOMMEND
    assert decision.next_module == "query_builder"
    assert decision.confidence == "HIGH"

def test_refine(router):
    previous_state = ConversationState(
        role="Engineer",
        technical_skills=["Python"]
    )
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python", "Java"]
    )
    decision = router.route(state, previous_state)
    assert decision.route == RouteType.REFINE
    assert decision.next_module == "query_builder"
    assert decision.confidence == "HIGH"

def test_priority_order_refuse_over_compare(router):
    state = ConversationState(
        scope_flag="off_topic",
        comparison_requested=True,
        mentioned_assessment_names=["Test A"]
    )
    decision = router.route(state)
    assert decision.route == RouteType.REFUSE

def test_priority_order_compare_over_clarify(router):
    state = ConversationState(
        comparison_requested=True,
        mentioned_assessment_names=["Test A"],
        clarification_needed=True
    )
    decision = router.route(state)
    assert decision.route == RouteType.COMPARE

def test_priority_order_clarify_over_refine(router):
    previous_state = ConversationState(
        role="Engineer",
        technical_skills=["Python"]
    )
    state = ConversationState(
        role="Engineer",
        technical_skills=["Python", "Java"],
        clarification_needed=True
    )
    decision = router.route(state, previous_state)
    assert decision.route == RouteType.CLARIFY

def test_clarification_priority(router):
    # role missing -> role
    assert router.route(ConversationState()).clarification_field == "role"
    
    # role present, seniority missing -> seniority
    assert router.route(ConversationState(role="X")).clarification_field == "seniority"
    
    # role, seniority present, tech skills missing -> technical_skills
    assert router.route(ConversationState(role="X", seniority="Y")).clarification_field == "technical_skills"
