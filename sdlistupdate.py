import pywikibot as pwb
import re
import pymysql

table_pattern = r'(?<={\| class="wikitable sortable" id="pages"\n! Article !! View count\n\|-\n)((.|\n)*)(?=\|})'
item_pattern = r'\[\[(.*)\]\]'

host = "enwiki.analytics.db.svc.wikimedia.cloud"
credentials = "~/replica.my.cnf"

site = pwb.Site('en', 'wikipedia')
page = pwb.Page(site, 'User:Uhai/Pages_without_short_descriptions_by_view_count')

table = re.findall(table_pattern, page.text)[0][0]
entries = re.findall(item_pattern, table)

in_subst = ', '.join(list(map(lambda x: '%s', entries)))
query = "SELECT p.page_title FROM page p WHERE p.page_namespace = 0 AND (p.page_is_redirect = 1 OR p.page_id IN (SELECT cl.cl_from FROM categorylinks cl WHERE cl.cl_to = 'Articles_with_short_description')) AND p.page_title IN (%s);" % in_subst

conn = pymysql.connect(
    host=host,
    read_default_file=credentials,
    database="enwiki_p"
)

with_sd = []

with conn.cursor() as cur:
    cur.execute(query, args=entries)
    data = cur.fetchall()

    for row in data:
        with_sd.append(str(row[0], encoding='utf-8'))

conn.close()

if len(with_sd) > 0:
    for entry in with_sd:
        delete_pattern = rf'\| \[\[{re.escape(entry)}\]\] \|\| [0-9]+\n\|-\n'
        page.text = re.sub(delete_pattern, '', page.text)

    page.save('Removed ' + str(len(with_sd)) + ' article' + ('s' if len(with_sd) > 1 else '') + ' with short description added (bot)')
