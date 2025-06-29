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
            "resource": "news_board",
            "name": title,
            "url": url,
            "description": title
        })

    return results[:5]

def cegeka_articles_parser(soup, base_url):
    articles = soup.select('wcl-cgk-article-card.article')
    results = []

    for article in articles:
        url = article.get('href', '')

        # Extract title from <h5> inside the article
        title_tag = article.find('h5', class_='spacing_bottom-24 text_weight-semibold')
        title = title_tag.get_text(strip=True) if title_tag else 'Untitled article'

        results.append({
            'name': title,
            'url': url,
            'description': title,
            'project': 'Cegeka',
            'resource': 'Intern nieuws',
            'type': 'news'
        })

    return results[:5]

def cegeka_jobs_parser(soup, base_url="https://www.cegeka.com"):
    results = []

    vacancies = soup.select('div.vacancy.box')
    for vacancy in vacancies:
        link_tag = vacancy.find('a', href=True)
        url = link_tag['href'] if link_tag else ''
        if url and not url.startswith('http'):
            url = base_url + url

        content = vacancy.find('div', class_='vacancy_content')
        if not content:
            continue

        title_tag = content.find('h5')
        title = title_tag.get_text(strip=True) if title_tag else 'Untitled job'

        desc_tag = content.find('p')
        description = desc_tag.get_text(strip=True) if desc_tag else ''

        results.append({
            'name': title,
            'url': url,
            'description': description,
            'project': 'Cegeka',
            'resource': 'Werken bij',
            'type': 'jobs'
        })

    return results[:5]

def ns_jobs_parser(soup, base_url="https://www.werkenbijns.nl"):
    results = []
    
    for item in soup.select("li.vacancy-item-cell"):
        link = item.find("a", class_="vacancy-item", href=True)
        if not link:
            continue
        url = link["href"]
        if not url.startswith("http"):
            url = base_url + url

        # Title
        title_tag = item.select_one(".vacancy-item-titles h3")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled job"

        # Description
        desc_tag = item.select_one(".vacancy-item-body .text")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        results.append({
            "name": title,
            "url": url,
            "description": description,
            "project": "Nederlandse Spoorwegen",
            "resource": "Werken bij",
            "type": "jobs"
        })
    return results[:5]
