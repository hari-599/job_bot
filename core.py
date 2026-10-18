"""Core engine: fetch jobs -> strict experience/location/title match -> dedupe -> return new matches."""
import hashlib, html, os, re, sqlite3, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

import companies as C

UA = {"User-Agent": "Mozilla/5.0 (personal job bot)"}

# ------------------------------------------------------------------ YOUR PROFILE
# ~1 year full-time AI/ML + Master's in AI. Accept roles whose *minimum* required
# experience is <= 2 years (0-2, 1-3, 2+, fresher...). Reject 3+.
MAX_MIN_YEARS = 2
MAX_AGE_DAYS = 3

TITLE_INCLUDE = re.compile(
    r"\b(ai|a\.i\.|ml|machine learning|data scien\w*|research(er)?|nlp|llm|gen ?ai|"
    r"generative|deep learning|computer vision|applied scientist|mlops|agent\w*)\b", re.I)
TITLE_EXCLUDE = re.compile(
    r"\b(senior|sr\.?|lead|principal|staff|head|director|manager|vp|architect|"
    r"intern(ship)?|sales|marketing|recruiter|"
    r"(engineer|scientist|developer|analyst)\s+(iii|iv|v|3|4|5))\b", re.I)
INDIA = re.compile(
    r"india|bangalore|bengaluru|hyderabad|pune|mumbai|delhi|gurgaon|gurugram|noida|"
    r"chennai|kochi|cochin|trivandrum|thiruvananthapuram|kerala|kolkata|ahmedabad", re.I)

# ------------------------------------------------------------------ EXPERIENCE PARSER
_RANGE = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d)?)\s*(?:\+|plus)?\s*(?:-|–|—|to)\s*(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)", re.I)
_SINGLE = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d)?)\s*(?:\+|plus)?\s*(?:years?|yrs?)", re.I)
_CUT = re.compile(r"preferred qualifications|preferred skills|nice to have|good to have|"
                  r"great to have|bonus points|what would make you stand out", re.I)
_SPLIT = re.compile(r"(?<!\d)\.(?!\d)|[\n;•]")


def required_years(text):
    """Minimum years of experience the posting demands (None if not stated).
    Ignores 'preferred / nice-to-have' sections; takes the highest lower-bound among requirements."""
    if not text:
        return None
    m = _CUT.search(text)
    if m:
        text = text[:m.start()]
    lows = []
    for s in _SPLIT.split(text):
        if not re.search(r"experience|exp\b|expertise|background|hands-on", s, re.I):
            continue
        r = _RANGE.findall(s)
        nums = [float(a) for a, _ in r] if r else [float(n) for n in _SINGLE.findall(s)]
        lows += [n for n in nums if n <= 15]
    if lows:
        return max(lows)
    if re.search(r"\b(fresher|freshers|new grad|entry[- ]level|recent graduate)\b", text, re.I):
        return 0
    return None


# ------------------------------------------------------------------ STORAGE
DB = sqlite3.connect(os.getenv("DB_PATH", "jobbot.db"), check_same_thread=False)
LOCK = threading.Lock()
with LOCK:
    DB.executescript("""
    CREATE TABLE IF NOT EXISTS jobs(h TEXT PRIMARY KEY, x TEXT, title, company, location, url,
        source, exp, status, ts);
    CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v);
    CREATE TABLE IF NOT EXISTS chats(id INTEGER PRIMARY KEY);
    """)
HEALTH = {}


def kv_get(k, d=None):
    with LOCK:
        r = DB.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return r[0] if r else d


def kv_set(k, v):
    with LOCK:
        DB.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (k, str(v)))
        DB.commit()


def add_chat(cid):
    with LOCK:
        DB.execute("INSERT OR IGNORE INTO chats VALUES (?)", (cid,))
        DB.commit()


def chats():
    with LOCK:
        return [r[0] for r in DB.execute("SELECT id FROM chats")]


def set_status(h, status):
    with LOCK:
        DB.execute("UPDATE jobs SET status=? WHERE h=?", (status, h))
        DB.commit()


def latest(n=10):
    with LOCK:
        return DB.execute("SELECT title,company,location,url,exp FROM jobs "
                          "WHERE status NOT LIKE 'rejected%' ORDER BY ts DESC LIMIT ?", (n,)).fetchall()


def stats():
    with LOCK:
        return DB.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()


