"""Generate 1000+ recruiter-style stress test queries for SHL assessment benchmark."""
from __future__ import annotations
import json
import random
import re
import math
from pathlib import Path
from typing import Any
from collections import Counter

random.seed(42)
ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "catalog" / "catalog.json", encoding="utf-8") as f:
    CATALOG: list[dict[str, Any]] = json.load(f)

with open(ROOT / "benchmark" / "retrieval_benchmark.json", encoding="utf-8") as f:
    EXISTING = [e["query"] for e in json.load(f)]

EXISTING_SET = set(q.strip().casefold() for q in EXISTING)

SKILL_KEYWORDS = sorted({
    kw.lower()
    for a in CATALOG
    for name_part in re.split(r"[\s\(\),/&-]+", a["name"])
    if (kw := name_part.strip()) and len(kw) > 1
})

ROLE_KEYWORDS = [
    "developer", "engineer", "analyst", "manager", "architect",
    "administrator", "consultant", "specialist", "lead", "head",
    "director", "executive", "supervisor", "coordinator", "associate",
    "trainee", "intern", "representative", "officer", "technician",
]

JOB_TITLES = [
    "software engineer", "data scientist", "data analyst", "business analyst",
    "product manager", "project manager", "frontend developer", "backend developer",
    "full stack developer", "devops engineer", "security analyst", "cloud architect",
    "sales representative", "account manager", "marketing manager", "hr manager",
    "financial analyst", "quality analyst", "test engineer", "system administrator",
    "network engineer", "database administrator", "site reliability engineer",
    "machine learning engineer", "ai engineer", "python developer", "java developer",
    "javascript developer", "react developer", "angular developer", "node developer",
    "ux designer", "ui designer", "technical lead", "engineering manager",
    "scrum master", "product owner", "delivery manager", "service desk analyst",
    "customer support", "operations manager", "supply chain analyst", "compliance officer",
]

ABBREVIATIONS = {
    "SWE": "software engineer", "SDE": "software development engineer",
    "PM": "product manager", "TPM": "technical program manager",
    "DE": "data engineer", "MLE": "machine learning engineer",
    "FE": "frontend", "BE": "backend", "FS": "full stack",
    "UX": "user experience", "UI": "user interface",
    "QA": "quality assurance", "SDET": "software development engineer in test",
    "DS": "data science", "DA": "data analyst",
    "HR": "human resources", "PR": "public relations",
    "IC": "individual contributor", "EM": "engineering manager",
    "TL": "team lead", "PE": "principal engineer",
}

JARGON = [
    "10x engineer", "full stack ninja", "rockstar developer",
    "coding guru", "tech wizard", "data wizard", "cloud guru",
    "security ninja", "devops samurai", "javascript ninja",
    "pythonista", "java champ", "react rockstar", "api whisperer",
    "database magician", "automation hero", "testing champion",
    "analytics superstar", "ai visionary", "blockchain pioneer",
]

ROLE_PARTIAL_REQS = [
    "just {} skills", "must know {}", "{} is must", "any {}",
    "{} experience needed", "strong {} required", "good with {}",
    "needs {}", "knows {}", "should have {} exp",
]

CONVERSATIONAL_TEMPLATES = [
    "hey what do you have for {}?",
    "we're looking for a good {} assessment",
    "can you recommend something for {}?",
    "need help finding {} tests",
    "what assessments work for {} roles?",
    "any good options for {} hiring?",
    "we need to screen {} candidates",
    "looking to hire {} what do you have",
    "got any {} assessments that are good?",
    "our team needs {} can you help?",
    "we are hiring for {} please suggest tests",
    "whats available for {} positions?",
    "need to evaluate {} applicants",
    "searching for {} skill tests",
    "do you have anything for {}?",
]

SHORT_QUERIES_TEMPLATES = [
    "{}",  # just the skill itself
    "need {}", "hiring {}", "looking for {}",
    "{} position", "{} role", "{} opening",
    "{} job", "{} req", "{} needed",
    "want {}", "require {}", "urgent {}",
    "{} candidate", "{} hire", "{} search",
]

