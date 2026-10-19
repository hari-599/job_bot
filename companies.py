"""Edit this file to add/remove companies. Wrong slugs are harmless: they show up as ERR in /status."""

QUERIES = ["AI Engineer", "Machine Learning Engineer", "Data Scientist",
           "AI Researcher", "Research Scientist", "Generative AI", "LLM", "NLP"]

# Workday searches are relevance-ranked, so we add "India" to bias towards Indian postings.
WORKDAY_QUERIES = ["machine learning India", "artificial intelligence India",
                   "data scientist India", "research scientist India"]

# boards.greenhouse.io/<slug>
GREENHOUSE = ["anthropic", "databricks", "stripe", "airbnb", "cloudflare", "datadog",
              "elastic", "twilio", "mongodb", "coinbase"]

# jobs.lever.co/<slug>
LEVER = ["cred", "meesho", "paytm", "palantir"]

# jobs.ashbyhq.com/<slug>
ASHBY = ["openai", "cohere", "perplexity"]

# jobs.smartrecruiters.com/<CompanyId>
SMARTRECRUITERS = ["Visa"]

# (display name, tenant, wd number, site) from <tenant>.wd<N>.myworkdayjobs.com/<site>
WORKDAY = [
    ("NVIDIA", "nvidia", 5, "NVIDIAExternalCareerSite"),
    ("Adobe", "adobe", 5, "external_experienced"),
    ("Salesforce", "salesforce", 12, "External_Career_Site"),
    ("Intel", "intel", 1, "External"),
    ("Mastercard", "mastercard", 1, "CorporateCareers"),
    ("Workday", "workday", 5, "Workday"),
]

AMAZON = True  # amazon.jobs public JSON search
