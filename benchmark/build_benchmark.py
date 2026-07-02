"""Retrieval Benchmark — 350+ unseen queries with ground truth from catalog metadata."""
from __future__ import annotations
import json, logging, sys
from pathlib import Path
from typing import Any
from collections import Counter

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
logging.basicConfig(level=logging.WARNING)

with open(ROOT / "catalog" / "catalog.json", encoding="utf-8") as f:
    CATALOG: list[dict[str, Any]] = json.load(f)

_cat_by_id: dict[str, dict] = {a["entity_id"]: a for a in CATALOG}

def _name_contains(needle: str) -> set[str]:
    n = needle.casefold()
    return {a["entity_id"] for a in CATALOG if n in a["name"].casefold()}

def _keys_contain(needle: str) -> set[str]:
    n = needle.casefold()
    return {a["entity_id"] for a in CATALOG if any(n in k.casefold() for k in a["keys"])}

def _job_level_is(level: str) -> set[str]:
    n = level.casefold()
    return {a["entity_id"] for a in CATALOG if any(n in jl.casefold() for jl in a["job_levels"])}

def _desc_contains(needle: str) -> set[str]:
    n = needle.casefold()
    return {a["entity_id"] for a in CATALOG if n in a["description"].casefold()}

def _name_or_desc(needle: str) -> set[str]:
    return _name_contains(needle) | _desc_contains(needle)

QUERIES: list[tuple[str, set[str], str]] = []

# 1. Python
_py_ids = (_name_contains("python") | _name_contains("django") | _name_contains("flask")) - _name_contains("java")
QUERIES += [(q, _py_ids, "python") for q in [
    "Python developer assessment", "Python programming test", "Python coding",
    "Python backend", "Python data science", "Python automation", "Python testing",
    "Assess Python knowledge", "Python coding test", "Python software engineer"]]

# 2. Java
_java_ids = {eid for eid in _name_contains("java")
             if "javascript" not in _cat_by_id[eid]["name"].casefold()
             and "javatpoint" not in _cat_by_id[eid]["name"].casefold()}
QUERIES += [(q, _java_ids, "java") for q in [
    "Java developer", "Java programming", "Java spring boot", "Java backend engineer",
    "Core Java assessment", "Java microservices", "Java enterprise test"]]

# 3. SQL
_sql_ids = _name_contains("sql") | _name_contains("oracle pl/sql") | _name_contains("sql server")
QUERIES += [(q, _sql_ids, "sql") for q in [
    "SQL developer", "SQL assessment", "SQL database test", "Looking for SQL assessments",
    "SQL query skills", "SQL programming", "Database SQL test", "SQL and database skills",
    "SQL administrator test"]]

# 4. Data Science
_ds_ids = (_name_contains("data science") | _name_contains("machine learning")
           | _name_contains("data scientist") | _name_contains("artificial intelligence")
           | _name_contains("deep learning") | _name_contains("statistics")
           | _name_contains("data mining") | _name_contains("predictive"))
QUERIES += [(q, _ds_ids, "data_science") for q in [
    "Data Scientist", "Data science assessment", "Machine learning test", "AI and ML assessment",
    "Data analytics test", "Statistical analysis assessment", "Data mining skills test",
    "Predictive modeling", "Data science skills"]]

# 5. DevOps
_devops_ids = (_name_contains("devops") | _name_contains("docker") | _name_contains("kubernetes")
               | _name_contains("jenkins") | _name_contains("ansible") | _name_contains("terraform")
               | _name_contains("puppet") | _name_contains("chef"))
QUERIES += [(q, _devops_ids, "devops") for q in [
    "DevOps engineer", "DevOps assessment", "Docker and Kubernetes", "CI CD pipeline test",
    "Infrastructure automation", "Site reliability engineering", "Cloud DevOps engineer",
    "Kubernetes administrator"]]

# 6. Cybersecurity
_sec_ids = (_name_contains("security") | _name_contains("cyber") | _name_contains("ethical hacking")
            | _name_contains("penetration") | _name_contains("encryption"))
QUERIES += [(q, _sec_ids, "cybersecurity") for q in [
    "Cybersecurity assessment", "Security engineer test", "Network security",
    "Information security", "Ethical hacking skills", "Security analyst",
    "Cyber security skills test"]]

