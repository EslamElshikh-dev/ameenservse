"""Check the generated site's crawl paths, metadata and business identity."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
BUSINESS = json.loads((ROOT / 'business-data.json').read_text())
BASE = BUSINESS['url']


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.ids, self.refs = path, [], []
        self.h1, self.canonical, self.robots = 0, [], ''
        self.schemas, self._schema = [], None
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical.append(a.get('href'))
        if tag == 'meta' and a.get('name') == 'robots':
            self.robots = a.get('content', '')
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self._schema = ''
        for key in ('href', 'src'):
            if a.get(key):
                self.refs.append(a[key])

    def handle_data(self, data):
        if self._schema is not None:
            self._schema += data

    def handle_endtag(self, tag):
        if tag == 'script' and self._schema is not None:
            self.schemas.append(json.loads(self._schema))
            self._schema = None


def file_for(url_path):
    path = ROOT / unquote(url_path).lstrip('/')
    if url_path in ('', '/'):
        return ROOT / 'index.html'
    return path if path.suffix else path.with_suffix('.html')


def check():
    pages = {p: Page(p) for p in ROOT.glob('*.html')}
    checked = 0
    for path, page in pages.items():
        route = '/' if path.stem == 'index' else '/' + path.stem
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
        expected = BUSINESS.get('pageUpdatedOn', {}).get(route, BUSINESS['contentUpdatedOn'])
        assert modified == expected, (route, 'lastmod')
    nav_paths = {'/plumber-riyadh', '/electrician-riyadh'}
    assert all(nav_paths.issubset(set(p.refs)) for p in pages.values())
    service_ids = set(json.loads((ROOT / 'service-media.json').read_text())['services'])
    assert service_ids.issubset(set(pages[ROOT / 'services.html'].ids)), 'missing service destinations'
    assert BUSINESS['reviewUrl'] in pages[ROOT / 'index.html'].refs
    print(f'PASS: {len(pages)} HTML pages, {checked} local references, {len(urls)} sitemap URLs; metadata, anchors and business identity checked.')


if __name__ == '__main__':
    check()
