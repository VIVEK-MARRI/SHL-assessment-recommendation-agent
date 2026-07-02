"""Extend the benchmark to 350+ queries."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from collections import Counter

ROOT = Path.cwd()
with open(ROOT / "catalog" / "catalog.json", encoding="utf-8") as f:
    CATALOG: list[dict[str, Any]] = json.load(f)

_cat_by_id: dict[str, dict] = {a["entity_id"]: a for a in CATALOG}

def _name(needle: str) -> set[str]:
    n = needle.casefold()
    return {a["entity_id"] for a in CATALOG if n in a["name"].casefold()}

def _keys(needle: str) -> set[str]:
    n = needle.casefold()
    return {a["entity_id"] for a in CATALOG if any(n in k.casefold() for k in a["keys"])}

def _job(level: str) -> set[str]:
    n = level.casefold()
    return {a["entity_id"] for a in CATALOG if any(n in jl.casefold() for jl in a["job_levels"])}

def _desc(needle: str) -> set[str]:
    n = needle.casefold()
    return {a["entity_id"] for a in CATALOG if n in a["description"].casefold()}

def _nd(needle: str) -> set[str]:
    return _name(needle) | _desc(needle)

# --- Precompute all ID sets ---
_py = (_name("python") | _name("django") | _name("flask")) - _name("java")
_jv = {eid for eid in _name("java") if "javascript" not in _cat_by_id[eid]["name"].casefold() and "javatpoint" not in _cat_by_id[eid]["name"].casefold()}
_sql = _name("sql") | _name("oracle pl/sql") | _name("sql server")
_ds = (_name("data science") | _name("machine learning") | _name("data scientist") | _name("artificial intelligence") | _name("deep learning") | _name("statistics") | _name("data mining") | _name("predictive"))
_do = (_name("devops") | _name("docker") | _name("kubernetes") | _name("jenkins") | _name("ansible") | _name("terraform") | _name("puppet") | _name("chef"))
_cy = (_name("security") | _name("cyber") | _name("ethical hacking") | _name("penetration") | _name("encryption"))
_ld = _nd("leadership") | _name("management")
_grad = _job("Graduate")
_entry = _job("Entry Level")
_pers = _keys("Personality & Behavior")
_cog = _keys("Ability & Aptitude")
_sim = _keys("Simulations")
_cld = (_name("cloud") | _name("aws") | _name("azure") | _name("gcp") | _name("google cloud") | _name("amazon web"))
_sal = _name("sales") | _name("selling") | _nd("sales")
_cs = _name("customer service") | _name("customer support") | _nd("customer service")
_fin = (_name("finance") | _name("accounting") | _name("audit") | _name("financial") | _name("tax") | _name("payroll"))
_mgt = _name("management") | _name("manager") | _name("supervisor")
_fe = (_name("html") | _name("css") | _name("javascript") | _name("react") | _name("angular") | _name("vue") | _name("frontend") | _name("typescript"))
_mob = (_name("android") | _name("ios") | _name("swift") | _name("kotlin") | _name("mobile") | _name("react native") | _name("flutter"))
_qa = (_name("testing") | _name("quality assurance") | _name("selenium") | _name("qa") | _name("test"))
_be = (_name("java") | _name("spring") | _name("hibernate") | _name("node") | _name(".net") | _name("csharp") | _name("asp") | _name("backend"))
_be = {eid for eid in _be if not any(x in _cat_by_id[eid]["name"].casefold() for x in ["html","css","javascript","react","angular","vue","frontend","typescript"])}
_hlth = (_name("medical") | _name("healthcare") | _name("clinical") | _name("nursing") | _name("pharma") | _nd("healthcare") | _name("medication") | _nd("medical"))
_mkt = (_name("marketing") | _name("brand") | _name("campaign") | _name("advertising") | _name("market research") | _name("digital") | _name("content marketing"))
_sc = (_name("logistics") | _name("supply chain") | _name("inventory") | _name("warehouse") | _nd("supply chain"))
_hr = (_name("hr ") | _name("human resources") | _name("recruitment") | _name("talent") | _name("payroll") | _name("benefits"))
_sap = _name("sap")
_orcl = _name("oracle")
_sfdc = _name("salesforce")
_node = _name("node")

Q: list[tuple[str, set[str], str]] = []

def add_group(queries: list[str], ids: set[str], cat: str):
    for q in queries:
        Q.append((q, ids, cat))

# Python
add_group([f"Python test {t}" for t in ["for developers","for data science","for ML","for automation","for API","for scripting","for AI","for ML engineers"]], _py, "python")
add_group(["Python coding challenge","Python developer skill test","Python programming knowledge","Python and SQL test"], _py | _sql, "python")

# Java
add_group([f"Java {t}" for t in ["EE test","developer skills","backend developer","programming challenge","Spring Boot","J2EE","Java 8","Java 11","microservices developer","enterprise java","developer test","coding assessment"]], _jv, "java")

# SQL
add_group([f"SQL {t}" for t in ["server test","query optimization","data analysis","report writing","database design","pl sql test","tsql test","mysql test","postgresql test","database management"]], _sql, "sql")
add_group(["Relational database test","Database skills test"], _sql, "sql")

# Data Science
add_group([f"Data science {t}" for t in ["for ML","for statistics","for analytics","with Python","with R","for big data","for predictive modeling","for AI","for deep learning"]], _ds, "data_science")
add_group(["ML engineer test","Data scientist skills","Machine learning engineer"], _ds, "data_science")

# DevOps
add_group([f"DevOps {t}" for t in ["tools test","pipeline management","container orchestration","cloud infrastructure","automation engine","release management","configuration management"]], _do, "devops")
add_group(["Kubernetes test","Docker container skills","CI CD pipeline","Infrastructure as code"], _do, "devops")

# Cybersecurity
add_group([f"Security {t}" for t in ["operations assessment","analyst test","threat detection","incident response","vulnerability assessment","network protection","data privacy","compliance test","risk assessment"]], _cy, "cybersecurity")
add_group(["SOC analyst skills","Penetration testing"], _cy, "cybersecurity")

# Leadership
add_group([f"{t} assessment" for t in ["Strategic leadership","Change management","Team building","Executive presence","Organizational development","Cross functional","Leader","Agile leadership","Senior leadership","Enterprise leadership"]], _ld, "leadership")
add_group(["Leadership test","Manager assessment","Supervisor test"], _ld, "leadership")

# Graduate
add_group([f"Graduate {t}" for t in ["hiring test","trainee assessment","recruitment drive","technical interview","scholarship test","internship test","apprenticeship test","software developer","engineer test","coding test"]], _grad, "graduate")
add_group(["New grad software engineer","Campus recruitment","Early talent assessment"], _grad, "graduate")

# Entry level
add_group([f"{t} candidate test" for t in ["Entry","Junior","Early career","Beginner","Associate","Fresher"]], _entry, "entry_level")
add_group(["Entry level developer","Junior dev test","Entry level IT"], _entry, "entry_level")

# Personality
add_group([f"Personality {t}" for t in ["profiling","type indicator","strengths","work style","motivational","team fit","cultural fit","styles","preferences","behavioral"]], _pers, "personality")

# Cognitive
add_group([f"{t} ability test" for t in ["Numerical","Verbal","Abstract","Logical","Analytical","Critical","Spatial","Deductive","Inductive","Quantitative"]], _cog, "cognitive")
add_group(["Cognitive test","Aptitude test for recruitment","Mental ability test"], _cog, "cognitive")

# Simulation
add_group([f"Simulation {t}" for t in ["based assessment","exercise","task test","role play","business simulation","technical simulation","coding simulation","leadership simulation"]], _sim, "simulation")

# Cloud
add_group([f"Cloud {t}" for t in ["architect test","developer skills","solution architect","infrastructure engineer","security test","cost management","migration test","computing","platform test"]], _cld, "cloud")

# Sales
add_group([f"Sales {t}" for t in ["team leader test","pipeline management","closing skills","territory management","key account test","lead generation","retail sales","operations","strategy"]], _sal, "sales")

# Customer Service
add_group([f"Customer service {t}" for t in ["representative test","support skills","complaint handling","client relations","communication test","call center test","help desk test","experience test"]], _cs, "customer_service")

# Finance
add_group([f"{t} test" for t in ["Investment","Risk management","Financial planning","Portfolio management","Corporate finance","Management accounting","Cost accounting","Financial analysis"]], _fin, "finance")

# Management
add_group([f"{t} assessment" for t in ["Mid level manager","Senior management","Supervisory skills","Shift manager","Department head","Team lead skills","Executive management"]], _mgt, "management")
add_group([f"Product {t}" for t in ["management test","owner assessment"]], _name("product") | _name("product manager"), "management")
add_group([f"Project manager test","Program manager test"], _name("project") | _name("pmp"), "management")

# Frontend
add_group([f"{t} test" for t in ["CSS skills","Responsive design","Web development","React hooks","Angular components","Vue components","JavaScript ES6","Frontend performance","Web accessibility","Frontend developer"]], _fe, "frontend")

# Mobile
add_group([f"{t} test" for t in ["iOS Swift","Android Kotlin","Cross platform","Flutter development","React Native","Mobile experience","Mobile engineer"]], _mob, "mobile")

# Testing / QA
add_group([f"{t} test" for t in ["QA analyst","Test case design","Integration testing","User acceptance","Performance testing","Load testing","Security testing","Regression testing"]], _qa, "testing")

# Backend
add_group([f"{t} test" for t in ["REST API","GraphQL","Database backend","Enterprise integration","Backend scalability","Server development"]], _be, "backend")

# Healthcare
add_group([f"{t} assessment" for t in ["Healthcare","Medical","Clinical research","Pharmaceutical","Nursing","Health"]], _hlth, "testing")

# Marketing
add_group([f"{t} test" for t in ["Digital marketing","Content marketing","Brand management","Market research","Growth marketing","Marketing analytics","SEO test"]], _mkt, "management")

# Supply Chain
add_group([f"{t} test" for t in ["Supply chain","Logistics","Inventory management","Procurement","Vendor management","Distribution","Warehouse"]], _sc, "management")

# HR
add_group([f"{t} test" for t in ["HR management","People operations","Workforce planning","Compensation analysis","Employee engagement","HR skills"]], _hr, "management")

# Misc domain
add_group(["Analytical skills","Critical thinking","Attention to detail","Problem solving"], _cog, "cognitive")
add_group(["Communication skills","Interpersonal skills","Negotiation skills","Time management","Teamwork test"], _pers, "personality")
add_group(["Training needs assessment","Learning assessment"], _pers | _cog, "personality")

# Technical contamination - test that Python queries return Python results
add_group(["Python test","Python skills assessment","Python programming knowledge test","Python coding test"], _py, "python")
add_group(["Java test","Java development skills","Java programming test"], _jv, "java")

# Constraint queries
add_group(["Technical test under 20 minutes","Short technical test","Fast coding test"], _py | _jv | _sql, "python")
add_group(["Cognitive test without personality","Reasoning test only"], _cog, "cognitive")

# Enterprise
add_group(["SAP consultant test","Oracle database test","Salesforce developer test","Enterprise software test"], _sap | _orcl | _sfdc, "cloud")

# ERP
add_group([f"{t} test" for t in ["SAP FICO","SAP HCM","SAP ABAP","Oracle EBS","Microsoft Dynamics"]], _sap | _orcl | _name("dynamics"), "cloud")

# Node.js
add_group(["Node.js back end test","Node developer assessment","Express.js test"], _node, "backend")

# Deduplicate
existing = json.loads((ROOT / "benchmark" / "retrieval_benchmark.json").read_text(encoding="utf-8"))
existing_texts = {e["query"] for e in existing}
all_q: dict[str, tuple[str, set[str], str]] = {}
for e in existing:
    all_q[e["query"]] = (e["query"], set(e["relevant_ids"]), e["category"])
for q, r, c in Q:
    if q not in existing_texts:
        all_q[q] = (q, r, c)

unique = list(all_q.values())
print(f"Total unique queries: {len(unique)}")
cat_counts = Counter(q[2] for q in unique)
for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {cnt}")

output = [{"query": q, "relevant_ids": list(r), "category": c} for q, r, c in unique]
(ROOT / "benchmark" / "retrieval_benchmark.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"\nSaved to benchmark/retrieval_benchmark.json")