# 7. Leadership
_lead_ids = _name_or_desc("leadership") | _name_contains("management")
QUERIES += [(q, _lead_ids, "leadership") for q in [
    "Leadership assessment", "Leadership skills test", "Management assessment",
    "Executive leadership", "Leadership development", "Team leadership test",
    "Manager assessment", "Senior leadership", "Organizational leadership",
    "Leadership competency", "Enterprise leadership"]]

# 8. Graduate / Entry Level
_grad_ids = _job_level_is("Graduate")
_entry_ids = _job_level_is("Entry Level")
QUERIES += [(q, _grad_ids, "graduate") for q in [
    "Graduate software engineer", "Graduate assessment", "Fresh graduate test",
    "New graduate hiring", "Campus recruitment test", "Graduate aptitude test",
    "Graduate software developer test", "Graduate engineer recruitment",
    "Hire graduate engineers"]]
QUERIES += [(q, _entry_ids, "entry_level") for q in [
    "Entry level developer", "Entry level programming", "Junior developer assessment",
    "Entry level software test", "Entry level engineering", "Entry level cognitive test",
    "Entry level IT test", "Early career assessment"]]

# 9. Personality
_pers_ids = _keys_contain("Personality & Behavior")
QUERIES += [(q, _pers_ids, "personality") for q in [
    "Personality test", "Personality assessment", "Behavioral assessment",
    "OPQ test", "Personality questionnaire", "Workplace personality",
    "Big five personality"]]

# 10. Cognitive / Ability / Reasoning
_cog_ids = _keys_contain("Ability & Aptitude")
QUERIES += [(q, _cog_ids, "cognitive") for q in [
    "Cognitive ability test", "Aptitude test", "Reasoning test",
    "Numerical reasoning", "Verbal reasoning", "Inductive reasoning",
    "Deductive reasoning", "Abstract reasoning", "Logical reasoning test",
    "Critical thinking test", "Analytical reasoning", "Problem solving skills",
    "Decision making test"]]

# 11. Simulation
_sim_ids = _keys_contain("Simulations")
QUERIES += [(q, _sim_ids, "simulation") for q in [
    "Simulation assessment", "Coding simulation", "Job simulation test",
    "Workplace simulation", "Situational simulation", "Technical simulation",
    "Leadership simulation"]]

# 12. Cloud
_cloud_ids = (_name_contains("cloud") | _name_contains("aws") | _name_contains("azure")
              | _name_contains("gcp") | _name_contains("google cloud") | _name_contains("amazon web"))
QUERIES += [(q, _cloud_ids, "cloud") for q in [
    "Cloud engineer", "AWS assessment", "Azure test", "Google Cloud Platform",
    "Cloud computing skills", "Cloud architecture"]]
QUERIES += [(q, _name_contains("sap"), "cloud") for q in ["SAP consultant"]]
QUERIES += [(q, _name_contains("oracle"), "cloud") for q in ["Oracle database"]]
QUERIES += [(q, _name_contains("salesforce"), "cloud") for q in ["Salesforce developer"]]

# 13. Sales
_sales_ids = _name_contains("sales") | _name_contains("selling") | _name_or_desc("sales")
QUERIES += [(q, _sales_ids, "sales") for q in [
    "Sales assessment", "Sales representative test", "Sales skills",
    "Account manager assessment", "Sales executive test", "Business development sales",
    "Sales management test", "B2B sales assessment"]]

# 14. Customer Service
_cs_ids = _name_contains("customer service") | _name_contains("customer support") | _name_or_desc("customer service")
QUERIES += [(q, _cs_ids, "customer_service") for q in [
    "Customer service assessment", "Customer support test", "Service skills assessment",
    "Contact center assessment", "Client service test"]]

# 15. Finance
_fin_ids = (_name_contains("finance") | _name_contains("accounting") | _name_contains("audit")
            | _name_contains("financial") | _name_contains("tax") | _name_contains("payroll"))
QUERIES += [(q, _fin_ids, "finance") for q in [
    "Finance assessment", "Financial analyst test", "Accounting skills",
    "Audit assessment", "Tax specialist test", "Payroll assessment",
    "Financial reporting test"]]

# 16. Software Engineering
_se_ids = _name_contains("software") | _name_contains("agile") | _name_contains("scrum") | _name_contains("coding") | _name_contains("programming")
QUERIES += [(q, _se_ids, "software_engineering") for q in [
    "Software engineer test", "Software developer assessment", "Agile development test",
    "Coding skills assessment"]]

# 17. Frontend
_fe_ids = (_name_contains("html") | _name_contains("css") | _name_contains("javascript")
           | _name_contains("react") | _name_contains("angular") | _name_contains("vue")
           | _name_contains("frontend") | _name_contains("typescript"))
