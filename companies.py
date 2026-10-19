
"""India-focused AI/ML job tracker.
ATS slugs are candidates: validate them using /status.
A valid slug does not guarantee India-based openings.
"""

QUERIES = [
    "AI Engineer",
    "Machine Learning Engineer",
    "ML Engineer",
    "Data Scientist",
    "Applied Scientist",
    "Research Scientist",
    "AI Researcher",
    "Research Engineer",
    "AI ML Engineer",
    "Generative AI Engineer",
    "LLM Engineer",
    "RAG Engineer",
    "AI Agent Engineer",
    "Agentic AI",
    "NLP Engineer",
    "Deep Learning Engineer",
    "Computer Vision Engineer",
    "MLOps Engineer",
    "ML Platform Engineer",
    "Applied AI Engineer",
    "AI Application Developer",
    "AI Software Engineer",
    "AI Automation Engineer",
    "Data Science",
    "Decision Scientist",
]

WORKDAY_QUERIES = [
    "machine learning India",
    "artificial intelligence India",
    "AI engineer India",
    "data scientist India",
    "research scientist India",
    "generative AI India",
    "LLM engineer India",
    "agentic AI India",
    "NLP India",
    "computer vision India",
    "MLOps India",
    "applied scientist India",
    "AI research India",
]

# Greenhouse: boards.greenhouse.io/<slug>
GREENHOUSE = [
    # Existing
    "anthropic", "databricks", "stripe", "airbnb",
    "cloudflare", "datadog", "elastic", "twilio",
    "mongodb", "coinbase",

    # AI, ML, LLM infrastructure
    "scaleai", "togetherai",

    # SaaS and developer platforms
    "figma", "reddit", "pinterest", "instacart",
    "duolingo", "brex", "ramp", "samsara", "gitlab",

    # Additional global tech employers
    "webflow", "launchdarkly", "cockroachlabs",
]

# Lever: jobs.lever.co/<slug>
LEVER = [
    # Existing
    "cred", "meesho", "paytm", "palantir",

    # Candidate India product / SaaS companies
    "freshworks", "zeta",
]

# Ashby: jobs.ashbyhq.com/<slug>
ASHBY = [
    # Existing
    "openai", "cohere", "perplexity",

    # AI-native / AI infrastructure candidates
    "cursor", "vapi", "langchain", "pinecone", "anyscale",
    "fireworks", "baseten", "writer", "lovable", "modal",

    # Software and data platforms
    "ramp", "linear", "posthog",
]

# SmartRecruiters: jobs.smartrecruiters.com/<CompanyId>
SMARTRECRUITERS = [
    "Visa",
]

# Only add entries here after verifying the exact Workday URL.
# (display name, tenant, wd number, site)
WORKDAY = [
    ("NVIDIA", "nvidia", 5, "NVIDIAExternalCareerSite"),
    ("Adobe", "adobe", 5, "external_experienced"),
    ("Salesforce", "salesforce", 12, "External_Career_Site"),
    ("Intel", "intel", 1, "External"),
    ("Mastercard", "mastercard", 1, "CorporateCareers"),
    ("Workday", "workday", 5, "Workday"),
]

AMAZON = True
