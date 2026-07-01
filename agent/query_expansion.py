"""Deterministic expansion and normalisation tables for the Query Builder.

All tables are static Python dicts — no LLM, no external lookups.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Skill normalisation
# Keeps BOTH the original token and the canonical alias in the query.
# ---------------------------------------------------------------------------

SKILL_NORMALIZATIONS: dict[str, str] = {
    "c++": "cpp",
    "c#": "csharp",
    "asp.net": "aspnet",
    "node.js": "nodejs",
    "vue.js": "vuejs",
    "react.js": "reactjs",
    "angular.js": "angularjs",
    "machine learning": "ml",
    "artificial intelligence": "ai",
    "generative ai": "genai",
    "gen ai": "genai",
    ".net": "dotnet",
    "typescript": "ts",
    "javascript": "js",
}

# ---------------------------------------------------------------------------
# Role expansion table
# Maps a lowercase role keyword to a list of expansion tokens.
# ---------------------------------------------------------------------------

ROLE_EXPANSION: dict[str, list[str]] = {
    # Engineering / Technical
    "backend developer": [
        "backend", "api", "microservices", "spring", "java", "rest", "sql",
        "database", "developer",
    ],
    "backend engineer": [
        "backend", "api", "microservices", "rest", "sql", "database", "engineer",
    ],
    "frontend developer": [
        "frontend", "html", "css", "javascript", "react", "angular", "vue",
        "ui", "developer",
    ],
    "frontend engineer": [
        "frontend", "html", "css", "javascript", "react", "ui", "engineer",
    ],
    "full stack developer": [
        "fullstack", "frontend", "backend", "javascript", "nodejs", "react",
        "sql", "api", "developer",
    ],
    "full stack engineer": [
        "fullstack", "frontend", "backend", "javascript", "nodejs", "api",
        "sql", "engineer",
    ],
    "software engineer": [
        "software", "engineering", "coding", "algorithms", "debugging",
        "design patterns", "testing",
    ],
    "software developer": [
        "software", "development", "coding", "algorithms", "debugging",
        "version control",
    ],
    "python developer": [
        "python", "django", "flask", "backend", "api", "sql", "software engineer",
    ],
    "python engineer": [
        "python", "django", "flask", "backend", "api", "sql", "engineer",
    ],
    "java developer": [
        "java", "spring", "maven", "hibernate", "backend", "api", "developer",
    ],
    "java engineer": [
        "java", "spring", "jvm", "backend", "api", "engineer",
    ],
    "devops engineer": [
        "devops", "ci/cd", "docker", "kubernetes", "aws", "linux",
        "infrastructure", "automation", "monitoring",
    ],
    "site reliability engineer": [
        "sre", "reliability", "observability", "infrastructure", "kubernetes",
        "monitoring", "incidents", "automation",
    ],
    "cloud engineer": [
        "cloud", "aws", "azure", "gcp", "infrastructure", "terraform",
        "kubernetes", "networking",
    ],
    "data engineer": [
        "data", "pipeline", "etl", "sql", "spark", "airflow", "bigquery",
        "python", "data warehouse",
    ],
    "data scientist": [
        "machine learning", "statistics", "python", "pandas", "numpy",
        "analytics", "modeling",
    ],
    "machine learning engineer": [
        "ml", "deep learning", "python", "tensorflow", "pytorch", "model training",
        "data pipelines", "mlops",
    ],
    "ai engineer": [
        "ai", "ml", "llm", "python", "deep learning", "model deployment",
        "nlp", "genai",
    ],
    "data analyst": [
        "sql", "excel", "python", "tableau", "power bi", "analytics",
        "reporting", "data visualisation",
    ],
    "business analyst": [
        "requirements", "analysis", "sql", "excel", "stakeholder",
        "documentation", "process improvement",
    ],
    "database administrator": [
        "dba", "sql", "oracle", "mysql", "postgresql", "performance tuning",
        "backup", "replication",
    ],
    "security engineer": [
        "security", "cybersecurity", "penetration testing", "firewalls",
        "compliance", "encryption", "siem",
    ],
    "mobile developer": [
        "mobile", "ios", "android", "swift", "kotlin", "react native",
        "flutter", "app",
    ],
    "ios developer": [
        "ios", "swift", "objective-c", "xcode", "apple", "mobile", "developer",
    ],
    "android developer": [
        "android", "kotlin", "java", "android studio", "mobile", "developer",
    ],
    "qa engineer": [
        "quality assurance", "testing", "automation", "selenium", "pytest",
        "bug tracking", "test cases",
    ],
    "test engineer": [
        "testing", "quality", "automation", "selenium", "manual testing",
        "regression", "test plans",
    ],
    "embedded engineer": [
        "embedded", "c", "c++", "firmware", "rtos", "microcontroller",
        "hardware", "iot",
    ],
    # Product / Design
    "product manager": [
        "product", "roadmap", "agile", "stakeholders", "requirements",
        "prioritisation", "user stories", "backlog",
    ],
    "product owner": [
        "product", "backlog", "scrum", "agile", "user stories", "sprint",
        "stakeholders",
    ],
    "ux designer": [
        "ux", "user experience", "wireframing", "prototyping", "figma",
        "usability", "design thinking",
    ],
    "ui designer": [
        "ui", "visual design", "figma", "css", "accessibility",
        "design systems", "prototyping",
    ],
    # Management / Leadership
    "engineering manager": [
        "management", "leadership", "team", "agile", "delivery",
        "technical", "mentoring", "performance",
    ],
    "team lead": [
        "leadership", "team", "mentoring", "technical", "delivery", "agile",
    ],
    "project manager": [
        "project", "planning", "stakeholders", "risk", "timeline", "budget",
        "delivery", "communication",
    ],
    "program manager": [
        "program", "portfolio", "governance", "stakeholders", "risk",
        "delivery", "cross-functional",
    ],
    "cto": [
        "technology", "leadership", "strategy", "architecture", "innovation",
        "team building", "executive",
    ],
    # Sales / Customer
    "sales manager": [
        "sales", "leadership", "communication", "negotiation", "customer",
        "management",
    ],
    "sales representative": [
        "sales", "customer", "negotiation", "communication", "crm",
        "pipeline", "targets",
    ],
    "account manager": [
        "account", "customer", "relationship", "sales", "negotiation",
        "communication", "retention",
    ],
    "customer success manager": [
        "customer success", "onboarding", "retention", "relationship",
        "communication", "product knowledge",
    ],
    # Finance / Operations
    "financial analyst": [
        "finance", "analysis", "excel", "financial modelling", "forecasting",
        "reporting", "accounting",
    ],
    "operations manager": [
        "operations", "process", "efficiency", "team", "management",
        "continuous improvement", "logistics",
    ],
    "hr manager": [
        "hr", "human resources", "recruitment", "employee relations",
        "performance", "compliance", "payroll",
    ],
    "recruiter": [
        "recruitment", "talent acquisition", "sourcing", "interviewing",
        "hr", "candidate", "hiring",
    ],
    # Marketing
    "marketing manager": [
        "marketing", "campaigns", "brand", "analytics", "strategy",
        "digital", "content",
    ],
    "digital marketing specialist": [
        "seo", "sem", "google ads", "social media", "analytics",
        "email marketing", "campaigns",
    ],
}


def get_role_expansion(role: str) -> list[str]:
    """Return expansion terms for a role using a deterministic lookup.

    Matching is case-insensitive.  If the exact role is not found the function
    falls back to partial-key matching so that "senior python developer" still
    expands via the "python developer" key.
    """
    if not role:
        return []

    normalised = role.strip().lower()

    # Exact match
    if normalised in ROLE_EXPANSION:
        return list(ROLE_EXPANSION[normalised])

    # Partial match: find the longest key that is a substring of the role
    best_key = ""
    best_terms: list[str] = []
    for key, terms in ROLE_EXPANSION.items():
        if key in normalised and len(key) > len(best_key):
            best_key = key
            best_terms = list(terms)

    return best_terms


def normalise_skill(skill: str) -> list[str]:
    """Return [original_token, normalised_alias] for a skill, or [original] if no alias.

    Both forms are kept so queries hit both the canonical and natural-language
    representations.
    """
    key = skill.strip().lower()
    alias = SKILL_NORMALIZATIONS.get(key)
    if alias and alias != key:
        return [skill.strip(), alias]
    return [skill.strip()]


def normalise_skills(skills: list[str]) -> list[str]:
    """Normalise a list of skills, deduplicate, and maintain deterministic order."""
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        for token in normalise_skill(skill):
            key = token.casefold()
            if key not in seen:
                seen.add(key)
                result.append(token)
    return result