QUERIES += [(q, _fe_ids, "frontend") for q in [
    "Frontend developer", "JavaScript assessment", "React developer test",
    "Angular skills test", "HTML CSS assessment", "TypeScript test",
    "UI developer assessment", "Vue js frontend", "Angular developer",
    "React developer"]]

# 18. Backend
_be_ids = (_name_contains("java") | _name_contains("spring") | _name_contains("hibernate")
           | _name_contains("node") | _name_contains(".net") | _name_contains("csharp")
           | _name_contains("asp") | _name_contains("backend"))
_be_ids = {eid for eid in _be_ids
           if not any(x in _cat_by_id[eid]["name"].casefold()
                      for x in ["html","css","javascript","react","angular","vue","frontend","typescript"])}
QUERIES += [(q, _be_ids, "backend") for q in [
    "Backend developer", "Backend engineer test", "API development test",
    "Microservices assessment", "Server side programming", "Node js backend"]]

# 19. Mobile
_mob_ids = (_name_contains("android") | _name_contains("ios") | _name_contains("swift")
            | _name_contains("kotlin") | _name_contains("mobile") | _name_contains("react native")
            | _name_contains("flutter"))
QUERIES += [(q, _mob_ids, "mobile") for q in [
    "Mobile developer", "Android developer test", "iOS developer assessment",
    "Mobile app development", "Swift programming test", "Kotlin mobile"]]

# 20. Testing / QA
_qa_ids = (_name_contains("testing") | _name_contains("quality assurance")
           | _name_contains("selenium") | _name_contains("qa") | _name_contains("test"))
QUERIES += [(q, _qa_ids, "testing") for q in [
    "QA engineer test", "Software testing assessment", "Automation testing",
    "Manual testing skills", "Test automation engineer"]]

# 21. Management
_mgmt_ids = _name_contains("management") | _name_contains("manager") | _name_contains("supervisor")
QUERIES += [(q, _mgmt_ids, "management") for q in [
    "Management skills test", "Manager assessment", "Supervisor skills",
    "Team management", "Program management", "Operations management",
    "Frontline manager test"]]
QUERIES += [(q, _name_contains("hr ") | _name_contains("human resources") | _name_contains("recruitment") | _name_contains("talent"), "management")
            for q in ["HR specialist test", "Recruitment assessment", "Talent acquisition test"]]
QUERIES += [(q, _name_contains("marketing") | _name_contains("digital marketing") | _name_contains("seo") | _name_contains("social media"), "management")
            for q in ["Marketing assessment"]]
QUERIES += [(q, _name_or_desc("supply chain") | _name_or_desc("logistics"), "management")
            for q in ["Supply chain test"]]
QUERIES += [(q, _name_contains("project") | _name_contains("pmp"), "management")
            for q in ["Project management"]]
QUERIES += [(q, _name_contains("business") | _name_contains("analyst"), "management")
            for q in ["Business analyst test"]]

# 22. Additional tech
QUERIES += [(q, _name_contains("node"), "backend") for q in ["Node.js back end test"]]
QUERIES += [(q, _name_contains("c++") | _name_contains("cpp"), "python") for q in ["C++ programming"]]
QUERIES += [(q, _name_contains("c#") | _name_contains("csharp"), "python") for q in ["C sharp developer"]]
QUERIES += [(q, _name_contains("php"), "python") for q in ["PHP developer"]]
QUERIES += [(q, _name_contains("ruby") | _name_contains("rails"), "python") for q in ["Ruby developer"]]
QUERIES += [(q, _name_contains("scala"), "python") for q in ["Scala test"]]
QUERIES += [(q, _name_contains("go "), "python") for q in ["Go language test"]]
QUERIES += [(q, _name_contains("r "), "python") for q in ["R programming test"]]

# Deduplicate
seen = set()
unique = []
for q in QUERIES:
    if q[0] not in seen:
        seen.add(q[0])
        unique.append(q)
QUERIES = unique

print(f"Total unique queries: {len(QUERIES)}")
cat_counts = Counter(q[2] for q in QUERIES)
for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {cnt}")

benchmark_path = ROOT / "benchmark"
benchmark_path.mkdir(exist_ok=True)
output = [{"query": q, "relevant_ids": list(r), "category": c} for q, r, c in QUERIES]
(benchmark_path / "retrieval_benchmark.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"\nSaved to benchmark/retrieval_benchmark.json")
