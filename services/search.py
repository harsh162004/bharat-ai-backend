# ============================================================
# services/search.py — Web Search Service for Bharat.ai v2.6
# ============================================================

import re
import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tavily import TavilyClient
from config import TAVILY_API_KEY

tavily = TavilyClient(api_key=TAVILY_API_KEY)
# ── Config ────────────────────────────────────────────────────
from config import NEWSAPI_KEY

MAX_SEARCH_CHARS = 3000
MAX_WIKI_SENTENCES = 4
MAX_DDG_RESULTS = 10

BLOCKED_DOMAINS = {
    "reddit.com", "quora.com", "pinterest.com", "pinterest.in",
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "tiktok.com", "youtube.com", "medium.com",
    "linkedin.com", "indeed.com", "naukri.com",
    "shiksha.com", "collegedunia.com", "careers360.com",
}

PREFERRED_DOMAINS = {
    "wikipedia.org", "gov.in", "nic.in", "ac.in",
    "dibrugarhuniversity.in", "du.ac.in", "dibru.ac.in",
    "nptel.ac.in", "iit.ac.in", "iisc.ac.in",
}

TRUSTED_NEWS_SOURCES = {
    "ndtv", "times of india", "the hindu", "bbc", "reuters",
    "cnn", "the guardian", "india today", "the indian express",
    "hindustan times", "news18", "moneycontrol", "livemint",
}

DU_QUICK_FACTS = {
    "name": "Dibrugarh University",
    "founded": "1965",
    "location": "Dibrugarh, Assam, India",
    "naac": "A Grade",
    "website": "https://dibru.ac.in",
    "vc": "Prof. Jiten Hazarika",
    "departments": ["Computer Science", "Commerce", "Physics",
                    "Chemistry", "Mathematics", "Botany", "Zoology",
                    "Economics", "English", "Assamese"],
}

DU_DEPARTMENTS = {
    "computer science": "dibru.ac.in/dept/computer-science",
    "cs": "dibru.ac.in/dept/computer-science",
    "commerce": "dibru.ac.in/dept/commerce",
    "physics": "dibru.ac.in/dept/physics",
    "chemistry": "dibru.ac.in/dept/chemistry",
    "mathematics": "dibru.ac.in/dept/mathematics",
    "botany": "dibru.ac.in/dept/botany",
    "zoology": "dibru.ac.in/dept/zoology",
    "economics": "dibru.ac.in/dept/economics",
    "english": "dibru.ac.in/dept/english",
    "assamese": "dibru.ac.in/dept/assamese",
}

RSS_FEEDS = [
    ("NDTV", "https://feeds.feedburner.com/ndtvnews-latest"),
    ("Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"),
    ("The Hindu", "https://www.thehindu.com/news/?service=rss"),
    ("BBC India", "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"),
    ("India Today", "https://www.indiatoday.in/rss/home"),
]

try:
    from ddgs import DDGS
    print("✅ Using ddgs import")
except ImportError:
    try:
        from duckduckgo_search import DDGS
        print("⚠️ Using old duckduckgo_search import")
    except ImportError:
        print("❌ FAILED to import DDGS - search will not work!")
        DDGS = None


# ── Helpers ───────────────────────────────────────────────────
def _truncate(text: str, sentences: int = MAX_WIKI_SENTENCES) -> str:
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    parts = re.split(sentence_pattern, text.strip())
    return " ".join(parts[:sentences]).strip()

def _is_blocked(url: str) -> bool:
    url_lower = url.lower()
    return any(domain in url_lower for domain in BLOCKED_DOMAINS)

def _is_preferred(url: str) -> bool:
    url_lower = url.lower()
    return any(domain in url_lower for domain in PREFERRED_DOMAINS)

def _relevance_score(result: dict, query: str, du_dept_url: str = None) -> int:
    query_words = set(query.lower().split())
    title = result.get("title", "").lower()
    url = result.get("url", "").lower()
    score = 0
    for word in query_words:
        if len(word) > 2 and word in title:
            score += 1
    if _is_preferred(url):
        score += 10
    if du_dept_url and du_dept_url in url:
        score += 15
    if any(url.endswith(tld) for tld in [".tk", ".ml", ".cf"]):
        score -= 5
    return score


# ── DU Knowledge Base ─────────────────────────────────────────
def _is_du_query(query: str) -> bool:
    q = query.lower()
    du_keywords = ["dibrugarh university", "dibru", "du assam", "dibrugarh", "ccsa"]
    return any(kw in q for kw in du_keywords)

def _detect_du_department(query: str) -> str:
    q = query.lower()
    for dept, url in DU_DEPARTMENTS.items():
        if dept in q:
            return url
    return None

