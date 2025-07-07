import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser
import re
import requests
import time
from lxml import etree

def parse_with_soup(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    try:
        name = soup.find('th', {'class': 'ddlabel'}).get_text(strip=True).split(' - ')
        table = soup.find('table', {'summary': 'This layout table is used to present the seating numbers.'})
        data = [cell.get_text(strip=True) for cell in table.find_all('td', {'class': 'dddefault'})]
        return name, data
    except AttributeError:
        return None, None

def parse_with_selectolax(html: str):
    tree = HTMLParser(html)
    th = tree.css_first("th.ddlabel")
    if not th:
        return None, None
    name = th.text().split(" - ")

    cells = tree.css("table[summary='This layout table is used to present the seating numbers.'] td.dddefault")
    data = [node.text() for node in cells]
    return name, data

def parse_with_lxml(html: str):
    parser = etree.HTMLParser()
    tree = etree.fromstring(html, parser)
    th_nodes = tree.xpath("//th[@class='ddlabel']/text()")
    if not th_nodes:
        return None, None
    name = [part.strip() for part in th_nodes[0].split(" - ")]

    data = tree.xpath(
        "//table[@summary='This layout table is used to present the seating numbers.']"
        "//td[@class='dddefault']/text()"
    )
    return name, data


_NAME_RE = re.compile(
    r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL
)
_TABLE_RE = re.compile(
    r'<table[^>]*summary=["\']This layout table is used to present the seating numbers\.["\'][^>]*>(.*?)</table>',
    re.IGNORECASE | re.DOTALL
)
_TD_RE = re.compile(r'<td[^>]*class=["\']dddefault["\'][^>]*>([^<]+)</td>', re.IGNORECASE)

def parse_course_regex(html: str):
    m_name = _NAME_RE.search(html)
    if not m_name:
        return None, None
    name = [part.strip().replace('<br />', '').replace('<br>', '') for part in m_name.group(1).split(" - ")]

    m_table = _TABLE_RE.search(html)
    if not m_table:
        return name, []
    snippet = m_table.group(1)
    data = _TD_RE.findall(snippet)
    return name, data

load_dotenv()
ENDPOINT = os.getenv('ENDPOINT')
url = ENDPOINT % (202508, 95175)

print(url)
html = requests.get(url).text
for fn in (parse_with_soup, parse_with_selectolax, parse_with_lxml, parse_course_regex):
    t0 = time.time()
    for _ in range(1000):
        name, data = fn(html)
    print(f"\n{fn.__name__}: {(time.time() - t0)/1000*1000:.2f} ms per call")
    print(f"Name: {name}")
    print(f"Data: {data}")