LONG_MESSY_TEMPLATES = [
    "Hey team we need to hire a {} who knows how to use all the major tools and frameworks in this space can you please send me some good technical assessments",
    "Hi there we are trying to fill a {} position urgently and need to test candidates before interview please recommend some good tests",
    "Our hiring manager is asking for {} assessments for the new team we are building could you please help us find the right ones",
    "We have an opening for a {} and need to screen about 15 candidates next week what assessments would you suggest for this role",
    "Hello looking for recommendations on {} tests we have a tight deadline and need to move fast please share the best options",
    "Can you suggest some assessments for {} we want to make sure we hire the right person for our growing team thanks",
    "We are expanding our {} team and need to evaluate both technical skills and soft skills do you have any recommendations",
    "Need to assess our {} candidates for an urgent role the hiring manager wants results by end of week what can you offer",
    "Looking for {} skill tests for a bulk hiring drive we are planning for next quarter please share catalog and pricing",
    "We need to evaluate {} for a senior position what assessments do you have that can measure both experience and aptitude",
]

PUNCTUATION_VARIANTS = [
    "need {} asap for our team",
    "looking for {} urgently",
    "wanted {} for our project",
    "require {} immediately",
    "need {} for backend team",
    "searching for {} position",
    "hiring {} no delay",
    "want {} candidate soon",
    "looking {} for our new team",
]

CAPS_VARIANTS = [
    "NEED {} FOR OUR TEAM",
    "Hiring a {} for our PROJECT",
    "Looking for {} DEVELOPER",
    "URGENT {} required",
    "Need a {} for our TEAM",
    "WANTED {} POSITION",
    "{} SPECIALIST needed",
    "REQUIRE {} ASAP",
]

IDIOMATIC_VARIANTS = [
    "looking for a {} who can hit the ground running",
    "need a {} who can think outside the box",
    "hiring a {} with a can-do attitude",
    "want a {} who is a team player",
    "need a {} who can wear multiple hats",
    "searching for a {} who can take ownership",
    "looking for a hands-on {} for our team",
    "need a {} who can work in a fast-paced environment",
]

KEYS_MAP = {
    "ability": "Ability & Aptitude",
    "aptitude": "Ability & Aptitude",
    "cognitive": "Ability & Aptitude",
    "reasoning": "Ability & Aptitude",
    "personality": "Personality & Behavior",
    "behavior": "Personality & Behavior",
    "behavioral": "Personality & Behavior",
    "knowledge": "Knowledge & Skills",
    "skill": "Knowledge & Skills",
    "technical": "Knowledge & Skills",
    "simulation": "Simulations",
    "sim": "Simulations",
    "situational": "Biodata & Situational Judgment",
    "biodata": "Biodata & Situational Judgment",
    "development": "Development & 360",
    "360": "Development & 360",
    "competency": "Competencies",
    "competence": "Competencies",
    "assessment exercise": "Assessment Exercises",
    "exercise": "Assessment Exercises",
}

ASSESSMENT_SKILLS_CACHE: list[tuple[str, list[str]]] = []
for a in CATALOG:
    tokens = set()
    for field in [a["name"], a["description"], *a["keys"], *a["job_levels"]]:
        for t in re.split(r"[\s\(\),./&:\-']+", str(field).lower()):
            t = t.strip().rstrip(".").rstrip(",")
            if len(t) > 1:
                tokens.add(t)
    ASSESSMENT_SKILLS_CACHE.append((a["entity_id"], list(tokens)))

def tokenize(text: str) -> set[str]:
    return {
        t.strip().rstrip(".").rstrip(",").rstrip("?").rstrip("!")
        for t in re.split(r"[\s\(\),./&:\-']+", text.lower())
        if len(t) > 1
    }

