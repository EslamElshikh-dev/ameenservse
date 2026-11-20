"""Check the generated site's crawl paths, metadata and business identity."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlsplit
from xml.etree import ElementTree
from article_content import POSTS, BY_SLUG, PUBLISHED
from service_routes import DETAIL_PAGES, SERVICE_DESTINATIONS

ROOT = Path(__file__).resolve().parent.parent
BUSINESS = json.loads((ROOT / 'business-data.json').read_text())
BASE = BUSINESS['url']
VERIFICATION_FILE = ROOT / 'google30c987a304e39bc9.html'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.ids, self.refs = path, [], []
        self.h1, self.canonical, self.robots = 0, [], ''
        self.meta, self.title, self.h1_text = {}, '', ''
        self._title, self._h1 = False, False
        self.schemas, self._schema = [], None
        self.service_cards, self._service = {}, None
        self.area_cards, self._area = {}, None
        self._area_heading, self._area_link = False, None
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set(a.get('class', '').split())
        if tag == 'article' and 'local-path-card' in classes and a.get('id', '').startswith('area-'):
            self._area = a['id']
            self.area_cards[self._area] = {'heading': '', 'links': []}
        if self._area is not None:
            if tag == 'h2':
                self._area_heading = True
            if tag == 'a':
                self._area_link = {'href': a['href'], 'text': ''}
                self.area_cards[self._area]['links'].append(self._area_link)
        if tag == 'article' and 'service-card' in classes:
            self._service = a['id']
            self.service_cards[self._service] = {}
        if tag == 'a' and self._service is not None:
            actions = classes & {'service-title-link', 'service-order', 'service-phone'}
            for action in actions:
                self.service_cards[self._service][action] = a['href']
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'h1':
            self.h1 += 1
            self._h1 = True
        if tag == 'title':
            self._title = True
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href'))
        if tag == 'meta' and a.get('name') == 'robots':
            self.robots = a.get('content', '')
        if tag == 'meta':
            self.meta[a.get('name') or a.get('property')] = a.get('content', '')
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self._schema = ''
        for key in ('href', 'src'):
            if a.get(key):
                self.refs.append(a[key])
        if a.get('srcset'):
            self.refs.extend(source.strip().split()[0] for source in a['srcset'].split(','))

    def handle_data(self, data):
        if self._area is not None and self._area_heading:
            self.area_cards[self._area]['heading'] += data
        if self._area_link is not None:
            self._area_link['text'] += data
        if self._title:
            self.title += data
        if self._h1:
            self.h1_text += data
        if self._schema is not None:
            self._schema += data

    def handle_endtag(self, tag):
        if tag == 'article':
            self._service = None
            self._area = None
        if tag == 'h2':
            self._area_heading = False
        if tag == 'a':
            self._area_link = None
        if tag == 'title':
            self._title = False
        if tag == 'h1':
            self._h1 = False
        if tag == 'script' and self._schema is not None:
            self.schemas.append(json.loads(self._schema))
            self._schema = None


def file_for(url_path):
    path = ROOT / unquote(url_path).lstrip('/')
    if url_path in ('', '/'):
        return ROOT / 'index.html'
    return path if path.suffix else path.with_suffix('.html')


def check_area_requests(by_route):
    districts = [
        ('النرجس', 'best-electrician-al-narjis'),
        ('الياسمين', 'best-electrician-al-yasmin'),
        ('العارض', 'best-electrician-al-arid'),
        ('الملقا', 'best-electrician-al-malqa'),
    ]
    north = by_route['/north-riyadh']
    assert 'service-areas' in north.ids
    assert '/north-riyadh#service-areas' in by_route['/electrician-riyadh'].refs
    assert set(north.area_cards) == {f'area-{i}' for i in range(1, 5)}, 'district card count'
    requests = []
    for i, (area, guide) in enumerate(districts, start=1):
        card = north.area_cards[f'area-{i}']
        assert card['heading'] == 'حي ' + area, (area, 'district heading')
        expected_messages = {
            'كهربائي': '\n'.join([
                f'السلام عليكم، أحتاج كهربائي في حي {area}.',
                'نوع الخدمة الكهربائية: ',
                'وصف المشكلة أو العمل المطلوب: ',
            ]),
            'سباك': f'السلام عليكم، أحتاج خدمة سباكة في حي {area}. وصف الطلب: ',
        }
        for service, expected_message in expected_messages.items():
            matches = [link for link in card['links'] if link['text'].strip() == f'اطلب {service} في {area}']
            assert len(matches) == 1, (area, service, 'district request label')
            order_url = urlsplit(matches[0]['href'])
            assert order_url._replace(query='').geturl() == BUSINESS['whatsapp'], (area, service, 'WhatsApp number')
            assert parse_qs(order_url.query) == {'text': [expected_message]}, (area, service, 'district WhatsApp message')
            requests.append(matches[0]['href'])
        assert len([link for link in card['links'] if link['href'].startswith(BUSINESS['whatsapp'])]) == 2, (area, 'district request count')
        guide_links = [link for link in card['links'] if link['href'] == '/blog/' + guide]
        assert len(guide_links) == 1 and area in guide_links[0]['text'], (area, 'district guide')
    assert len(set(requests)) == 8, 'eight unique district requests'


def check():
    assert VERIFICATION_FILE.is_file(), 'missing Google ownership verification file'
    assert VERIFICATION_FILE.read_bytes().rstrip(b'\r\n') == ('google-site-verification: ' + VERIFICATION_FILE.name).encode(), 'Google ownership verification content'
    pages = {p: Page(p) for p in ROOT.rglob('*.html') if '.git' not in p.parts and p != VERIFICATION_FILE}
    by_route = {'/' if p == ROOT / 'index.html' else '/' + p.relative_to(ROOT).with_suffix('').as_posix(): page for p, page in pages.items()}
    checked = 0
    for path, page in pages.items():
        route = '/' if path == ROOT / 'index.html' else '/' + path.relative_to(ROOT).with_suffix('').as_posix()
        assert page.h1 == 1, (path.name, 'H1 count', page.h1)
        assert len(page.ids) == len(set(page.ids)), (path.name, 'duplicate IDs')
        assert page.canonical == [urljoin(BASE, route)], (path.name, 'canonical')
        assert ('noindex' in page.robots) == (route == '/404'), (path.name, 'robots')
        assert len(page.schemas) == 1, (path.name, 'JSON-LD count')
        graph = page.schemas[0]['@graph']
        business = [node for node in graph if node.get('@id') == BASE + '#business']
        assert len(business) == 1 and business[0]['telephone'] == BUSINESS['telephone']
        assert not any(node.get('@type') in ('Review', 'AggregateRating') for node in graph)
        assert len([node['@id'] for node in graph]) == len(set(node['@id'] for node in graph))
        for ref in page.refs:
            target = urlsplit(urljoin(BASE.rstrip('/') + route, ref))
            if target.netloc != urlsplit(BASE).netloc or target.scheme not in ('http', 'https'):
                continue
            local = file_for(target.path)
            assert local.is_file(), (path.name, 'missing local target', ref)
            if target.fragment and local in pages:
                assert unquote(target.fragment) in pages[local].ids, (path.name, 'missing anchor', ref)
            checked += 1
    sitemap = ElementTree.parse(ROOT / 'sitemap.xml')
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = sitemap.findall('s:url', ns)
    assert len(urls) == len(pages) - 1
    for entry in urls:
        loc, modified = entry.find('s:loc', ns).text, entry.find('s:lastmod', ns).text
        local = file_for(urlsplit(loc).path)
        assert local in pages and local.stem != '404'
        assert pages[local].canonical == [loc]
        route = urlsplit(loc).path
        post = BY_SLUG.get(route.removeprefix('/blog/')) if route.startswith('/blog/') else None
        expected = post.get('modified', PUBLISHED) if post else BUSINESS.get('pageUpdatedOn', {}).get(route, BUSINESS['contentUpdatedOn'])
        assert modified == expected, (route, 'lastmod')
        web_page = [node for node in pages[local].schemas[0]['@graph'] if node.get('@id') == loc + '#webpage']
        assert len(web_page) == 1 and web_page[0].get('dateModified') == modified, (route, 'WebPage dateModified vs lastmod')
        if post:
            image = entry.find('{http://www.google.com/schemas/sitemap-image/1.1}image/{http://www.google.com/schemas/sitemap-image/1.1}loc')
            assert image is not None and file_for(urlsplit(image.text).path).is_file(), (route, 'sitemap image')
    assert len({page.title for page in pages.values()}) == len(pages), 'duplicate page titles'
    assert len({page.meta['description'] for page in pages.values()}) == len(pages), 'duplicate descriptions'
    expected_titles = ['افضل سباك', 'أفضل سباك في النرجس', 'افضل سباك في العارض', 'افضل سباك في الياسمين', 'افصل سباك في الملقا', 'افضل كهربائي', 'افضل كهربائي في النرجس', 'افضل كهربائي في الياسمين', 'افضل كهربائي في العارض', 'افضل كهربائي في الملقا', 'تأسيس سباكة', 'تصليح سباكة']
    assert [post['title'] for post in POSTS] == expected_titles
    assert len(BY_SLUG) == len(POSTS) == 12
    photos = {photo['key']: photo for photo in json.loads((ROOT / 'service-media.json').read_text())['photos']}
    for post in POSTS:
        route = '/blog/' + post['slug']
        page = by_route[route]
        assert page.h1_text == post['title'], (route, 'exact requested heading')
        assert page.meta['og:type'] == 'article'
        assert page.meta['og:image'] == BASE + photos[post['photo']]['src']
        assert page.meta['twitter:image'] == page.meta['og:image']
        article = [node for node in page.schemas[0]['@graph'] if node.get('@type') == 'BlogPosting']
        assert len(article) == 1 and article[0]['headline'] == post['title']
        assert article[0]['datePublished'] == PUBLISHED
        assert article[0]['dateModified'] == post.get('modified', PUBLISHED)
        assert article[0]['image'] == [page.meta['og:image']]
        assert article[0]['author']['@id'] == BASE + '#business'
        breadcrumb = next(node for node in page.schemas[0]['@graph'] if node.get('@type') == 'BreadcrumbList')
        assert [item['position'] for item in breadcrumb['itemListElement']] == [1, 2, 3]
        assert breadcrumb['itemListElement'][-1]['name'] == post['title']
        assert route in by_route['/blog'].refs, (route, 'archive discovery')
        assert all('/blog/' + related in page.refs for related in post['related'])
        assert all('article-' + section_id in page.ids for section_id, *_ in post['sections'])
        assert 'article-faq' in page.ids and 'loading="eager"' in page.path.read_text()
    archive = next(node for node in by_route['/blog'].schemas[0]['@graph'] if node.get('@type') == 'ItemList')
    assert archive['numberOfItems'] == len(POSTS)
    reachable, pending = set(), ['/']
    while pending:
        route = pending.pop()
        if route in reachable:
            continue
        reachable.add(route)
        for ref in by_route[route].refs:
            target = urlsplit(urljoin(BASE.rstrip('/') + route, ref))
            if target.netloc == urlsplit(BASE).netloc and target.path in by_route and target.path not in reachable:
                pending.append(target.path)
    assert set(by_route) - {'/404'} <= reachable, 'orphan content pages'
    nav_paths = {'/plumber-riyadh', '/electrician-riyadh'}
    assert all(nav_paths.issubset(set(p.refs)) for p in pages.values())
    check_area_requests(by_route)
    service_ids = set(json.loads((ROOT / 'service-media.json').read_text())['services'])
    directory = by_route['/services']
    assert service_ids == set(directory.service_cards) == set(SERVICE_DESTINATIONS), 'missing service destinations'
    service_data = {node['@id']: node for node in directory.schemas[0]['@graph'] if node.get('@type') == 'Service'}
    for slug, destination in SERVICE_DESTINATIONS.items():
        item = service_data[BASE + 'services#' + slug]
        assert item['url'] == urljoin(BASE, destination), (slug, 'structured destination')
        assert directory.service_cards[slug]['service-title-link'] == destination, (slug, 'directory link')
        for page in (directory, by_route[urlsplit(destination).path]):
            card = page.service_cards[slug]
            order_url = urlsplit(card['service-order'])
            assert order_url._replace(query='').geturl() == BUSINESS['whatsapp'], (slug, 'WhatsApp number')
            message = parse_qs(order_url.query)['text'][0].splitlines()
            assert message == [
                'السلام عليكم، أحتاج خدمة ' + item['name'] + '.',
                'الحي في الرياض: ',
                'وصف المشكلة أو العمل المطلوب: ',
            ], (slug, 'WhatsApp message')
            assert card['service-phone'] == 'tel:' + BUSINESS['telephone']
            assert card['service-order'] == item['availableChannel']['serviceUrl']
    for route, group in DETAIL_PAGES.items():
        page = by_route[route]
        assert page.h1_text == group['title']
        assert page.meta['og:image'] == BASE + photos[group['photo']]['src']
        assert route in directory.refs and route in by_route[group['parent']].refs
        assert set(page.service_cards) == set(group['services'])
        assert all('#' + slug in page.refs for slug in group['services'])
    assert BUSINESS['reviewUrl'] in pages[ROOT / 'index.html'].refs
    review_data = json.loads((ROOT / 'reviews-data.json').read_text())
    assert len(review_data['reviews']) + len(review_data['ratingOnly']) == BUSINESS['reviewSnapshot']['count']
    assert review_data['asOf'] == BUSINESS['reviewSnapshot']['asOf']
    assert len({review['author'] for review in review_data['reviews']}) == len(review_data['reviews'])
    assert all(review.get('text') for review in review_data['reviews'])
    assert all('text' not in review for review in review_data['ratingOnly'])
    for filename, count in [('index.html', 14), ('about.html', 14), ('services.html', 6)]:
        content = (ROOT / filename).read_text()
        assert content.count('class="review-card"') == count, (filename, 'review count')
        assert 'reviews.js?v=20261116-carousel' in content
        assert 'aria-live="polite"' in content and 'إيقاف الحركة' in content
        for review in review_data['reviews'][:count]:
            from html import escape
            assert escape(review['text']) in content, (filename, review['author'], 'quotation')
            assert review['url'] in pages[ROOT / filename].refs
        assert 'AggregateRating' not in content and '"@type": "Review"' not in content
    print(f'PASS: {len(pages)} HTML pages, {checked} local references, {len(urls)} sitemap URLs with matching page dates, {len(service_ids)} service destinations, 8 district WhatsApp requests and the Google verification file.')


if __name__ == '__main__':
    check()
