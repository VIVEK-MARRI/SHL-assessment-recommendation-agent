"""
Full-coverage benchmark generator.
Reads catalog.json, generates multiple natural-language query formulations per assessment,
writes benchmark/full_coverage_benchmark.json.
"""
import json
import re
import os

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "catalog", "catalog.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "full_coverage_benchmark.json")

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    catalog = json.load(f)

SUFFIX_PATTERN = re.compile(
    r"(?:\s*[-–—]\s*)?(Test|Assessment|Measure|Questionnaire|Inventory"
    r"|Report|Profile|Scale|Solution|Simulation)(?:\s+\d+(?:\.\d+)?)?$",
    re.IGNORECASE,
)

VERSION_PATTERN = re.compile(
    r"\s*[([](New|R\d+|U\.S\.|U\.K\.|UK|US|US\s*\(R\d+\)|U\.K\."
    r"|adaptive|General|Australia|AUS|Castilian|European|North American"
    r"|Canadian|Indian Accent|Entry Level|Advanced Level|Intermediate Level"
    r"|Developer|Architecture)\s*[)\]]?\s*",
    re.IGNORECASE,
)

VERSION_SUFFIX_PATTERN = re.compile(
    r"\s+v\d+(?:\.\d+)?(?:\s*-\s*\w+)?$|\s+\d+\.\d+(?:\s*-\s*\w+)?$|\s+[(]?\d+(?:\))?$",
    re.IGNORECASE,
)

PAREN_CLEANUP = re.compile(r"\s*\([^)]*\)\s*")

ABBREVIATIONS = {
    "OPQ": "Occupational Personality Questionnaire",
    "MFS": "Multi-Rater Feedback System",
    "MQ": "Motivation Questionnaire",
    "DSI": "Dependability and Safety Instrument",
    "PJM": "Performance Judgment",
    "SVAR": "Spoken Voice Assessment",
    "UCF": "Universal Competency Framework",
    "SSAS": "SQL Server Analysis Services",
    "SSIS": "SQL Server Integration Services",
    "SSRS": "SQL Server Reporting Services",
    "RPA": "Robotic Process Automation",
    "MVC": "Model-View-Controller",
    "MVVM": "Model-View-ViewModel",
    "WCF": "Windows Communication Foundation",
    "WPF": "Windows Presentation Foundation",
    "XAML": "Extensible Application Markup Language",
    "AWS": "Amazon Web Services",
    "ITIL": "Information Technology Infrastructure Library",
    "SAP": "Systems, Applications, and Products",
    "HCM": "Human Capital Management",
    "BW": "Business Warehouse",
    "SD": "Sales and Distribution",
    "ABAP": "Advanced Business Application Programming",
    "DBA": "Database Administrator",
    "ETL": "Extract, Transform, Load",
    "VLSI": "Very Large Scale Integration",
}

RELEVANT_SUFFIXES = [
    "Test", "Assessment", "Measure", "Questionnaire", "Inventory",
    "Report", "Profile", "Scale", "Solution", "Simulation",
]


def clean_name(name):
    n = name.strip()
    n = re.sub(r"\s*\(New\)\s*$", "", n)
    n = re.sub(r"\s*\(adaptive\)\s*$", "", n)
    n = re.sub(r"\s*\(MFS\)\s*$", "", n)
    n = re.sub(r"\s*-\s*(IC|Individual Contributor|Sales Manager)$", "", n, flags=re.IGNORECASE)
    n = re.sub(r"\s+Solution\s*$", "", n, flags=re.IGNORECASE)
    n = n.strip()
    return n


_PAREN_QUALIFIER = re.compile(
    r"\s*\((?:Advanced|Entry|Intermediate)\s+Level\)\s*", re.IGNORECASE
)


def extract_core(name):
    name = clean_name(name)
    for sfx in RELEVANT_SUFFIXES:
        name = re.sub(r"\s*[-–—]\s*" + re.escape(sfx) + r"$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+" + re.escape(sfx) + r"\s*\d+(?:\.\d+)?$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+" + re.escape(sfx) + r"$", "", name, flags=re.IGNORECASE)
    name = _PAREN_QUALIFIER.sub("", name)
    name = VERSION_SUFFIX_PATTERN.sub("", name)
    name = name.strip()
    return name