def _detect_professor(query: str) -> str:
    match = re.search(r"(?:dr\.?|prof\.?|professor)\s+([a-z]+(?:\s+[a-z]+)?)", query, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def _get_du_context(query: str) -> str:
    lines = [
        f"[Official DU Info] Dibrugarh University — Founded {DU_QUICK_FACTS['founded']}, "
        f"Location: {DU_QUICK_FACTS['location']}, NAAC: {DU_QUICK_FACTS['naac']}, "
        f"Vice Chancellor: {DU_QUICK_FACTS['vc']}, "
        f"Website: {DU_QUICK_FACTS['website']}",
    ]
    dept = _detect_du_department(query)
    if dept:
        lines.append(f"[Department] Official page: https://{dept}")
    prof = _detect_professor(query)
    if prof:
        lines.append(f"[Professor Search] Looking up: {prof}")
    return "\n".join(lines)

def _load_du_knowledge() -> list:
    kb_path = os.path.join(os.path.dirname(__file__), "du_knowledge.json")
    if not os.path.exists(kb_path):
        return []
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Failed to load DU knowledge base: {e}")
        return []

def du_knowledge_search(query: str) -> str:
    kb = _load_du_knowledge()
    if not kb:
        return ""
    q_words = set(query.lower().split())
    matches = []
    for entry in kb:
        content = entry.get("content", "").lower()
        title = entry.get("title", "").lower()
        score = 0
        for word in q_words:
            if len(word) > 2:
                if word in title:
                    score += 3
                if word in content:
                    score += 1
        if score > 0:
            matches.append((score, entry))
    matches.sort(key=lambda x: x[0], reverse=True)
    if matches:
        chunks = []
        for score, entry in matches[:2]:
            text = entry.get("content", "")[:500]
            chunks.append(f"[DU Website] {entry.get('title', '')}: {text}")
        return "\n\n".join(chunks)
    return ""


# ── DuckDuckGo Search ─────────────────────────────────────────
def ddg_search(query: str, max_results: int = MAX_DDG_RESULTS, du_dept_url: str = None, site_restrict: str = None) -> list:
    if DDGS is None:
        print("❌ DDGS is None — library not installed!")
        return []
    search_query = f"site:{site_restrict} {query}" if site_restrict else query
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(search_query, max_results=max_results))
            print(f"🔍 DDG found {len(raw_results)} raw results for: {search_query}")
            filtered = [r for r in raw_results if not _is_blocked(r.get("href", ""))]
            results = []
            for r in filtered:
                result = {
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                }
                result["_score"] = _relevance_score(result, query, du_dept_url)
                results.append(result)
            results.sort(key=lambda x: x["_score"], reverse=True)
            for r in results:
                del r["_score"]
            for i, r in enumerate(results[:3]):
                print(f"   [{i+1}] {r['title'][:60]}...")
            return results
    except Exception as e:
            print(f"❌ DuckDuckGo search FAILED: {e}")
            print("🔄 Falling back to Tavily...")
            return tavily_search(query, max_results)

def tavily_search(query: str, max_results: int = 5):
    try:
        print("🔥 USING TAVILY SEARCH")
        print("🔥 USING TAVILY SEARCH")
        result = tavily.search(
            query=query,
            search_depth="basic",
            max_results=max_results
        )

        results = []

        for r in result.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "url": r.get("url", "")
            })

        print(f"✅ Tavily found {len(results)} results")
        return results

    except Exception as e:
        print(f"❌ Tavily FAILED: {e}")
        return []