def find_relevant(query: str) -> list[str]:
    qt = tokenize(query)
    multi_word_skills = []
    for kw in sorted(SKILL_KEYWORDS, key=len, reverse=True):
        kw_lower = kw.lower()
        if " " in kw_lower and kw_lower in query.lower():
            multi_word_skills.append(kw_lower)
    scores: dict[str, float] = {}
    for eid, tokens in ASSESSMENT_SKILLS_CACHE:
        score = 0.0
        matched = set()
        for mw in multi_word_skills:
            for t in tokens:
                if mw in t or t in mw:
                    score += 2.0
                    matched.add(mw)
        for qw in qt:
            if qw in ("looking", "hiring", "need", "want", "test", "role",
                      "position", "job", "team", "candidate", "good", "help",
                      "find", "know", "work", "new", "assess", "screen",
                      "evaluate", "recommend", "opening", "required", "needed",
                      "urgent", "asap", "search", "available", "option",
                      "applicant", "hire", "recruit", "skill", "experience",
                      "senior", "junior", "lead", "head", "staff", "great",
                      "best", "right", "must", "just", "any", "exp"):
                continue
            for t in tokens:
                if qw == t:
                    score += 3.0
                    break
                elif len(qw) > 3 and (qw in t or t in qw):
                    score += 1.0
                    break
                elif len(qw) > 4 and t.startswith(qw):
                    score += 1.5
                    break
        for role in ROLE_KEYWORDS:
            if role in query.lower() and role in tokens:
                score += 2.0
        if score > 0:
            scores[eid] = score
    ranked = sorted(scores.keys(), key=lambda e: -scores[e])
    return ranked[:20]

def short_id(count: int) -> int:
    return count + 1

def make_unique(query: str, seen: set) -> str | None:
    q = query.strip()
    f = q.casefold()
    if f in EXISTING_SET:
        return None
    if f in seen:
        return None
    seen.add(f)
    return q