_STOP = frozenset({
    "A", "AN", "THE", "OF", "FOR", "IN", "AND", "TO", "WITH", "AT", "BY", "ON",
    "V1", "V2", "R1", "R2", "-", "–", "—",
})


def _clean_words(words):
    result = []
    for w in words:
        w = w.strip("()")
        if w and w.upper() not in _STOP:
            result.append(w)
    return result


def extract_role_keywords(name, description=""):
    core = extract_core(name)
    words = core.split()
    if not words:
        return core, core

    filtered = _clean_words(words)
    if not filtered:
        filtered = [w for w in words if w.upper() not in _STOP]
    if not filtered:
        filtered = words

    role = " ".join(filtered[:4])
    skill = " ".join(filtered[:3])
    return role, skill


def extract_short_name(name):
    core = extract_core(name)
    words = core.split()
    clean = _clean_words(words)
    if not clean:
        clean = [w for w in words if w.upper() not in _STOP]
    if not clean:
        clean = words
    return " ".join(clean[:3])


def infer_category(assessment):
    keys = assessment.get("keys", [])
    name = assessment.get("name", "")
    desc = assessment.get("description", "")
    combined = (name + " " + desc).lower()

    key_map = {
        "Ability & Aptitude": "cognitive",
        "Personality & Behavior": "personality",
        "Simulations": "simulation",
        "Competencies": "competencies",
        "Biodata & Situational Judgment": "situational_judgment",
        "Development & 360": "development",
        "Assessment Exercises": "exercises",
    }
    for k, cat in key_map.items():
        if k in keys:
            return cat

    name_lower = name.lower()

    if re.search(r"\bleadership\b|\bmanager\b|\bsupervisor\b|\bexecutive\b", name_lower):
        return "leadership"
    if re.search(r"\bsales\b", name_lower):
        return "sales"
    if re.search(r"\bfinance\b|\baccounting\b|\baudit\b|\bpayable\b|\breceivable\b", name_lower):
        return "finance"
    if re.search(r"\bpersonality\b|\bopq\b|\bbehavio[u]?r\b", name_lower):
        return "personality"
    if re.search(r"\bsimulation\b", name_lower):
        return "simulation"
    if re.search(r"\bcognitive\b|\baptitude\b|\breasoning\b|\bability\b", name_lower):
        return "cognitive"
    if re.search(r"\bpython\b", name_lower) and "jython" not in name_lower:
        return "python"
    if re.search(r"\bjava\b(?!\s*script)", name_lower):
        return "java"
    if re.search(r"\bsql\b|\bdatabase\b|\bdata\s+warehouse\b|\bmongodb\b|\boracle\b", name_lower):
        return "sql"
    if re.search(r"\bcloud\b|\baws\b|\bazure\b", name_lower):
        return "cloud"
    if re.search(r"\bsecurity\b|\bcyber\b|\bhipaa\b", name_lower):
        return "cybersecurity"
    if re.search(r"\bdevops\b", name_lower):
        return "devops"
    if re.search(r"\btesting\b|\bqa\b|\bquality\b|\betl\s+testing\b|\bmanual\s+testing\b|\bload\s+runner\b|\bselenium\b", name_lower):
        return "testing"
    if re.search(r"\bfrontend\b|\breact\b|\bangular\b|\bcss3?\b|\bhtml(5)?\b|\bjquery\b|\bjavascript\b|\btypescript\b|\bdojo\b|\bdrupal\b", name_lower):
        return "frontend"
    if re.search(r"\bnode\.?\s*js\b|\bexpress\b|\bbackend\b|\bmicroservice\b|\bspring\b|\bhibernate\b|\bstruts\b|\brestful\b", name_lower):
        return "backend"
    if re.search(r"\bmobile\b|\bios\b|\bandroid\b|\bswift\b", name_lower):
        return "mobile"
    if re.search(r"\.net\b|\bc#\b|\bcsharp\b|\basp\b|\bvb\.net\b", name_lower):
        return "dotnet"
    if re.search(r"\bmarketing\b|\bbrand\b|\bseo\b|\badvertising\b|\bsocial media\b|\bdigital advertising\b", name_lower):
        return "marketing"
    if re.search(r"\bhr\b|\btalent\b|\brecruitment\b|\bhiring\b|\bhuman resources\b|\bhcm\b", name_lower):
        return "hr"
    if re.search(r"\bengineering\b|\bsoftware\b|\bprogramming\b|\bcomputer science\b|\bprogramming concepts\b|\bcoding\b", name_lower):
        return "software_engineering"
    if re.search(r"\bcivil\b|\bmechanical\b|\belectrical\b|\bchemical\b|\baerospace\b|\baeronautical\b|\bindustrial\b|\bmining\b|\bpetroleum\b|\bceramic\b|\bautomotive\b|\bmetallurgical\b|\bpolymer\b|\btextile\b|\bmarine\b|\bgeoscience\b|\bfire\s+engineering\b|\binstrumentation\b|\bmechatronics\b|\btelecommunications\b|\belectronics\b|\bsemiconductor\b|\bpower\s+electronics\b|\bpower\s+system\b|\bproduction\b|\bbio(Tech|medical|chemistry|physics|science|logy|engineering|informatics)\b|\bpharma\b|\bchemis", name_lower):
        return "engineering"

    return "general"


