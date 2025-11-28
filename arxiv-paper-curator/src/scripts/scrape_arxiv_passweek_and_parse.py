import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import datetime
import os

BASE_URL = "https://arxiv.org "
SAVE_SCRAPE_WEBPAGE_PATH = "/home/hhy/project/paper-agent/papers-agent/passweek_2000_scrape/"

def fetch_pass_week_papers(category="cs.AI", show=1000):
    """
    从 /list/<category>/pastweek?show=1000 页面抓取数据，
    返回 {date_str: [ {id, version, title} , ... ]} 的字典。

    date_str 形如: "Tue, 11 Nov 2025"
    """
    url = f"{BASE_URL}/list/{category}/pastweek?show={show}"

    headers = {
        "User-Agent": "arxiv-daily-groups-bot/0.1 (mailto:mzthhy@gmail.com)"
    }

    now = datetime.datetime.now().strftime("%Y-%m-%d")
    local_file = os.path.join(SAVE_SCRAPE_WEBPAGE_PATH, category, f"{now}.html")

    if not os.path.exists(local_file):
    
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        text = resp.text
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
        with open(local_file, "w") as f:
            f.write(text)
    else:
        with open(local_file, "r") as f:
            text = f.read()

    soup = BeautifulSoup(text, "html.parser")

    dlpage = soup.find("div", id="dlpage")
    if dlpage is None:
        raise RuntimeError("Cannot find div#dlpage on page – HTML structure changed?")

    # 找到所有h3元素（日期标题）
    all_h3 = dlpage.find_all("h3")

    groups = defaultdict(list)
    current_date = None

    # 修改策略：直接寻找所有h3和紧跟其后的dt/dd对
    for h3 in all_h3:
        current_date = h3.get_text(strip=True).split(" (")[0]  # 去掉"(showing...)"部分

        # 收集紧跟h3后面的所有dt/dd对，直到下一个h3
        dts = []
        dds = []
        current_element = h3.next_sibling

        while current_element:
            if hasattr(current_element, 'name'):
                if current_element.name == 'h3':
                    # 遇到下一个h3，停止收集
                    break
                elif current_element.name == 'dt':
                    dts.append(current_element)
                elif current_element.name == 'dd':
                    dds.append(current_element)
            current_element = current_element.next_sibling

        # dt 和 dd 是一一对应的
        for dt, dd in zip(dts, dds):
                # 找到 arXiv ID：一般在指向 /abs/... 的链接里
                a = dt.find("a", href=re.compile(r"^/abs/"))
                if not a:
                    continue
                raw_id_text = a.get_text(strip=True)  # 例如 "arXiv:2511.07413"
                raw_id_text = raw_id_text.replace("arXiv:", "").strip()

                # 分离出 id 和版本号（如果有 v2、v3）
                m = re.match(r"(?P<id>\d+\.\d+)(v(?P<ver>\d+))?", raw_id_text)
                if m:
                    arxiv_id = m.group("id")
                    version = int(m.group("ver") or 1)
                else:
                    arxiv_id = raw_id_text
                    version = 1

                # 解析标题：div.list-title 里面形如 "Title: xxx"
                title_div = dd.find("div", class_="list-title")
                if title_div:
                    title_text = title_div.get_text(" ", strip=True)
                    # 去掉前缀 "Title:"
                    title_text = re.sub(r"^Title:\s*", "", title_text)
                else:
                    title_text = ""

                groups[current_date].append(
                    {
                        "id": arxiv_id,       # "2511.07413"
                        "version": version,   # 1, 2, ...
                        "title": title_text,  # 论文标题
                    }
                )
    return groups