def generate_all() -> list[dict]:
    queries: list[dict] = []
    seen: set[str] = set()
    cats: dict[str, list[str]] = {}

    all_skill_names = sorted({
        a["name"].lower().strip()
        for a in CATALOG
        if a["keys"] == ["Knowledge & Skills"]
    })

    single_skills = sorted({
        kw.lower() for a in CATALOG
        for name_part in re.split(r"[\s\(\),/&-]+", a["name"])
        if (kw := name_part.strip()) and len(kw) > 2
        and kw.lower() not in ("new", "the", "and", "for", "with", "core",
                               "advanced", "entry", "level", "basic", "planning",
                               "system", "management", "development", "services",
                               "science", "systems", "techniques", "enterprise")
    })

    popular_skills = [
        s for s in single_skills
        if s.lower() in ("python", "java", "javascript", "react", "angular",
                         "node", "sql", "aws", "azure", "docker", "kubernetes",
                         "devops", "data", "machine", "security", "cloud",
                         "sales", "marketing", "hr", "finance", "accounting",
                         "c++", "c#", "ruby", "php", "swift", "kotlin",
                         "typescript", "css", "html", "git", "jenkins",
                         "selenium", "tableau", "power", "scala", "go",
                         "r", "sap", "oracle", "salesforce", "spring",
                         "django", "flask", "express", "mongo", "redis")
    ]

    domain_skills = {
        "python": ["4123", "3989", "4124"],
        "java": ["4034", "4032", "4056", "4084", "4158"],
        "sql": ["4144", "4035", "4145", "3789"],
        "data science": ["4013", "3982", "3983", "4124"],
        "devops": ["4059", "4152", "4086", "4045"],
        "cloud": ["4028", "4045", "4207"],
        "security": ["4053", "331", "4068"],
        "sales": ["3932", "3930", "3937", "4230"],
        "marketing": ["4008", "4003", "4171", "4014"],
        "hr": ["3999", "4135"],
        "finance": ["3992", "4083", "4178", "4179"],
        "frontend": ["4052", "4080", "4081", "4177", "3989", "4153", "4021"],
        "backend": ["4034", "4039", "4123", "3997", "4017", "4143"],
        "mobile": ["4160", "4102", "4129"],
        "testing": ["4159", "4138", "4157", "4065", "4229"],
        "leadership": ["3856", "4287", "749", "750", "4300"],
        "cognitive": ["3968", "3971", "3946", "3734", "3745"],
        "personality": ["720", "727", "748", "724", "1048"],
        "management": ["4116", "742", "3999", "3769"],
        "customer service": ["3933", "3931", "4189"],
        "supply chain": [],
        "healthcare": ["4041", "4077", "4162", "3998"],
    }

    formulation_counts: dict[str, int] = Counter()

    def add(qtext: str, formulation: str):
        q = make_unique(qtext, seen)
        if q is None:
            return
        rel = find_relevant(q)
        cat = determine_category(q, rel)
        queries.append({
            "query": q,
            "relevant_ids": rel,
            "category": cat,
            "formulation": formulation,
        })
        formulation_counts[formulation] += 1

    def determine_category(query: str, relevant: list[str]) -> str:
        ql = query.lower()
        if any(w in ql for w in ["cognitive", "aptitude", "reasoning", "numerical", "verbal", "abstract", "logical", "deductive", "inductive"]):
            return "cognitive"
        if any(w in ql for w in ["personality", "behavioral", "opq", "motivation"]):
            return "personality"
        if any(w in ql for w in ["devops", "docker", "kubernetes", "jenkins", "ci/cd", "cicd"]):
            return "devops"
        if any(w in ql for w in ["security", "cyber", "ethical hacking", "penetration"]):
            return "cybersecurity"
        if any(w in ql for w in ["cloud", "aws", "azure", "gcp"]):
            return "cloud"
        if any(w in ql for w in ["data science", "machine learning", "data scientist", "ai", "deep learning"]):
            return "data_science"
        if any(w in ql for w in ["python", "django", "flask"]):
            return "python"
        if any(w in ql for w in ["java", "spring", "hibernate", "j2ee", "ejb"]):
            return "java"
        if any(w in ql for w in ["sql", "database", "oracle pl/sql", "tsql"]):
            return "sql"
        if any(w in ql for w in ["frontend", "react", "angular", "vue", "html", "css", "javascript", "typescript"]):
            return "frontend"
        if any(w in ql for w in ["backend", "node", "express", "api", "microservice"]):
            return "backend"
        if any(w in ql for w in ["mobile", "android", "ios", "swift", "kotlin", "flutter"]):
            return "mobile"
        if any(w in ql for w in ["testing", "qa", "selenium", "automation test"]):
            return "testing"
        if any(w in ql for w in ["sales", "selling", "account manager"]):
            return "sales"
        if any(w in ql for w in ["marketing", "seo", "brand", "advertising"]):
            return "marketing"
        if any(w in ql for w in ["hr ", "human resource", "recruitment", "talent"]):
            return "hr"
        if any(w in ql for w in ["finance", "accounting", "audit", "tax", "payroll"]):
            return "finance"
        if any(w in ql for w in ["leadership", "management", "manager", "supervisor"]):
            return "management"
        if any(w in ql for w in ["customer service", "customer support", "call center", "help desk"]):
            return "customer_service"
        if any(w in ql for w in ["graduate", "entry level", "fresher", "campus", "junior"]):
            return "entry_level"
        if any(w in ql for w in ["healthcare", "medical", "nursing", "clinical", "pharma"]):
            return "healthcare"
        if any(w in ql for w in ["supply chain", "logistics", "inventory", "warehouse"]):
            return "supply_chain"
        if relevant:
            top = CATALOG[[a["entity_id"] for a in CATALOG].index(relevant[0])] if any(a["entity_id"] == relevant[0] for a in CATALOG) else None
            if top:
                for k in top.get("keys", []):
                    for label, keyval in KEYS_MAP.items():
                        if label in k.lower():
                            return keyval.lower().replace(" & ", "_").replace(" ", "_")
        return "general"

    skills_for_queries = ["python", "java", "javascript", "react", "angular",
                          "node js", "sql", "aws", "azure", "docker",
                          "kubernetes", "devops", "data science", "machine learning",
                          "security", "cloud", "sales", "marketing",
                          "hr", "finance", "c++", "c#", "ruby", "php",
                          "swift", "kotlin", "typescript", "css", "html5",
                          "git", "jenkins", "selenium", "tableau", "sap",
                          "oracle", "salesforce", "spring", "django",
                          "flask", "express", "mongo", "redis", "go",
                          "r", "scala", "android", "ios", "react native",
                          "agile", "leadership", "management", "testing"]

    more_skills = [
        "python", "java", "javascript", "react", "angular", "node.js",
        "sql", "aws", "azure", "docker", "kubernetes", "terraform",
        "ansible", "jenkins", "git", "linux", "devops", "data science",
        "machine learning", "deep learning", "artificial intelligence",
        "security", "cybersecurity", "cloud computing", "salesforce",
        "sap", "oracle", "python developer", "java developer",
        "full stack", "frontend", "backend", "data analyst",
        "data engineer", "devops engineer", "security analyst",
        "product manager", "project manager", "scrum master",
        "business analyst", "quality analyst", "software engineer",
        "software developer", "web developer", "mobile developer",
        "react developer", "angular developer", "node developer",
        "sql developer", "cloud architect", "solutions architect",
        "technical lead", "engineering manager", "delivery head",
        "test automation", "manual testing", "api testing",
        "performance testing", "ui developer", "ux designer",
        "database administrator", "system administrator",
        "network engineer", "compliance officer", "risk analyst",
        "financial analyst", "marketing manager", "hr manager",
        "operations manager", "supply chain manager",
        "customer success", "technical support", "help desk",
        "sales representative", "account executive",
        "business development", "strategic planning",
        "change management", "team leadership",
    ]

    # Category 1: Short queries (2-4 words)
    for skill in random.sample(more_skills, min(120, len(more_skills))):
        tmpl = random.choice(SHORT_QUERIES_TEMPLATES)
        q = tmpl.format(skill)
        if random.random() < 0.3:
            q = q.lower()
        add(q, "short")
    for _ in range(30):
        s1, s2 = random.sample(more_skills, 2)
        q = f"{s1} {s2}"
        add(q, "short")
    # Super short 2-word
    for pair in [
        ("python", "dev"), ("java", "dev"), ("frontend", "engineer"),
        ("backend", "dev"), ("data", "analyst"), ("security", "analyst"),
        ("devops", "lead"), ("sales", "rep"), ("hiring", "manager"),
        ("tech", "lead"), ("software", "engineer"), ("data", "scientist"),
        ("cloud", "architect"), ("product", "manager"), ("project", "manager"),
        ("test", "engineer"), ("system", "admin"), ("network", "engineer"),
        ("ml", "engineer"), ("ai", "specialist"), ("ux", "designer"),
        ("full", "stack"), ("site", "reliability"), ("scrum", "master"),
        ("business", "analyst"), ("quality", "analyst"),
        ("delivery", "manager"), ("technical", "writer"),
        ("database", "admin"), ("compliance", "officer"),
    ]:
        q = f"{pair[0]} {pair[1]}"
        add(q, "short")

    # Category 2: Long messy queries (15-30 words)
    for i in range(200):
        skill = random.choice(more_skills)
        tmpl = random.choice(LONG_MESSY_TEMPLATES)
        q = tmpl.format(skill)
        add(q, "long_messy")

    # Category 3: Missing punctuation
    for skill in random.sample(more_skills, min(80, len(more_skills))):
        tmpl = random.choice(PUNCTUATION_VARIANTS)
        q = tmpl.format(skill)
        add(q, "missing_punctuation")

    # Category 4: Mixed capitalization
    for skill in random.sample(more_skills, min(60, len(more_skills))):
        tmpl = random.choice(CAPS_VARIANTS)
        q = tmpl.format(skill.capitalize() if random.random() < 0.5 else skill.upper())
        if random.random() < 0.3:
            parts = list(q)
            for _ in range(random.randint(2, 5)):
                idx = random.randint(0, len(parts) - 1)
                parts[idx] = parts[idx].upper() if random.random() < 0.5 else parts[idx].lower()
            q = "".join(parts)
        add(q, "mixed_caps")

    # Category 5: Abbreviations
    for abbr, full in ABBREVIATIONS.items():
        q = f"{abbr} position"
        add(q, "abbreviation")
        q2 = f"hiring {abbr}"
        add(q2, "abbreviation")
        q3 = f"{abbr} role need test"
        add(q3, "abbreviation")
    # More abbreviation variants
    extra_abbrs = ["SWE opening", "SDE role", "PM position", "DE role",
                   "MLE role", "FE dev", "BE dev", "QA tester",
                   "DS role", "HR opening", "IC role"]
    for q in extra_abbrs:
        add(q, "abbreviation")

    # Category 6: Industry jargon
    for phrase in JARGON:
        q = f"looking for a {phrase}"
        add(q, "jargon")
        q2 = f"need a {phrase} for our team"
        add(q2, "jargon")
        q3 = f"hiring a {phrase}"
        add(q3, "jargon")
    # More jargons with skills
    jargon_phrases = [
        "coding ninja", "data guru", "security wizard",
        "cloud expert", "agile champion", "testing guru",
        "analytics pro", "database expert", "api expert",
        "automation specialist", "performance guru",
    ]
    for phrase in jargon_phrases:
        q = f"need {phrase}"
        add(q, "jargon")
        add(f"looking for a {phrase}", "jargon")

    # Category 7: Partial requirements
    for skill in random.sample(more_skills, min(60, len(more_skills))):
        tmpl = random.choice(ROLE_PARTIAL_REQS)
        q = tmpl.format(skill)
        add(q, "partial_requirement")
    more_partials = [
        "just python no java", "must know react", "react is must",
        "any sql experience", "cloud exp needed", "java mandatory",
        "python essential", "javascript required", "aws experience must",
        "docker knowledge needed", "kubernetes exp mandatory",
        "leadership skills", "management experience",
        "testing experience required", "agile exp needed",
        "communication skills must", "team player required",
        "problem solving essential", "analytical skills needed",
    ]
    for q in more_partials:
        add(q, "partial_requirement")

    # Category 8: Conversational
    for skill in random.sample(more_skills, min(120, len(more_skills))):
        tmpl = random.choice(CONVERSATIONAL_TEMPLATES)
        q = tmpl.format(skill)
        if random.random() < 0.3:
            q = q.capitalize()
        add(q, "conversational")
    extra_convo = [
        "we need python dev can you help",
        "hi looking for java assessments thanks",
        "hello team need to hire react devs urgently",
        "hey there do you have tests for data scientists",
        "we are trying to fill a devops role any suggestions",
        "can you recommend some good security assessments",
        "i need to find tests for our new cloud team",
        "our recruitment team is looking for sales assessments",
        "what assessments do you recommend for managers",
        "would like to get some suggestions for finance roles",
        "we have a bulk hiring for engineers please suggest",
        "looking for entry level tests for campus hiring",
        "need some cognitive ability tests for screening",
        "can you share what personality tests you have",
        "we need to assess leadership potential any ideas",
        "looking for something to test coding skills",
        "what do you have for senior software engineer roles",
        "need to screen 50 candidates for java positions",
        "hiring manager wants python tests this week",
        "we need a good database assessment for our dba role",
        "could you recommend something for react native",
        "looking for machine learning assessments",
        "need to test analytical skills of our candidates",
        "whats good for assessing communication skills",
        "do you have any group exercise assessments",
    ]
    for q in extra_convo:
        add(q, "conversational")

    # Category 9: Role+skill combinations
    for skill in random.sample(more_skills, min(50, len(more_skills))):
        role = random.choice(JOB_TITLES)
        q = f"{role} {skill}"
        add(q, "role_skill_comb")
        q2 = f"{skill} {role}"
        add(q2, "role_skill_comb")

    for _ in range(60):
        role = random.choice(JOB_TITLES)
        skill = random.choice(more_skills)
        q = f"{role} with {skill}"
        add(q, "role_skill_comb")
        q2 = f"{role} who knows {skill}"
        add(q2, "role_skill_comb")

    # Additional: Range queries
    range_skills = [
        ("python", "sql"), ("java", "spring"), ("react", "node"),
        ("aws", "docker"), ("data science", "python"),
        ("devops", "kubernetes"), ("frontend", "react"),
        ("backend", "sql"), ("mobile", "kotlin"),
        ("security", "cloud"), ("sales", "marketing"),
        ("finance", "accounting"), ("hr", "recruitment"),
        ("leadership", "management"), ("testing", "selenium"),
        ("java", "microservices"), ("python", "django"),
        ("javascript", "typescript"), ("scala", "spark"),
        ("ai", "machine learning"),
    ]
    for s1, s2 in range_skills:
        add(f"{s1} and {s2} assessments", "range")
        add(f"{s1} with {s2} experience", "range")
        add(f"need {s1} and {s2} developer", "range")

    # Idiosyncratic recruiter queries
    for skill in random.sample(more_skills, min(40, len(more_skills))):
        tmpl = random.choice(IDIOMATIC_VARIANTS)
        q = tmpl.format(skill.capitalize() if random.random() < 0.5 else skill)
        add(q, "idiomatic")

    extra_idioms = [
        "we need someone who breathes python",
        "looking for a java rockstar who knows spring inside out",
        "need a full stack dev who can do everything",
        "hiring a devops engineer who lives and breathes automation",
        "want a data ninja who can crunch numbers like crazy",
        "need a cloud guru who has seen it all",
        "searching for a security expert who can sleep hack",
        "looking for a sales beast who can close any deal",
        "need a marketing whiz who understands digital",
        "want a leader who can inspire teams",
        "looking for someone with 10 years of java exp",
        "need a candidate who knows python like the back of their hand",
        "hiring someone who can code in their sleep",
        "need a developer who eats data structures for breakfast",
        "looking for a coder who dreams in algorithms",
    ]
    for q in extra_idioms:
        add(q, "idiomatic")

    print(f"\nGenerated {len(queries)} queries before fill-target...")
    return queries, formulation_counts