def derive_seniority(job_levels):
    labels = []
    jl_joined = " ".join(job_levels)

    if re.search(r"Entry Level|Graduate", jl_joined):
        labels.append("entry level")
        labels.append("graduate")
        labels.append("junior")

    if re.search(r"Professional Individual Contributor", jl_joined):
        labels.append("mid level")
        labels.append("professional")

    if re.search(r"Manager|Front Line Manager", jl_joined):
        labels.append("manager")
        labels.append("senior")

    if re.search(r"Director|Executive", jl_joined):
        labels.append("executive")
        labels.append("director")

    if re.search(r"General Population", jl_joined):
        labels.append("general")

    return labels if labels else ["general"]


def generate_queries(assessment):
    entity_id = assessment["entity_id"]
    name = assessment.get("name", "")
    description = assessment.get("description", "")
    job_levels = assessment.get("job_levels", [])
    keys = assessment.get("keys", [])

    queries = []
    cat = infer_category(assessment)

    clean = clean_name(name)
    role, skill = extract_role_keywords(name, description)
    short = extract_short_name(name)

    def add(formulation, query_text):
        queries.append({
            "query": query_text,
            "relevant_ids": [entity_id],
            "category": cat,
            "formulation": formulation,
        })

    add("direct", clean)

    if skill.lower().endswith("skills"):
        recruiter_q = f"We are looking for someone with {skill}"
    else:
        recruiter_q = f"We are looking for someone with {skill} skills"

    add("role", f"I need to hire {role}")
    add("skill", f"Looking for {skill} assessment")
    add("recruiter", recruiter_q)
    add("scenario", f"Hiring for {role} position")
    add("short", short)

    return queries


def main():
    all_queries = []

    for assessment in catalog:
        qs = generate_queries(assessment)
        all_queries.extend(qs)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_queries, f, indent=2, ensure_ascii=False)

    n = len(all_queries)
    n_assess = len(catalog)

    id_to_qcount = {}
    for q in all_queries:
        for rid in q["relevant_ids"]:
            id_to_qcount.setdefault(rid, 0)
            id_to_qcount[rid] += 1

    counts = list(id_to_qcount.values())
    min_q = min(counts) if counts else 0
    max_q = max(counts) if counts else 0
    avg_q = n / n_assess if n_assess else 0

    form_breakdown = {}
    for q in all_queries:
        f = q["formulation"]
        form_breakdown[f] = form_breakdown.get(f, 0) + 1

    assessed_with_q = len(id_to_qcount)

    print("=" * 60)
    print("FULL COVERAGE BENCHMARK GENERATION STATS")
    print("=" * 60)
    print(f"Total assessments in catalog: {n_assess}")
    print(f"Total queries generated:     {n}")
    print(f"Assessments with >=1 query:  {assessed_with_q}")
    print(f"Queries per assessment:")
    print(f"  Min:  {min_q}")
    print(f"  Max:  {max_q}")
    print(f"  Avg:  {avg_q:.1f}")
    print()
    print("Formulation breakdown:")
    for f in ["direct", "role", "skill", "recruiter", "scenario", "short"]:
        print(f"  {f:12s}: {form_breakdown.get(f, 0)}")
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
