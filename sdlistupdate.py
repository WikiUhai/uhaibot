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
list_entries = re.findall(item_pattern, table)

if len(list_entries) > 0:
    in_subst = ', '.join(list(map(lambda x: '%s', list_entries)))
    query = "SELECT p.page_title, CASE WHEN p.page_id IN (SELECT cl.cl_from FROM categorylinks cl WHERE cl.cl_to IN ('Redirects_to_Wiktionary', 'All_disambiguation_pages', 'Pages_with_short_description', 'Articles_with_short_description', 'All_redirects_for_discussion')) OR p.page_is_redirect THEN 1 ELSE 0 END FROM page p WHERE p.page_namespace = 0 AND p.page_title IN (%s);" % in_subst

    conn = pymysql.connect(
        host=host,
        read_default_file=credentials,
        database="enwiki_p"
    )

    all_articles = []
    to_remove = []

    with conn.cursor() as cur:
        cur.execute(query, args=list_entries)
        data = cur.fetchall()

        for row in data:
            all_articles.append(str(row[0], encoding='utf-8'))

            if int(row[1]) == 1:
                to_remove.append(str(row[0], encoding='utf-8'))

    conn.close()

    for entry in list_entries:
        if entry not in all_articles:
            to_remove.append(entry)

    if len(to_remove) > 0:
        for entry in to_remove:
            delete_pattern = rf'\| \[\[{re.escape(entry)}\]\] \|\| [0-9]+\n\|-\n'
            page.text = re.sub(delete_pattern, '', page.text)

        page.save('Removed ' + str(len(to_remove)) + ' completed or deleted article' + ('s' if len(to_remove) > 1 else '') + ' (bot)')