qlist, fcounts = generate_all()

# Check if we have enough
print(f"After generation: {len(qlist)} unique queries")

# If we need more, generate additional queries from combinations
seen_final = {q["query"].casefold() for q in qlist}

formulation = "short"
extra_skills = ["python", "java", "javascript", "react", "angular", "node.js", "sql", "aws", "azure", "docker", "kubernetes", "devops", "data science", "machine learning", "artificial intelligence", "security", "cyber", "cloud", "sales", "marketing", "hr", "finance", "c++", "c#", "ruby", "php", "swift", "kotlin", "typescript", "css", "html5", "git", "jenkins", "selenium", "tableau", "sap", "oracle", "salesforce", "spring", "django", "flask", "express js", "mongo", "redis", "go", "r", "scala", "android", "ios", "react native", "agile", "leadership", "management", "testing", "qa", "product manager", "project manager", "business analyst", "data analyst", "software engineer", "full stack", "frontend", "backend", "mobile", "cloud architect", "solutions architect", "scrum master", "tech lead", "engineering manager"]

while len(qlist) < 1000:
    skill = random.choice(extra_skills)
    tmpl = random.choice(SHORT_QUERIES_TEMPLATES)
    q = tmpl.format(skill)
    if q.casefold() not in seen_final and q.casefold() not in EXISTING_SET:
        rel = find_relevant(q)
        cat = "general"
        ql = q.lower()
        if any(w in ql for w in ["python", "django"]):
            cat = "python"
        elif any(w in ql for w in ["java", "spring"]):
            cat = "java"
        elif any(w in ql for w in ["sql", "database"]):
            cat = "sql"
        elif any(w in ql for w in ["react", "angular", "frontend", "css", "html"]):
            cat = "frontend"
        elif any(w in ql for w in ["node", "backend", "express", "api"]):
            cat = "backend"
        elif any(w in ql for w in ["devops", "docker", "kubernetes", "jenkins"]):
            cat = "devops"
        elif any(w in ql for w in ["data science", "machine learning", "data scientist", "ai"]):
            cat = "data_science"
        elif any(w in ql for w in ["security", "cyber"]):
            cat = "cybersecurity"
        elif any(w in ql for w in ["cloud", "aws", "azure"]):
            cat = "cloud"
        elif any(w in ql for w in ["sales"]):
            cat = "sales"
        elif any(w in ql for w in ["marketing"]):
            cat = "marketing"
        elif any(w in ql for w in ["hr"]):
            cat = "hr"
        elif any(w in ql for w in ["finance", "accounting"]):
            cat = "finance"
        elif any(w in ql for w in ["management", "leadership"]):
            cat = "management"
        elif any(w in ql for w in ["test", "qa", "selenium"]):
            cat = "testing"
        qlist.append({
            "query": q,
            "relevant_ids": rel,
            "category": cat,
            "formulation": "short",
        })
        seen_final.add(q.casefold())

