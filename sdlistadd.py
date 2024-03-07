import pywikibot as pwb
import re
import pymysql
from datetime import datetime, timedelta
from viewcountreader import ViewCountReader

LIST_NUMBER = 3000
TO_DATE_PATTERN = re.compile(r'(?<=\{\{#EXPR:)[0-9]+(?=\+)')
HEADER_PATTERN = re.compile(r'(?<=\=\= ).*?(?= \=\=)')
TABLE_PATTERN = re.compile(r'(?<=\{\| class\=\"wikitable sortable\" id\=\"pages\"\n! Article !! View count\n\|-\n).*?(?=\|\})', re.DOTALL)
ITEM_PATTERN = re.compile(r'(?<=\[\[).*?(?=\]\])')
QUERY = "SELECT page_title FROM page WHERE page_namespace = 0 AND page_is_redirect = 0 AND page_id NOT IN (SELECT cl_from FROM categorylinks WHERE cl_to IN ('All_disambiguation_pages', 'Pages_with_short_description', 'Articles_with_short_description', 'All_redirects_for_discussion')) AND page_title != 'Main_Page'"

DB_HOST = "enwiki.analytics.db.svc.wikimedia.cloud"
DB_CREDENTIALS = "~/replica.my.cnf"


def get_dump_data():
    vcr = ViewCountReader()
    counts = vcr.run(save=True)
    return counts


def query_database():
    list_articles = []

    conn = pymysql.connect(
        host=DB_HOST,
        read_default_file=DB_CREDENTIALS,
        database="enwiki_p"
    )

    with conn.cursor() as cur:
        cur.execute(QUERY)
        data = cur.fetchall()

        for row in data:
            list_articles.append(str(row[0], encoding='utf-8'))

    conn.close()

    return list_articles


def create_list(dump_data, query_data):
    result = {}

    for item in query_data:
        result[item] = lookup_vc(dump_data, item)

    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:LIST_NUMBER])


def update_page(list):
    site = pwb.Site('en', 'wikipedia')
    page = pwb.Page(site, 'User:Uhai/Pages_without_short_descriptions_by_view_count')

    # Update month/year header
    today = datetime.today()
    previous_month = datetime.today() - timedelta(days=today.day)
    year = previous_month.strftime("%Y")
    month = previous_month.strftime("%B")
    page.text = HEADER_PATTERN.sub(month + ' ' + year, page.text)

    # Update "short descriptions added to date" value
    table = TABLE_PATTERN.findall(page.text)[0]
    list_entries = ITEM_PATTERN.findall(table)
    page.text = TO_DATE_PATTERN.sub(lambda m: str(int(m.group(0)) + (LIST_NUMBER - len(list_entries))), page.text)

    # Add new entries in place of old ones in table
    new_list = '\n'.join(map(lambda vals: f'| [[{vals[0]}]] || {vals[1]}\n|-', list.items()))
    page.text = TABLE_PATTERN.sub(new_list + '\n', page.text)

    page.save('Add data for ' + month + ' ' + year + ' (bot)')


def lookup_vc(dump_data, page_title):
    try:
        if '"' in page_title:
            page_title = page_title.replace('"', '\\"')
            page_title = '"' + page_title + '"'

        return dump_data[page_title]
    except KeyError:
        return 0


if __name__ == '__main__':
    viewcounts = get_dump_data()
    articles = query_database()
    list = create_list(viewcounts, articles)
    update_page(list)