# ------------------------------------------------------------------ HELPERS
def http(method, url, **kw):
    try:
        r = requests.request(method, url, headers=UA, timeout=25, **kw)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise RuntimeError(f"{e.__class__.__name__} {getattr(getattr(e, 'response', None), 'status_code', '')}")


def txt(h):
    return BeautifulSoup(html.unescape(h or ""), "html.parser").get_text("\n", strip=True)


def iso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def mk(id_, title, company, loc, url, posted, source, desc=None, detail=None, exp=None):
    return dict(id=id_, title=title or "", company=company or "", location=loc or "", url=url,
                posted=posted, source=source, desc=desc, detail=detail, exp=exp)


# ------------------------------------------------------------------ SOURCES
def gh(c):
    d = http("GET", f"https://boards-api.greenhouse.io/v1/boards/{c}/jobs")
    out = []
    for j in d["jobs"]:
        def detail(i=j["id"]):
            return {"desc": txt(http("GET", f"https://boards-api.greenhouse.io/v1/boards/{c}/jobs/{i}")["content"])}
        out.append(mk(f"gh:{c}:{j['id']}", j["title"], c, (j.get("location") or {}).get("name"),
                      j["absolute_url"], iso(j.get("updated_at")), "Greenhouse", detail=detail))
    return out


def lever(c):
    out = []
    for j in http("GET", f"https://api.lever.co/v0/postings/{c}", params={"mode": "json"}):
        desc = (j.get("descriptionPlain") or "") + "\n" + "\n".join(
            f"{l.get('text', '')}: {txt(l.get('content'))}" for l in j.get("lists", []))
        out.append(mk(f"lv:{j['id']}", j["text"], c, (j.get("categories") or {}).get("location"),
                      j["hostedUrl"], datetime.fromtimestamp(j["createdAt"] / 1000, timezone.utc),
                      "Lever", desc=desc))
    return out


def ashby(c):
    out = []
    for j in http("GET", f"https://api.ashbyhq.com/posting-api/job-board/{c}").get("jobs", []):
        out.append(mk(f"ab:{j['id']}", j["title"], c, j.get("location"), j.get("jobUrl"),
                      iso(j.get("publishedAt")), "Ashby",
                      desc=j.get("descriptionPlain") or txt(j.get("descriptionHtml"))))
    return out


def smartrecruiters(c):
    out = []
    d = http("GET", f"https://api.smartrecruiters.com/v1/companies/{c}/postings",
             params={"country": "in", "limit": 100})
    for j in d.get("content", []):
        def detail(ref=j["ref"]):
            secs = http("GET", ref).get("jobAd", {}).get("sections", {})
            return {"desc": "\n".join(txt(s.get("text")) for s in secs.values())}
        loc = j.get("location") or {}
        out.append(mk(f"sr:{j['id']}", j["name"], c, f"{loc.get('city', '')}, {loc.get('country', '')}",
                      f"https://jobs.smartrecruiters.com/{c}/{j['id']}", iso(j.get("releasedDate")),
                      "SmartRecruiters", detail=detail))
    return out


def _wd_age(s):
    s = (s or "").lower()
    now = datetime.now(timezone.utc)
    if "today" in s:
        return now
    if "yesterday" in s:
        return now - timedelta(days=1)
    m = re.search(r"(\d+)\+?\s*days", s)
    return now - timedelta(days=int(m.group(1))) if m else None


def workday(name, tenant, n, site):
    base = f"https://{tenant}.wd{n}.myworkdayjobs.com"
    out = []
    for q in C.WORKDAY_QUERIES:
        d = http("POST", f"{base}/wday/cxs/{tenant}/{site}/jobs",
                 json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q})
        for p in d.get("jobPostings", []):
            def detail(path=p["externalPath"]):
                i = http("GET", f"{base}/wday/cxs/{tenant}/{site}{path}")["jobPostingInfo"]
                loc = ", ".join(filter(None, [i.get("location"), (i.get("country") or {}).get("descriptor"),
                                              *(i.get("additionalLocations") or [])]))
                return {"desc": txt(i.get("jobDescription")), "loc": loc}
            out.append(mk(f"wd:{tenant}:{p['externalPath']}", p["title"], name, p.get("locationsText"),
                          f"{base}/en-US/{site}{p['externalPath']}", _wd_age(p.get("postedOn")),
                          "Workday", detail=detail))
    return out


