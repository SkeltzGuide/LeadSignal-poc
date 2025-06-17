from bs4 import BeautifulSoup
from typing import List, Dict

def hackernews_parser(soup, base_url):
    results = []

    stories = soup.find_all("tr", class_="athing")
    for story in stories:
        story_id = story.get("id")
        title_elem = story.find("span", class_="titleline")
        if not title_elem:
            continue

        link = title_elem.find("a")
        title = link.text.strip()
        url = link.get("href")

        # Get subtext row, which is right after the current story row
        subtext = story.find_next_sibling("tr")
        time_tag = subtext.select_one(".age")
        timestamp = time_tag.get("title") if time_tag else ""

        results.append({
            "project": "Hackernews",
            "type": "news",
            "name": title,
            "url": url,
            "description": title
        })

    return results[:5]

def timetohire_parser(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    vacancies = []
    cards = soup.select("div.VacatureList__Wrapper__Mk_7J")

    for card in cards:
        # Title
        title_tag = card.select_one("h3.VacatureList__Title__u4746")
        title = title_tag.get_text(strip=True) if title_tag else "No title"

        # URL
        link_tag = card.select_one("a.VacatureList__LinkBtn__3_4n3")
        href = link_tag.get("href") if link_tag else "#"
        url = href if href.startswith("http") else base_url.rstrip("/") + href

        # Description
        desc_tag = card.select_one("div.VacatureList__Content__mfD1j p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        vacancies.append({
            "project": "TTH",
            "type": "job_board",
            "name": title,
            "url": url,
            "description": description
        })

    return vacancies