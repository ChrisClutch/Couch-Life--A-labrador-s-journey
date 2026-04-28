import datetime as dt
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlencode, urlparse

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


st.set_page_config(page_title="Willamette Valley Permit Finder", layout="wide")


@dataclass(frozen=True)
class CityConfig:
    name: str
    state: str = "OR"
    county: str | None = None
    portal_hint: str | None = None


CITIES: list[CityConfig] = [
    CityConfig("Salem", county="Marion", portal_hint="cityofsalem.net"),
    CityConfig("Aumsville", county="Marion"),
    CityConfig("Turner", county="Marion"),
    CityConfig("Silverton", county="Marion"),
    CityConfig("Keizer", county="Marion", portal_hint="keizer.org"),
    CityConfig("Brooks", county="Marion"),
    CityConfig("McMinnville", county="Yamhill"),
    CityConfig("Woodburn", county="Marion"),
    CityConfig("Albany", county="Linn"),
    CityConfig("Corvallis", county="Benton"),
    CityConfig("Monmouth", county="Polk"),
    CityConfig("Independence", county="Polk"),
    CityConfig("Stayton", county="Marion"),
]

PERMIT_KEYWORDS = [
    "permit",
    "building permit",
    "planning permit",
    "land use permit",
    "submitted permit",
    "permit application",
]


def build_query(city: CityConfig, user_query: str, permit_type: str) -> str:
    terms = [
        f'"{city.name}"',
        f'"{city.state}"',
        f'"{permit_type}"',
        '"permit"',
        user_query.strip(),
        "(site:.gov OR site:.org)",
    ]
    if city.portal_hint:
        terms.append(f"site:{city.portal_hint}")
    return " ".join(term for term in terms if term)


def duckduckgo_html_search(query: str, max_results: int = 10) -> list[dict[str, str]]:
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PermitFinder/1.0; +https://streamlit.io)",
    }

    response = requests.get(url, params=params, timeout=25, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict[str, str]] = []

    for result in soup.select(".result"):
        link_tag = result.select_one(".result__a")
        snippet_tag = result.select_one(".result__snippet")
        if not link_tag:
            continue

        link = link_tag.get("href", "").strip()
        title = link_tag.get_text(" ", strip=True)
        snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

        if title and link:
            results.append({"title": title, "url": link, "snippet": snippet})

        if len(results) >= max_results:
            break

    return results


def score_result(city: CityConfig, record: dict[str, str]) -> int:
    haystack = " ".join([record.get("title", ""), record.get("snippet", ""), record.get("url", "")]).lower()
    score = 0

    if city.name.lower() in haystack:
        score += 3
    if "permit" in haystack:
        score += 3
    if any(keyword in haystack for keyword in PERMIT_KEYWORDS):
        score += 2
    if city.county and city.county.lower() in haystack:
        score += 1

    domain = urlparse(record.get("url", "")).netloc.lower()
    if domain.endswith(".gov"):
        score += 2
    if city.portal_hint and city.portal_hint in domain:
        score += 3

    return score


def run_search(cities: Iterable[CityConfig], user_query: str, permit_type: str, per_city_limit: int) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []

    for city in cities:
        query = build_query(city, user_query=user_query, permit_type=permit_type)
        try:
            results = duckduckgo_html_search(query, max_results=per_city_limit)
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "city": city.name,
                    "title": "Search failed",
                    "url": "",
                    "snippet": str(exc),
                    "score": 0,
                    "query": query,
                }
            )
            continue

        for item in results:
            rows.append(
                {
                    "city": city.name,
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item["snippet"],
                    "score": score_result(city, item),
                    "query": query,
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame = frame.sort_values(["score", "city"], ascending=[False, True]).reset_index(drop=True)
    return frame


st.title("🏗️ City Permit Search (Salem + Nearby Cities)")
st.caption(
    "Searches across city websites and public pages for potential permit submissions in Salem and nearby Oregon cities."
)

with st.sidebar:
    st.header("Search options")
    permit_type = st.selectbox(
        "Permit type",
        ["building permit", "planning permit", "land use permit", "electrical permit", "plumbing permit"],
        index=0,
    )
    user_query = st.text_input("Extra keywords", placeholder="subdivision, address, applicant name...")
    per_city_limit = st.slider("Results per city", min_value=3, max_value=15, value=8)

    default_cities = [c.name for c in CITIES]
    selected_city_names = st.multiselect("Cities", options=default_cities, default=default_cities)

selected_cities = [c for c in CITIES if c.name in selected_city_names]

search_now = st.button("Search permits")

if search_now:
    if not selected_cities:
        st.warning("Pick at least one city.")
    else:
        with st.spinner("Searching city permit pages..."):
            df = run_search(selected_cities, user_query=user_query, permit_type=permit_type, per_city_limit=per_city_limit)

        if df.empty:
            st.info("No matches found.")
        else:
            st.success(f"Found {len(df)} candidate results.")

            top_only = st.toggle("Show only higher-confidence matches (score >= 5)", value=True)
            out = df[df["score"] >= 5] if top_only else df

            st.dataframe(
                out[["city", "score", "title", "url", "snippet"]],
                use_container_width=True,
                hide_index=True,
            )

            csv = out.to_csv(index=False).encode("utf-8")
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name=f"permit_search_{stamp}.csv",
                mime="text/csv",
            )

            st.subheader("City-specific search links")
            for city in selected_cities:
                query = build_query(city, user_query=user_query, permit_type=permit_type)
                href = "https://duckduckgo.com/?" + urlencode({"q": query})
                st.markdown(f"- **{city.name}**: [open web search]({href})")
else:
    st.info("Set your filters and click **Search permits**.")

st.divider()
st.caption(
    "Note: This tool uses public web indexing and may miss records that are only available behind city permit portals. "
    "For legal verification, confirm entries directly with each city's official permit system."
)