# Also add some conversational fillers
conversation_fillers = [
    "what tests do you have for {} developers",
    "are there any good {} assessments available?",
    "can you suggest {} skill tests for hiring",
    "we are looking to assess {} capabilities",
    "need to validate {} knowledge of candidates",
    "what options exist for {} evaluation",
    "do you offer {} certification tests",
    "looking for a reliable {} test for recruitment",
]
while len(qlist) < 1050:
    skill = random.choice(more_skills)
    tmpl = random.choice(conversation_fillers)
    q = tmpl.format(skill)
    if q.casefold() not in seen_final and q.casefold() not in EXISTING_SET:
        rel = find_relevant(q)
        cat = "general"
        ql = q.lower()
        for kw, c in [("python", "python"), ("java", "java"), ("sql", "sql"),
                       ("react", "frontend"), ("angular", "frontend"), ("css", "frontend"),
                       ("devops", "devops"), ("docker", "devops"), ("kubernetes", "devops"),
                       ("data science", "data_science"), ("machine learning", "data_science"),
                       ("security", "cybersecurity"), ("cloud", "cloud"),
                       ("aws", "cloud"), ("azure", "cloud"),
                       ("sales", "sales"), ("marketing", "marketing"),
                       ("hr", "hr"), ("finance", "finance"),
                       ("node", "backend"), ("backend", "backend"),
                       ("mobile", "mobile"), ("android", "mobile"),
                       ("leadership", "management"), ("management", "management")]:
            if kw in ql:
                cat = c
                break
        qlist.append({
            "query": q,
            "relevant_ids": rel,
            "category": cat,
            "formulation": "conversational",
        })
        seen_final.add(q.casefold())

# Shuffle
random.shuffle(qlist)

# Compute stats
total = len(qlist)
with_relevance = sum(1 for q in qlist if q["relevant_ids"])
formulation_dist = Counter(q["formulation"] for q in qlist)
avg_rel = sum(len(q["relevant_ids"]) for q in qlist) / total

output_path = ROOT / "benchmark" / "stress_benchmark.json"
output_path.write_text(json.dumps(qlist, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n{'='*60}")
print(f"  Stress Benchmark Generation Complete")
print(f"{'='*60}")
print(f"  Total queries generated:  {total}")
print(f"  With >=1 relevant:        {with_relevance} ({100*with_relevance/total:.1f}%)")
print(f"  Avg relevant/query:       {avg_rel:.2f}")
print(f"\n  Distribution across formulations:")
for f, c in sorted(formulation_dist.items(), key=lambda x: -x[1]):
    print(f"    {f:25s}: {c:4d} ({100*c/total:.1f}%)")
print(f"\n  Output: {output_path}")
print(f"{'='*60}")
