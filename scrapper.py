import requests
import argparse
import json
import re
from bs4 import BeautifulSoup
from itertools import permutations


def get_tribute_page_link(name: str) -> str:
    # Adams Jesse Leroy -> Jesse Leroy Adams
    name_permutations = ["+".join(p) for p in permutations(name.split())]

    for name_permutation in name_permutations:
        r = requests.get(f'https://www.honorstates.org/index.php?q={name_permutation}')
        if not r.raise_for_status():
            sp = BeautifulSoup(r.text, 'html.parser')
            try:
                link = sp.find("td", class_="qrname").a.get('href')
                return link
            except AttributeError:
                continue
    return False


def get_tribute_page_tree(link: str) -> str:
    r = requests.get(f'{link}')
    if not r.raise_for_status():
        return r.text
    else:
        return False


def parse_tribute(tp: str) -> dict:
    soup = BeautifulSoup(tp, 'html.parser')
    parsed_output = dict()

    parsed_output['title'] = soup.title.text
    parsed_output['name'] = soup.find(class_="h1mega").text
    parsed_output['short_bio'] = "\n".join(
        [sent.strip() for sent in soup.find(class_="hs_container").text.split("★")]
    )

    service_overview_table = [td.text.strip() for td in soup.table.find_all('td')]
    parsed_output['service_overview'] = dict()

    for label, value in zip(service_overview_table[::2], service_overview_table[1::2]):
        parsed_output['service_overview'][f'{label}'] = value

    full_info_headers = [
        header.text.strip() for header in soup.find_all("div", class_=re.compile(".*(headlet)"))
    ]
    full_info_paragraphs = [
        paragraph.text.strip() for paragraph in soup.find_all("div", class_=re.compile(".*(innerwithline)"))
    ]
    parsed_output['full_info'] = dict()

    for header, paragraph in zip(full_info_headers, full_info_paragraphs):
        parsed_output['full_info'][f'{header}'] = paragraph

    return parsed_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple scrapper for https://honorstates.org')
    parser.add_argument('searched_person', type=str, nargs='+',
                        help='a name of a person to look for')
    args = parser.parse_args()
    tribute_page_link = get_tribute_page_link(" ".join(args.searched_person))
    if tribute_page_link:
        print(f'Great! Seems like honorstates has an entry for such person in their DB.')
        with open(f'./{"_".join(args.searched_person)}.json', 'w') as outfile:
            json.dump(parse_tribute(get_tribute_page_tree(tribute_page_link)), outfile, indent=4, sort_keys=False)
    else:
        print(f'Sorry! Seems like honorstates doesn\'t have such person in their DB.')