def amazon():
    out = []
    for q in C.QUERIES[:4]:
        d = http("GET", "https://www.amazon.jobs/en/search.json",
                 params={"base_query": q, "loc_query": "India", "country": "IND",
                         "sort": "recent", "result_limit": 50})
        for j in d.get("jobs", []):
            try:
                posted = datetime.strptime(" ".join(j["posted_date"].split()), "%B %d, %Y").replace(tzinfo=timezone.utc)
            except Exception:
                posted = None
            out.append(mk(f"am:{j['id_icims']}", j["title"], "Amazon",
                          j.get("normalized_location") or j.get("location"),
                          "https://www.amazon.jobs" + j["job_path"], posted, "amazon.jobs",
                          desc=txt(j.get("basic_qualifications"))))  # basic quals only, not 'preferred'
    return out


def build_tasks():
    t = []
    t += [(f"greenhouse:{c}", lambda c=c: gh(c)) for c in C.GREENHOUSE]
    t += [(f"lever:{c}", lambda c=c: lever(c)) for c in C.LEVER]
    t += [(f"ashby:{c}", lambda c=c: ashby(c)) for c in C.ASHBY]
    t += [(f"smartrecruiters:{c}", lambda c=c: smartrecruiters(c)) for c in C.SMARTRECRUITERS]
    t += [(f"workday:{w[0]}", lambda w=w: workday(*w)) for w in C.WORKDAY]
    if C.AMAZON:
        t.append(("amazon", amazon))
    return t


# ------------------------------------------------------------------ MATCHING
def quick_ok(j):
    if not TITLE_INCLUDE.search(j["title"]) or TITLE_EXCLUDE.search(j["title"]):
        return False
    p = j["posted"]
    if p:
        p = p if p.tzinfo else p.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - p > timedelta(days=MAX_AGE_DAYS):
            return False
    loc = j["location"]
    if loc and not INDIA.search(loc) and not re.search(r"\d+\s+locations|multiple|remote|various", loc, re.I):
        return False
    return True


def judge(j, strict=True):
    """-> (ok, tag). Strict = reject postings that don't state experience (unless LinkedIn-level-filtered)."""
    text, loc = j.get("desc") or "", j["location"]
    if not (INDIA.search(loc) or re.search(r"\bindia\b", text, re.I)):
        return False, "not india"
    yrs = required_years(text)
    if yrs is None:
        yrs = j.get("exp")
    if yrs is not None:
        return yrs <= MAX_MIN_YEARS, (f"{yrs:g}+ yrs" if yrs else "fresher / 0 yrs") if yrs <= MAX_MIN_YEARS else f"needs {yrs:g}y"
    return (not strict), "not stated"


def _process(j, strict):
    h = hashlib.md5(j["id"].encode()).hexdigest()[:12]
    x = hashlib.md5((j["company"] + j["title"]).lower().encode()).hexdigest()[:12]
    with LOCK:
        if DB.execute("SELECT 1 FROM jobs WHERE h=? OR x=?", (h, x)).fetchone():
            return None
    if j["detail"]:
        try:
            d = j["detail"]()
            j["desc"] = d.get("desc")
            j["location"] = d.get("loc") or j["location"]
        except Exception:
            return None  # transient: retry next cycle
    ok, tag = judge(j, strict)
    j.update(h=h, tag=tag)
    with LOCK:
        DB.execute("INSERT OR IGNORE INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (h, x, j["title"], j["company"], j["location"], j["url"], j["source"], tag,
                    "match" if ok else "rejected", datetime.now().isoformat()))
        DB.commit()
    return j if ok else None


def run_cycle():
    strict = kv_get("strict", "1") == "1"

    def safe(task):
        label, fn = task
        try:
            res = fn()
            HEALTH[label] = f"ok ({len(res)})"
            return res
        except Exception as e:
            HEALTH[label] = f"ERR {e}"
            return []

    with ThreadPoolExecutor(8) as ex:
        batches = list(ex.map(safe, build_tasks()))
        uniq = {}
        for b in batches:
            for j in b:
                if quick_ok(j):
                    uniq.setdefault((j["company"] + j["title"]).lower(), j)
        found = [m for m in ex.map(lambda j: _process(j, strict), uniq.values()) if m]
    return sorted(found, key=lambda j: j["posted"].timestamp() if j["posted"] and j["posted"].tzinfo else 0,
                  reverse=True)