# ── Wikipedia Search ──────────────────────────────────────────
def wiki_search(query: str) -> str:
    def _direct_lookup(search_term: str) -> str:
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + search_term.replace(" ", "_")
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("extract"):
                    return data.get("extract", "")
            return ""
        except Exception:
            return ""

    def _opensearch_lookup(search_term: str) -> str:
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {"action": "opensearch", "search": search_term,
                      "limit": 3, "namespace": 0, "format": "json"}
            r = requests.get(url, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                titles = data[1] if len(data) > 1 else []
                for title in titles[:2]:
                    extract = _direct_lookup(title)
                    if extract:
                        return extract
            return ""
        except Exception:
            return ""

    try:
        result = _direct_lookup(query)
        if result:
            print(f"✅ Wikipedia found (direct): {query[:50]}...")
            return _truncate(result)
        clean_query = query.replace("Dr. ", "").replace("Dr ", "").strip()
        if clean_query != query and clean_query:
            result = _direct_lookup(clean_query)
            if result:
                return _truncate(result)
        result = _opensearch_lookup(query)
        if result:
            print(f"✅ Wikipedia found (opensearch): {query[:50]}...")
            return _truncate(result)
        print("⚠️ Wikipedia: No page found")
        return ""
    except Exception as e:
        print(f"❌ Wikipedia search FAILED: {e}")
        return ""


# ── NewsAPI Search ────────────────────────────────────────────
def fetch_news(query: str) -> str:
    if not NEWSAPI_KEY:
        return _fetch_news_rss(query)
    try:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = "https://newsapi.org/v2/everything"
        params = {"q": query, "from": from_date, "sortBy": "relevancy",
                  "language": "en", "pageSize": 10, "apiKey": NEWSAPI_KEY}
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if data.get("status") != "ok":
            return _fetch_news_rss(query)
        articles = data.get("articles", [])
        if not articles:
            return ""
        trusted = [a for a in articles if any(s in a.get("source", {}).get("name", "").lower() for s in TRUSTED_NEWS_SOURCES)]
        selected = trusted[:5] if trusted else articles[:3]
        news = [f"- {a.get('title', '')}: {a.get('description', '') or ''}" for a in selected if a.get('title')]
        return "Latest News:\n" + "\n".join(news) if news else ""
    except Exception as e:
        print(f"❌ NewsAPI FAILED: {e}")
        return _fetch_news_rss(query)


# ── RSS News Fallback ─────────────────────────────────────────
def _fetch_news_rss(query: str) -> str:
    def _score_article(title: str, query: str) -> int:
        query_words = set(query.lower().split())
        title_lower = title.lower()
        return sum(1 for w in query_words if len(w) > 2 and w in title_lower)

    all_articles = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for source_name, feed_url in RSS_FEEDS:
        try:
            r = requests.get(feed_url, headers=headers, timeout=6)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item"):
                title_tag = item.find("title")
                desc_tag = item.find("description")
                title = title_tag.text.strip() if title_tag else ""
                desc = desc_tag.text.strip() if desc_tag else ""
                if title:
                    all_articles.append({"title": title, "desc": desc, "source": source_name})
        except Exception as e:
            print(f"⚠️ RSS feed failed [{source_name}]: {e}")

    try:
        google_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
        r = requests.get(google_url, headers=headers, timeout=6)
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            desc_tag = item.find("description")
            title = title_tag.text.strip() if title_tag else ""
            desc = desc_tag.text.strip() if desc_tag else ""
            if title:
                all_articles.append({"title": title, "desc": desc, "source": "Google News"})
    except Exception as e:
        print(f"⚠️ Google News RSS failed: {e}")

    if not all_articles:
        return ""

    seen_titles = set()
    scored = []
    for article in all_articles:
        title = article["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)
        article["_score"] = _score_article(title, query)
        scored.append(article)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    news = [f"- [{a['source']}] {a['title']}: {a['desc']}" for a in scored[:5]]
    return "Latest News:\n" + "\n".join(news) if news else ""


# ── Nominatim Local Search ────────────────────────────────────
def nominatim_search(query: str) -> str:
    try:
        headers = {"User-Agent": "BharatAI/1.0"}
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 3, "countrycodes": "in"}
        r = requests.get(url, headers=headers, params=params, timeout=5)
        data = r.json()
        if not data:
            return ""
        results = [f"📍 {place.get('display_name', '')}" for place in data]
        return "Local Places:\n" + "\n".join(results)
    except Exception as e:
        print(f"❌ Nominatim FAILED: {e}")
        return ""


# ── Live Score Fetcher ────────────────────────────────────────
def fetch_live_scores() -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://www.espncricinfo.com/live-cricket-score", headers=headers, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        scores = []
        for card in soup.find_all("div", class_=lambda c: c and "match" in c.lower())[:5]:
            text = card.get_text(separator=" ", strip=True)
            if len(text) > 20:
                scores.append(text[:300])
        return "Live Cricket Scores:\n\n" + "\n\n".join(scores) if scores else ""
    except Exception as e:
        print(f"❌ Live scores FAILED: {e}")
        return ""


# ── Combined Search (Smart Routing) ───────────────────────────
def combined_search(query: str) -> str:
    q = query.lower()
    output = ""

    is_news_query = any(w in q for w in ["news", "latest", "today", "current affairs", "breaking", "headlines"])
    is_score_query = any(w in q for w in ["live score", "ipl score", "cricket score", "match score", "live match", "ipl", "cricket"])
    is_person_query = any(w in q for w in [
        "who is", "who was", "biography", "born", "about",
        "minister", "president", "cm", "chief minister", "governor",
        "ceo", "founder", "leader", "scientist", "actor", "actress",
        "politician", "officer", "director", "chairman"
    ])
    is_place_query = any(w in q for w in ["where is", "location", "city", "state", "district", "near me", "places"])
    is_edu_query = any(w in q for w in [
        "university", "college", "institute", "school", "academy",
        "department", "faculty", "bca", "mca", "btech", "mtech",
        "bsc", "msc", "bba", "mba", "phd"
    ])
    is_du = _is_du_query(query)
    du_dept = _detect_du_department(query) if is_du else None
    prof = _detect_professor(query) if is_du else None
    is_freshness_query = any(w in q for w in ["admission", "result", "notice", "date", "exam", "2025", "2026", "2027"])

    def _add_if_room(text: str) -> bool:
        nonlocal output
        if len(output) + len(text) > MAX_SEARCH_CHARS:
            return False
        output += text
        return True

    # ── DU Query Special Handling ──────────────────────────────
    if is_du:
        _add_if_room(f"{_get_du_context(query)}\n\n")

        kb_result = du_knowledge_search(query)
        if kb_result:
            _add_if_room(f"[DU Knowledge Base]\n{kb_result}\n\n")

        search_query = f"{query} {datetime.now().year}" if is_freshness_query else query
        print(f"🔄 DU search query: {search_query}")

        site_results = ddg_search(search_query, max_results=5, du_dept_url=du_dept, site_restrict="dibru.ac.in")
        if site_results:
            _add_if_room("[Official DU Website Results]\n")
            for r in site_results[:3]:
                if not _add_if_room(f"- {r['title']}: {r['snippet']}\n\n"):
                    break

        if len(output) < 500:
            general_results = ddg_search(search_query, max_results=5, du_dept_url=du_dept)
            if general_results:
                _add_if_room("[General Web Results]\n")
                for r in general_results[:3]:
                    if not _add_if_room(f"- {r['title']}: {r['snippet']}\n\n"):
                        break

        wiki_query = prof if prof else "Dibrugarh University"
        wiki = wiki_search(wiki_query)
        if wiki:
            _add_if_room(f"[Wikipedia] {wiki}\n\n")

        if is_place_query:
            nominatim = nominatim_search("Dibrugarh University")
            if nominatim:
                _add_if_room(f"[Location] {nominatim}\n\n")

        final = output.strip()
        if len(final) > MAX_SEARCH_CHARS:
            final = final[:MAX_SEARCH_CHARS] + "\n... [truncated]"
        print(f"📄 Final DU search output: {len(final)} chars")
        return final or "No results found."

    # ── Non-DU Queries ─────────────────────────────────────────
    if is_score_query and not is_news_query and not is_person_query and not is_place_query and not is_edu_query:
        live = fetch_live_scores()
        if live:
            _add_if_room(live + "\n\n")

    elif is_news_query and not is_edu_query:
        news = fetch_news(query)
        if news:
            _add_if_room(news + "\n\n")

    elif is_person_query and not is_edu_query:
        wiki = wiki_search(query)
        if wiki:
            _add_if_room(f"Wikipedia: {wiki}\n\n")
        # Always run DDG too — don't rely on wiki alone
        ddg_results = ddg_search(query, max_results=8)
        for r in ddg_results:
            if not _add_if_room(f"- {r['title']}: {r['snippet']}\n\n"):
                break

    elif is_edu_query:
        wiki = wiki_search(query)
        if wiki:
            _add_if_room(f"Wikipedia: {wiki}\n\n")
        results = ddg_search(query, max_results=8)
        for r in results:
            if not _add_if_room(f"- {r['title']}: {r['snippet']}\n\n"):
                break
        if is_place_query:
            nominatim = nominatim_search(query)
            if nominatim:
                _add_if_room(f"{nominatim}\n\n")

    elif is_place_query:
        nominatim = nominatim_search(query)
        if nominatim:
            _add_if_room(f"{nominatim}\n\n")

    else:
        results = ddg_search(query, max_results=8)
        for r in results:
            if not _add_if_room(f"- {r['title']}: {r['snippet']}\n\n"):
                break

    final = output.strip()
    if len(final) > MAX_SEARCH_CHARS:
        final = final[:MAX_SEARCH_CHARS] + "\n... [truncated]"
    print(f"📄 Final search output: {len(final)} chars")
    return final or "No results found."


# ── Simple web_search wrapper ─────────────────────────────────
def web_search(query: str) -> dict:
    try:
        result_text = combined_search(query)
        return {"success": True, "query": query, "results": result_text}
    except Exception as e:
        print(f"❌ web_search FAILED: {e}")
        return {"success": False, "error": str(e)}