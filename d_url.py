import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

zipmods = []

def extract_links(url):
    print(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"请求失败: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    if not table:
        print(f"未找到表格: {url}")
        return
    rows = table.find_all('tr')[2:]  # 跳过标题行

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 4:
            continue

        icon_td = cols[0]
        name_td = cols[1]
        modified_td = cols[2]
        size_td = cols[3]

        a_tag = icon_td.find('a')
        if not a_tag or 'href' not in a_tag.attrs:
            continue

        link = urljoin(url, a_tag['href'])
        name = name_td.text.strip()
        last_modified = modified_td.text.strip()
        size = size_td.text.strip()

        if link.endswith('/'):
            extract_links(link)
        elif link.endswith('.zipmod'):
            zipmods.append((link, name, last_modified, size))

def save_to_csv(filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for i, (link, name_td, last_modified, size) in enumerate(zipmods, start=1):
            writer.writerow([i, link, name_td, last_modified, size])

if __name__ == '__main__':
    start_url = 'https://sideload2.betterrepack.com/download/AISHS2/'
    extract_links(start_url)
    save_to_csv('d_url.csv')
    print(f"已保存 {len(zipmods)} 个 zipmod 链接到 d_url.csv")
