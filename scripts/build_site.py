"""Build the static Arabic site from one verified business data source; no runtime dependencies."""
import html
import json
import math
import re
from pathlib import Path
from urllib.parse import quote, urlencode
from datetime import date
from article_content import POSTS, BY_SLUG, PUBLISHED
from service_routes import CATEGORY_PAGES, DETAIL_PAGES, SERVICE_DESTINATIONS, SERVICE_GROUPS

ROOT = Path(__file__).resolve().parent.parent
B = json.loads((ROOT / 'business-data.json').read_text())
MEDIA = json.loads((ROOT / 'service-media.json').read_text())
REVIEWS = json.loads((ROOT / 'reviews-data.json').read_text())
PHOTOS = {photo['key']: photo for photo in MEDIA['photos']}
COMPONENTS = json.loads((ROOT / 'site-components.json').read_text())
AREAS = B['serviceAreas']
AREA_ENTITIES = [{'@type': 'City', 'name': 'الرياض'}] + [{'@type': 'Place', 'name': 'حي ' + area + '، الرياض'} for area in AREAS]
FEATURED = ['drain-unblocking', 'tap-installation', 'water-pumps', 'plumbing-installation', 'water-leaks', 'electrical-maintenance', 'breaker-replacement', 'spotlights', 'chandeliers']
BASE = B['url']
ESC = html.escape
MAP = B['mapUrl']
ADDRESS = B['streetAddress'] + '، ' + B['addressLocality'] + ' ' + B['postalCode']
PHONE = B['telephone']
POST_BY_ROUTE = {'/blog/' + post['slug']: post for post in POSTS}


def article_route(post):
    return '/blog/' + post['slug']


def article_reading_time(post):
    text = post['dek'] + ' '.join(section[2] for section in post['sections'])
    return max(1, math.ceil(len(re.sub('<[^>]+>', ' ', text).split()) / 180))


def article_image(photo_key, hero=False):
    photo = PHOTOS[photo_key]
    sizes = '(max-width: 600px) calc(100vw - 36px), (max-width: 900px) calc(100vw - 44px), 800px'
    return f'<img src="/{photo["src"]}" srcset="/{photo["small"]} 480w, /{photo["src"]} 800w" sizes="{sizes}" width="800" height="500" alt="{ESC(photo["alt"])}" loading="{"eager" if hero else "lazy"}" decoding="async"' + (' fetchpriority="high"' if hero else '') + '>'


def article_card(post):
    category = 'السباكة' if post['category'] == 'plumbing' else 'الكهرباء والإنارة'
    route = article_route(post)
    return f'''<article class="guide-card"><a class="guide-card-image" href="{route}" tabindex="-1" aria-hidden="true">{article_image(post['photo'])}<span>{category}</span></a><div class="guide-card-copy"><span class="guide-card-location">{icon('map')} {ESC(post['area'])}<span>{article_reading_time(post)} دقائق قراءة</span></span><h3><a href="{route}">{ESC(post['title'])}</a></h3><p>{ESC(post['focus'])}</p><a class="guide-card-link" href="{route}" aria-label="اقرأ مقال {ESC(post['title'])}">اقرأ الدليل {icon('arrow')}</a></div></article>'''


def article_teasers(slugs, title='أدلة تساعدك قبل طلب الخدمة.'):
    cards = ''.join(article_card(BY_SLUG[slug]) for slug in slugs)
    return '<section class="section guide-reading"><div class="wrap">' + section_heading('من مقالات أمين سرور', title, 'إجابات عملية لاختيار الخدمة وتجهيز الطلب ومناقشة نطاق العمل.', button('/blog', 'كل المقالات', 'outline')) + '<div class="guide-grid">' + cards + '</div></div></section>'


def article_archive():
    navigation = '<nav class="guide-categories" aria-label="أقسام المقالات"><a href="#plumbing-guides">مقالات السباكة <span>7</span></a><a href="#electrical-guides">مقالات الكهرباء <span>5</span></a><a href="#request-guide">جهّز طلبك</a></nav>'
    groups = ''
    for category, heading, section_id in [('plumbing', 'من تسرب صغير إلى تأسيس متكامل.', 'plumbing-guides'), ('electrical', 'من أول نقطة إلى آخر لمسة إنارة.', 'electrical-guides')]:
        selected = [post for post in POSTS if post['category'] == category]
        groups += f'<section class="section guide-archive-section" id="{section_id}" aria-labelledby="{section_id}-title"><div class="wrap"><div class="guide-group-heading"><span class="eyebrow">{"أدلة السباكة" if category == "plumbing" else "أدلة الكهرباء"}</span><h2 id="{section_id}-title">{heading}</h2></div><div class="guide-grid">' + ''.join(article_card(post) for post in selected) + '</div></div></section>'
    return '<div class="wrap">' + navigation + '</div>' + groups


def article_page(post):
    category = 'السباكة' if post['category'] == 'plumbing' else 'الكهرباء والإنارة'
    service = '/plumber-riyadh' if post['category'] == 'plumbing' else '/electrician-riyadh'
    default_request = 'مرحبًا أمين سرور، قرأت مقال ' + post['title'] + ' وأرغب في تنسيق الخدمة. الحي: ' + post['area'] + '. تفاصيل الطلب: '
    request = wa(post.get('request_message', default_request))
    form_params = {'service': post.get('request_service', 'خدمات السباكة' if post['category'] == 'plumbing' else 'صيانة الكهرباء')}
    if post['area'] in AREAS:
        form_params['area'] = post['area']
    request_form = '/contact?' + urlencode(form_params) + '#request'
    toc = ''.join(f'<li><a href="#article-{section_id}"><span>{i + 1:02}</span>{ESC(heading)}</a></li>' for i, (section_id, heading, _) in enumerate(post['sections']))
    sections = ''
    for i, (section_id, heading, content) in enumerate(post['sections']):
        sections += f'<section class="guide-body-section" aria-labelledby="article-{section_id}"><h2 id="article-{section_id}">{ESC(heading)}</h2>{content}</section>'
        if i == 1:
            photo = PHOTOS[post['secondary']]
            sections += '<figure class="guide-inline-image">' + article_image(post['secondary']) + '<figcaption>' + ESC(photo['alt']) + '</figcaption></figure>'
    questions = ''.join(f'<details><summary>{ESC(question)}{icon("plus")}</summary><p>{ESC(answer)}</p></details>' for question, answer in post['faqs'])
    related = ''.join(article_card(BY_SLUG[slug]) for slug in post['related'])
    points = ''.join('<li>' + icon('check') + '<span>' + ESC(point) + '</span></li>' for point in post['takeaways'])
    hero_photo = PHOTOS[post['photo']]
    return f'''<article class="guide-article" aria-labelledby="article-title"><header class="guide-hero"><div class="wrap"><nav class="breadcrumbs" aria-label="مسار التنقل"><a href="/">الرئيسية</a><span>/</span><a href="/blog">المقالات ودليل العميل</a><span>/</span><span aria-current="page">{ESC(post['title'])}</span></nav><div class="guide-hero-grid"><div class="guide-hero-copy"><div class="guide-labels"><a href="{service}">{category}</a><span>{ESC(post['area'])}</span></div><h1 id="article-title">{ESC(post['title'])}</h1><p class="guide-dek">{ESC(post['dek'])}</p><div class="guide-meta"><span>نشر: <a href="/about">أمين سرور</a></span><time datetime="{PUBLISHED}">{arabic_date(PUBLISHED)}</time><span>{article_reading_time(post)} دقائق قراءة</span></div><a class="guide-start" href="#article-content">ابدأ القراءة {icon('arrow')}</a></div><figure class="guide-hero-image">{article_image(post['photo'], True)}<figcaption>{ESC(hero_photo['alt'])}</figcaption></figure></div></div></header><div class="wrap"><section class="guide-takeaways" aria-labelledby="takeaways-title"><h2 id="takeaways-title">ثلاث نقاط تبدأ منها</h2><ul>{points}</ul></section><div class="guide-layout" id="article-content"><aside class="guide-sidebar"><nav class="guide-toc" aria-labelledby="toc-title"><h2 id="toc-title">في هذا المقال</h2><ol>{toc}<li><a href="#article-faq"><span>؟</span>أسئلة قبل طلب الخدمة</a></li></ol></nav><div class="guide-help"><span class="eyebrow">من القراءة إلى طلب واضح</span><h2>وش يحتاج بيتك؟</h2><p>أرسل الحي ووصف الحالة لتأكيد التوفر وتنسيق الزيارة مع أمين سرور.</p>{button(request, 'أرسل تفاصيل الطلب', 'primary', 'whatsapp')}{button('tel:' + PHONE, 'اتصال بأمين سرور', 'outline', 'phone')}<a class="guide-service-link" href="{service}">استكشف نطاق الخدمة {icon('arrow')}</a></div></aside><div class="guide-article-body">{sections}<section class="guide-faq" aria-labelledby="article-faq"><span class="eyebrow">تفاصيل تهمك</span><h2 id="article-faq">أسئلة قبل طلب الخدمة</h2><div class="accordion">{questions}</div></section><div class="guide-endnote"><p>هل تحتاج توضيح نطاق طلبك؟ راجع <a href="{service}">تفاصيل خدمات {category}</a>، أو استخدم <a href="{ESC(request_form)}">نموذج تجهيز رسالة واتساب</a> لإرسال المعلومات التي تخص حالتك.</p><a href="/blog">العودة إلى كل المقالات {icon('arrow')}</a></div></div></div></div><section class="section guide-related" aria-labelledby="related-title"><div class="wrap"><span class="eyebrow">كمّل الصورة</span><h2 id="related-title">أدلة مرتبطة باحتياجك</h2><div class="guide-grid">{related}</div></div></section></article>{cta()}'''

# Service names reflect the Business Profile and existing website specialties.
SERVICES = [
 ('pipe-repair','إصلاح أنابيب السباكة','plumbing','إصلاح مواسير المياه والصرف والوصلات المتضررة، ومعالجة التسرب حسب حالة التمديدات وإمكانية الوصول إلى موضع العطل.','pipe'),
 ('toilet-repair','إصلاح المراحيض','plumbing','معالجة مشكلات السيفون والتعبئة والتسرب في المرحاض، وفحص الوصلات لتحديد القطعة التي تحتاج إلى إصلاح أو استبدال.','water'),
 ('showers','تركيب دُشّ','plumbing','تركيب أطقم الدش وتجهيز نقاط تغذية المياه، وضبط التوصيلات والتثبيت وتجربة التشغيل بعد التركيب.','water'),
 ('water-heater-installation','تركيب سخّانات مياه','plumbing','تركيب سخان المياه وتوصيل مداخل ومخارج المياه ومصدر التشغيل، ومراجعة التثبيت والصمامات بحسب نوع السخان.','water'),
 ('outdoor-plumbing','إصلاح أنظمة السباكة الخارجية','plumbing','فحص وإصلاح مواسير ووصلات السباكة الخارجية المتضررة، وتحديد نطاق العمل وفق طبيعة الموقع وحالة الشبكة.','pipe'),
 ('water-tank-repair','إصلاح خزّانات الماء','plumbing','فحص مشكلات الخزان والوصلات والصمامات المرتبطة به، وتحديد أعمال الإصلاح المناسبة حسب نوعه وحالته.','water'),
 ('pool-plumbing','إصلاح سباكة المسابح','plumbing','مراجعة مشكلات مواسير ووصلات سباكة المسبح وتحديد الجزء المتضرر. تُحدّد إمكانية التنفيذ ونطاق الإصلاح بعد معرفة تفاصيل الموقع.','water'),
 ('water-heater-repair','إصلاح سخّانات المياه','plumbing','فحص التسرب وضعف التسخين ومشكلات توصيلات السخان، وتحديد سبب العطل والصيانة أو الاستبدال المطلوب.','water'),
 ('plumbing-services','خدمات السباكة','plumbing','خدمات سباكة للمنازل والشقق والفلل في الرياض، تشمل أعمال التركيب والتأسيس والصيانة بحسب الطلب وحالة الموقع.','pipe'),
 ('plumbing-maintenance','تصليح وصيانة السباكة','plumbing','صيانة الخلاطات والسيفونات والوصلات ونقاط المياه والصرف، ومعالجة الأعطال الظاهرة بعد تحديد السبب.','tool'),
 ('basins','تركيب وتصليح مغاسل','plumbing','تركيب المغاسل وتوصيل تغذية المياه والصرف، ومعالجة تسرب الوصلات ومشكلات الاستخدام في الحمامات والمطابخ.','water'),
 ('plumbing-emergency','سباك طوارئ','plumbing','طلبات السباكة العاجلة مثل التسرب المفاجئ أو انفصال الوصلات. اشرح الحالة وأرسل موقعك لتأكيد التوفر وتنسيق الزيارة.','clock'),
 ('plumbing-installation','تأسيس وتمديد شبكات السباكة','plumbing','تأسيس وتجديد تمديدات المياه والصرف، وتجهيز نقاط الحمامات والمطابخ ومراجعة المسارات قبل التشطيب.','pipe'),
 ('water-leaks','كشف وإصلاح تسربات المياه','plumbing','فحص علامات التسرب وتحديد مصدره في المواسير والوصلات ونقاط الحمامات والمطابخ، ثم معالجة الجزء المتضرر.','water'),
 ('electrical-maintenance','صيانة الكهرباء','electrical','فحص أعطال التوصيلات والقواطع ونقاط الإنارة، وتحديد الإصلاح المناسب لحالة الكهرباء في المنزل أو الفيلا.','bolt'),
 ('electrical-installation','تأسيس الكهرباء','electrical','تجهيز مسارات الأسلاك ونقاط المفاتيح والأفياش والإنارة ولوحات التوزيع بحسب احتياجات المكان ونطاق العمل.','bolt'),
 ('electrical-repair','تصليح كهرباء','electrical','تحديد سبب توقف الدائرة أو نقطة الكهرباء ومعالجة التوصيلات أو القطع المتضررة بعد الفحص.','tool'),
 ('chandeliers','تركيب ثريات','electrical','تركيب الثريات وتجهيز التوصيل والتثبيت المناسب لنوعها ووزنها ونوع السقف، ثم تجربة الإنارة.','light'),
 ('decorative-chandeliers','تركيب ثريات كريستال ورخام','electrical','تركيب الثريات الديكورية مع مراجعة وزن القطعة ونقاط التعليق والتوصيل. أرسل صورة الثريا والسقف لتوضيح متطلبات التركيب.','light'),
 ('lighting-panels','تركيب لوحات اضاءة','electrical','تركيب لوحات ووحدات الإضاءة، وتجهيز نقاط التوصيل وتثبيتها بالشكل المناسب للمكان.','light'),
 ('electrical-panels','تركيب طابلون كهرباء','electrical','تركيب لوحة توزيع الكهرباء وتنظيم التوصيلات والقواطع وفق متطلبات المكان، مع مراجعة الدوائر قبل التشغيل.','bolt'),
 ('short-circuit','إصلاح التماس الكهرباء','electrical','فحص تكرار فصل القاطع أو توقف جزء من الدائرة، وتحديد موضع الخلل في الأسلاك والتوصيلات وإصلاح الجزء المتضرر.','bolt'),
 ('wire-repair','إصلاح الأسلاك الكهربائية','electrical','فحص الأسلاك والتوصيلات الكهربائية المتضررة وتحديد موضع الخلل، ثم الإصلاح أو الاستبدال المناسب حسب حالة التمديدات.','tool'),
 ('switch-repair','إصلاح مقابس ومفاتيح كهربائية','electrical','فحص الأفياش والمفاتيح التي لا تعمل أو تعاني من ضعف التوصيل، واستبدال القطعة المتضررة واختبار التشغيل.','bolt'),
 ('lighting','تركيب تجهيزات إنارة','electrical','تركيب واستبدال وحدات الإنارة والسبوت لايت وLED والثريات، وتجهيز نقاط الكهرباء والتثبيت وتجربة الإضاءة.','light'),
 ('wiring','مدّ الأسلاك الكهربائية','electrical','تمديد وتجديد الأسلاك وتجهيز مسارات ونقاط الإنارة والأفياش والمفاتيح وتنظيم التوصيلات وفحص الدوائر.','bolt'),
]

SERVICE_EXTENSIONS = [
 ('drain-unblocking','تسليك الأحواض وفتحات الصرف','plumbing','فحص بطء التصريف وانسداد الأحواض وفتحات الصرف الداخلية، ومعالجة الانسداد القابل للوصول بالطريقة المناسبة لحالة المواسير وموقعه.','pipe'),
 ('tap-installation','تركيب وتغيير خلاطات المياه','plumbing','فك الخلاط المتضرر وتركيب خلاطات المغاسل والمطابخ والدش، مع فحص المحابس والوصلات وتجربة تدفق المياه بعد التركيب.','water'),
 ('water-pumps','تركيب وصيانة مضخات المياه','plumbing','فحص مشكلات تشغيل مضخة المياه وتوصيلاتها، وتركيب أو استبدال المضخة المناسبة بعد مراجعة نوعها وحالة الشبكة ومتطلبات الموقع.','tool'),
 ('water-pressure','فحص ضعف ضغط المياه','plumbing','تحديد أسباب ضعف تدفق الماء في الخلاطات والدش، ومراجعة المحابس والتوصيلات والمضخة عند الحاجة قبل تحديد الإصلاح المناسب.','water'),
 ('cistern-float','تغيير عوامة السيفون وقطع التعبئة','plumbing','معالجة استمرار نزول الماء أو بطء تعبئة صندوق الطرد، وفحص عوامة السيفون وصمام التعبئة واستبدال القطعة المناسبة عند الحاجة.','water'),
 ('water-valves','تغيير محابس ووصلات المياه','plumbing','فك واستبدال محابس المياه والوصلات المتضررة في نقاط الحمام والمطبخ، ومراجعة مقاس القطع والتوصيل وفحص التسرب بعد العمل.','pipe'),
 ('breaker-replacement','فحص وتغيير القواطع الكهربائية','electrical','فحص سبب تكرار فصل القاطع ومراجعة الدائرة والأحمال المتصلة، ثم استبدال القاطع المتضرر بالمواصفات المناسبة بعد تحديد سبب المشكلة.','bolt'),
 ('socket-installation','تركيب مقابس ومفاتيح كهربائية','electrical','تركيب واستبدال الأفياش والمفاتيح ومراجعة التوصيلات والتثبيت داخل العلب، ثم فحص عمل النقاط التي جرى تركيبها.','bolt'),
 ('spotlights','تركيب سبوت لايت','electrical','تركيب وتجديد السبوت لايت مع مراجعة مقاس فتحات السقف والتوصيلات ومواصفات الوحدة، ثم تجربة الإضاءة بعد التثبيت.','light'),
 ('electrical-emergency','كهربائي للأعطال العاجلة','electrical','استقبال طلبات انقطاع الكهرباء المفاجئ أو تكرار فصل القاطع. اشرح الحالة وأرسل اسم الحي لتأكيد التوفر وتنسيق الزيارة.','clock'),
]
SERVICES += SERVICE_EXTENSIONS
SERVICES += [
 ('faucet-repair','إصلاح صنابير المياه','plumbing','فحص التنقيط أو ضعف التدفق من الصنبور وتحديد سبب المشكلة في الصنبور أو الوصلة، ثم مراجعة التشغيل بعد الإصلاح.','water'),
 ('faucet-installation','تركيب صنابير المياه','plumbing','تركيب أو استبدال صنابير المياه بعد مراجعة مقاس نقطة التغذية وحالة التوصيلات، ثم تجربة الصنبور وفحص الوصلات.','water'),
 ('toilet-installation','تركيب مراحيض','plumbing','تركيب المرحاض ومراجعة توافق نقطة الصرف وتغذية المياه وطريقة التثبيت، ثم تجربة التعبئة والتصريف بعد العمل.','water'),
 ('led-lighting','تركيب إنارة LED','electrical','تركيب أو استبدال وحدات LED في المنازل والشقق والفلل، مع مراجعة المقاس ونقطة التغذية وطريقة التثبيت وتجربة الإنارة.','light'),
 ('lighting-repair','صيانة وإصلاح الإنارة المنزلية','electrical','فحص وحدات الإنارة التي تتقطع أو تتوقف ومراجعة المفتاح والتوصيلات المرتبطة بها، ثم تحديد الإصلاح المناسب وتجربة التشغيل.','light'),
 ('lighting-replacement','استبدال وحدات الإنارة','electrical','استبدال وحدات الإنارة القديمة أو المتضررة بعد مراجعة المقاس وطريقة التثبيت وتوافق الوحدة البديلة مع نقاط الكهرباء القائمة.','light'),
 ('lighting-point-wiring','تمديد وتجديد نقاط الإنارة','electrical','تجهيز أو تجديد نقاط الإنارة حسب توزيع الوحدات والأثاث ومرحلة التشطيب، مع مراجعة المسارات والتوصيلات قبل التنفيذ.','bolt'),
]
SERVICES_BY_SLUG = {service[0]: service for service in SERVICES}
assert sorted(SERVICES_BY_SLUG) == sorted(slug for group in SERVICE_GROUPS.values() for slug in group['services'])
SERVICE_COUNTS = {cat: sum(s[2] == cat for s in SERVICES) for cat in ('plumbing', 'electrical')}
REVIEW_SNAPSHOT = B['reviewSnapshot']
assert REVIEWS['asOf'] <= REVIEW_SNAPSHOT['asOf']  # Review quotations and the rating summary retain independent source dates.

def arabic_date(value):
    d = date.fromisoformat(value)
    months = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
    return f'{d.day} {months[d.month - 1]} {d.year}'

FAQ = [
 ('ما الخدمات المتاحة لدى أمين سرور؟','نقدم تأسيس وصيانة السباكة وإصلاح المواسير والتسربات وتركيب الأدوات الصحية والسخانات، إلى جانب تأسيس وصيانة الكهرباء وإصلاح الأعطال وتركيب لوحات التوزيع والثريات والإنارة. تجد تفاصيل الخدمات في صفحة الخدمات.'),
 ('أين يقع أمين سرور وما نطاق الخدمة؟', f'عنوان النشاط في {ADDRESS}. تشمل الخدمة مدينة الرياض، ويمكن إرسال اسم الحي أو رابط الموقع على واتساب لتأكيد إمكانية الزيارة والموعد المناسب.'),
 ('ما ساعات العمل؟','العمل على مدار الساعة، طوال أيام الأسبوع، وفق المواعيد الحالية للنشاط. تواصل مباشرة لتأكيد التوفر وموعد الزيارة حسب الخدمة والموقع.'),
 ('كيف أطلب سباكًا أو كهربائيًا؟','اتصل على 0545350293 أو افتح واتساب من الموقع. اذكر الخدمة ووصف المشكلة واسم الحي، وأرسل صورًا واضحة عند الإمكان لتوضيح الطلب قبل تنسيق الزيارة.'),
 ('هل توجد أسعار ثابتة لجميع الخدمات؟','تختلف التكلفة بحسب نوع العطل وحالة التمديدات وقطع الغيار ونطاق العمل. أرسل تفاصيل الطلب للاستفسار، ووضّح الأعمال المطلوبة والتكلفة المتفق عليها قبل التنفيذ.'),
 ('هل تنفذون أعمال التأسيس للمنازل والفلل؟','نعم، تشمل الخدمات تأسيس وتمديد شبكات المياه والصرف والكهرباء للمنازل والشقق والفلل. أرسل مرحلة المشروع واحتياجاته لتنسيق المعاينة وتحديد نطاق التنفيذ.'),
]

ICON_PATHS = {
 'phone':'<path d="M7 3H4a1 1 0 0 0-1 1c0 9.4 7.6 17 17 17a1 1 0 0 0 1-1v-3l-5-2-2 2a15 15 0 0 1-7-7l2-2-2-5Z"/>',
 'chat':'<path d="M21 11.5a9 9 0 0 1-9 9 10 10 0 0 1-4-1L3 21l1.5-5a9 9 0 1 1 16.5-4.5Z"/><path d="m8 8 1 3 3 3 3 1 1-2-2-1-1 1-3-3 1-1-1-2Z"/>',
 'arrow':'<path d="M19 12H5m6-6-6 6 6 6"/>',
 'map':'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'bolt':'<path d="m13 2-9 12h7l-1 8 10-13h-7l1-7Z"/>',
 'water':'<path d="M12 2S4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z"/><path d="M8 16a4 4 0 0 0 4 4"/>',
 'pipe':'<path d="M3 5h8v5h6v9h-6v-4H6V5M1 5h12M10 10v5M17 8v13M9 19h10"/>',
 'light':'<path d="M9 18h6m-6 3h6M8 13a6 6 0 1 1 8 0c-1.3 1-1.5 2-1.5 3h-5c0-1-.2-2-1.5-3ZM12 1v1M2 9h1m18 0h1M4 3l1 1m14-1-1 1"/>',
 'tool':'<path d="M20 4a6 6 0 0 1-8 8l-7 8a2 2 0 1 1-3-3l8-7a6 6 0 0 1 8-8l-4 4 4 2 2-4Z"/>',
 'check':'<path d="m5 12 4 4L19 6"/>',
 'star':'<path d="m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z"/>',
 'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
 'plus':'<path d="M12 5v14M5 12h14"/>',
 'instagram':'<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
 'home':'<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7"/>',
}
SPRITE = '<svg class="sprite" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + ''.join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k,v in ICON_PATHS.items()) + '</svg>'

def icon(name, variant='green'):
    if name == 'whatsapp':
        assert variant in ('green', 'white', 'black')
        return f'<img class="icon icon-whatsapp" src="/assets/whatsapp-{variant}.svg" width="24" height="24" alt="" aria-hidden="true">'
    return f'<svg class="icon" aria-hidden="true" focusable="false"><use href="#i-{name}"></use></svg>'

def wa(text='مرحبًا، أرغب في الاستفسار عن خدمات السباكة وصيانة الكهرباء في الرياض.'):
    return B['whatsapp'] + '?text=' + quote(text)

def service_request(name):
    return wa(f'السلام عليكم، أحتاج خدمة {name}.\nالحي في الرياض: \nوصف المشكلة أو العمل المطلوب: ')

def button(href, text, kind='primary', glyph='arrow', extra=''):
    external = ' target="_blank" rel="noopener noreferrer"' if href.startswith('https://') else ''
    glyph_markup = icon('whatsapp', 'white' if kind in ('primary', 'outline-light') else ('black' if kind == 'gold' else 'green')) if href.startswith(B['whatsapp']) else icon(glyph)
    return f'<a class="button button-{kind}" href="{ESC(href)}"{external} {extra}>{glyph_markup}<span>{text}</span></a>'

NAV = [('/plumber-riyadh','السباكة'),('/electrician-riyadh','الكهرباء'),('/services','كل الخدمات'),('/#work','أعمالنا'),('/#reviews','آراء العملاء'),('/blog','المقالات'),('/contact','تواصل معنا')]

def header(path):
    links=''.join(f'<a href="{u}"'+(' aria-current="page"' if u==path or (u in ('/blog', '/services') and path.startswith(u + '/')) else '')+f'>{n}</a>' for u,n in NAV)
    return f'''<div class="topline"><div class="wrap"><span>{icon('map')} النرجس، الرياض</span><span>{icon('clock')} على مدار الساعة · طوال الأسبوع</span><a href="{ESC(MAP)}" target="_blank" rel="noopener noreferrer">موقعنا على الخريطة {icon('arrow')}</a></div></div>
<header class="site-header" id="top"><div class="wrap header-inner"><a class="brand" href="/" aria-label="أمين سرور، الصفحة الرئيسية"><img src="/assets/brand-mark.svg" width="52" height="52" alt=""><span><strong>أمين سرور</strong><small>للسباكة وصيانة الكهرباء</small></span></a><nav id="main-nav" aria-label="التنقل الرئيسي">{links}</nav><a class="header-call" aria-label="اتصل بأمين سرور على 0545350293" href="tel:{PHONE}">{icon('phone')}<b dir="ltr">{B['displayPhone']}</b></a><button class="menu-toggle" aria-label="فتح القائمة" aria-controls="main-nav" aria-expanded="false">{icon('menu')}</button></div></header>'''

def footer():
    return f'''<footer class="site-footer"><div class="wrap footer-grid"><div class="footer-about"><a class="brand" href="/"><img src="/assets/brand-mark.svg" width="50" height="50" alt=""><span><strong>أمين سرور</strong><small>للسباكة وصيانة الكهرباء</small></span></a><p>أعمال التأسيس والصيانة للسباكة والكهرباء في المنازل والشقق والفلل بالرياض. تواصل مباشرة واشرح طلبك لتنسيق الخدمة.</p><a class="social-link" href="{B['instagram']}" target="_blank" rel="noopener noreferrer">{icon('instagram')} تابع أعمالنا على إنستغرام</a></div><div><h2>استكشف الموقع</h2><div class="footer-links"><a href="/services">كل الخدمات</a><a href="/plumber-riyadh">سباك بالرياض</a><a href="/electrician-riyadh">كهربائي بالرياض</a><a href="/north-riyadh">مناطق الخدمة في شمال الرياض</a><a href="/#work">صور من أعمالنا</a><a href="/#reviews">آراء العملاء على Google</a><a href="/about">عن أمين سرور</a><a href="/blog">المقالات ودليل العميل</a><a href="/contact">التواصل والموقع</a></div></div><div><h2>بيانات التواصل</h2><a class="contact-line" href="tel:{PHONE}">{icon('phone')}<b dir="ltr">{B['displayPhone']}</b></a><p class="contact-line">{icon('map')}<span>{ESC(ADDRESS)}</span></p><p class="contact-line">{icon('clock')}<span>24 ساعة، 7 أيام في الأسبوع</span></p></div></div><div class="wrap footer-bottom"><p>© <span id="current-year">2026</span> {B['name']}</p>{COMPONENTS['developerCreditHtml']}</div></footer><nav class="contact-dock" aria-label="التواصل السريع"><a class="floating-contact floating-whatsapp" href="{ESC(wa())}" target="_blank" rel="noopener noreferrer" aria-label="تواصل مع أمين سرور عبر واتساب">{icon('whatsapp')}<span class="floating-label" aria-hidden="true">تواصل عبر واتساب</span></a><a class="floating-contact floating-phone" href="tel:{PHONE}" aria-label="اتصل بأمين سرور على 0545350293">{icon('phone')}<span class="floating-label" aria-hidden="true">اتصل الآن</span></a></nav>'''

def section_heading(kicker, title, intro='', link=''):
    return f'<div class="section-heading"><div><span class="eyebrow">{kicker}</span><h2>{title}</h2>'+ (f'<p>{intro}</p>' if intro else '') + '</div>' + link + '</div>'

def page_intro(title, intro, label):
    return f'<section class="page-intro"><div class="wrap"><nav class="breadcrumbs" aria-label="مسار التنقل"><a href="/">الرئيسية</a><span>/</span><span aria-current="page">{label}</span></nav><span class="eyebrow">أمين سرور · الرياض</span><h1>{title}</h1><p>{intro}</p></div></section>'

def service_card(service, index, current_path):
    slug, name, cat, desc, glyph=service
    href = service_request(name)
    destination = SERVICE_DESTINATIONS[slug]
    title = ESC(name)
    if current_path != destination.split('#')[0]:
        title = f'<a class="service-title-link" href="{destination}">{title}{icon("arrow")}</a>'
    details=MEDIA['services'][slug]
    photo=PHOTOS[details['photo']]
    category='أعمال السباكة' if cat=='plumbing' else 'الكهرباء والإنارة'
    points=''.join(f'<li>{icon("check")}<span>{ESC(point)}</span></li>' for point in details['points'])
    variant='white' if cat=='plumbing' else 'black'
    return f'''<article class="service-card service-card--{cat}" id="{slug}" data-category="{cat}"><div class="service-media"><img src="/{photo['src']}" srcset="/{photo['small']} 480w, /{photo['src']} 800w" sizes="(max-width: 600px) 92vw, (max-width: 920px) 46vw, 410px" width="800" height="500" alt="{ESC(photo['alt'])}" loading="lazy" decoding="async"><span class="service-photo-badge">{icon(glyph)}{category}</span><span class="service-photo-number" aria-hidden="true">{index:02d}</span></div><div class="service-copy"><h3>{title}</h3><p>{ESC(desc)}</p><ul class="service-points" aria-label="تفاصيل الخدمة">{points}</ul><div class="service-actions"><a class="service-order" data-service-name="{ESC(name)}" href="{ESC(href)}" target="_blank" rel="noopener noreferrer" aria-label="اطلب خدمة {ESC(name)} عبر واتساب">{icon('whatsapp',variant)}<span>اطلب عبر واتساب</span>{icon('arrow')}</a><a class="service-phone" href="tel:{PHONE}" aria-label="اتصل لطلب خدمة {ESC(name)} على 0545350293">{icon('phone')}</a></div></div></article>'''

def cta():
    return f'<section class="section cta-section" id="contact"><div class="wrap cta-panel"><div><span class="eyebrow">خلّنا نعرف وش تحتاج</span><h2>عطل بسيط أو تأسيس جديد؟<br>ابدأ بتواصل مباشر.</h2><p>اشرح طلبك وأرسل صور المكان واسم الحي. ننسّق معك الخدمة والموعد حسب تفاصيل الطلب.</p></div><div class="cta-actions">{button(wa(),'أرسل تفاصيل طلبك','gold','chat')}{button("tel:"+PHONE,'<b dir="ltr">'+B['displayPhone']+'</b>','outline-light','phone')}<span>{icon('clock')} العمل على مدار الساعة</span></div></div></section>'

def faq():
    return '<section class="section faq-section" id="faq"><div class="wrap faq-layout"><div>'+section_heading('إجابات تهمك','قبل ما تطلب الخدمة','معلومات واضحة عن الخدمات والتواصل والمواعيد.')+button('/contact','عندك استفسار آخر؟','outline','chat')+'</div><div class="accordion">'+''.join(f'<details><summary>{q}{icon("plus")}</summary><p>{a}</p></details>' for q,a in FAQ)+'</div></div></section>'

def location():
    return f'''<section class="section location-section" id="areas"><div class="wrap location-layout"><div>{section_heading('قريب من تفاصيل بيتك','في النرجس، ونخدم الرياض.','تأسيس وصيانة السباكة والكهرباء داخل مدينة الرياض. أرسل موقعك ونوع الخدمة لتنسيق الزيارة.')}<address>{icon('map')}<span>{ADDRESS}</span></address><div class="location-actions">{button(MAP,'افتح الموقع على خرائط Google','primary','map')}{button('/contact','تفاصيل التواصل','outline')}</div><p class="small-note">لتنسيق الزيارة أو الاستفسار عن الوصول، تواصل معنا أولًا.</p></div><div class="map-card"><div class="map-card-head"><span>{icon('map')} موقع أمين سرور</span><span>الرياض · النرجس</span></div><iframe title="موقع أمين سرور في حي النرجس بالرياض" src="https://www.google.com/maps?q=أمين%20سرور%20لخدمات%20السباكة%20وصيانة%20الكهرباء&amp;cid=809316932329652691&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe><a href="{ESC(MAP)}" target="_blank" rel="noopener noreferrer">عرض الموقع والاتجاهات {icon('arrow')}</a></div></div></section>'''

def work():
    images=[('interior','تركيبات مغاسل وإنارة داخلية','مغاسل وتجهيزات إنارة داخلية من صور أعمال أمين سرور'),('basins','تركيب وتجهيز المغاسل','تركيب مغاسل وخلاطات من أعمال أمين سرور'),('showroom','الأدوات وتجهيزات السباكة','أدوات وتجهيزات السباكة الظاهرة في صور ملف أمين سرور')]
    return '<section class="section work-section" id="work"><div class="wrap">'+section_heading('الصورة توضح التفاصيل','من أعمالنا وتجهيزاتنا.','صور حقيقية من الملف التجاري لأمين سرور.',button(B['instagram'],'شاهد المزيد','outline','instagram'))+'<div class="work-grid">'+''.join(f'<figure><img src="/assets/{name}.webp" srcset="/assets/{name}-sm.webp 480w, /assets/{name}.webp 960w" sizes="(max-width: 600px) 90vw, 33vw" width="720" height="960" alt="{alt}" loading="lazy" decoding="async"><figcaption><span>0{i+1}</span><h3>{title}</h3></figcaption></figure>' for i,(name,title,alt) in enumerate(images))+'</div></div></section>'

def reviews(limit=None):
    selected = REVIEWS['reviews'][:limit] if limit else REVIEWS['reviews']
    cards = []
    for i, review in enumerate(selected):
        name = ESC(review['author'])
        source = ESC(review['url'])
        stars = '<span class="review-stars" role="img" aria-label="'+str(review['rating'])+' من 5 نجوم">' + icon('star') * review['rating'] + '</span>'
        excerpt = bool(review.get('excerpt'))
        attribution = 'مقتطف من مراجعة على Google' if excerpt else 'مراجعة على خرائط Google'
        source_label = 'مراجعات الملف على Google' if review.get('sourceScope') == 'profile' else 'اقرأ المراجعة الأصلية'
        source_accessible = f'مصدر مراجعة {review["author"]}: {source_label}'
        quote = ESC(review['text']) + (' …' if excerpt else '')
        cards.append(f'''<figure class="review-card" aria-label="التقييم {i + 1} من {len(selected)}"><div class="review-card-top">{stars}<span class="review-quote-mark" aria-hidden="true">“</span></div><blockquote cite="{source}"><p>{quote}</p></blockquote><figcaption><span class="review-avatar review-avatar--{i % 3}" aria-hidden="true">{ESC(review['initial'])}</span><span class="review-author"><strong dir="auto">{name}</strong><small>{attribution}</small></span></figcaption><a class="review-source" href="{source}" target="_blank" rel="noopener noreferrer" aria-label="{ESC(source_accessible)}">{source_label} {icon('arrow')}</a></figure>''')
    return f'''<section class="section reviews-section" id="reviews" aria-labelledby="reviews-title"><div class="wrap"><div class="section-heading"><div><span class="eyebrow">تجارب من ملفنا على Google</span><h2 id="reviews-title">شغلنا، بعيون عملائنا.</h2><p>من تركيب المغاسل إلى صيانة الإنارة؛ هذه كلمات كتبها أصحاب التجربة عن التعامل وجودة العمل.</p></div>{button(MAP,'كل المراجعات على Google','outline','map')}</div><div class="review-summary"><div class="review-score"><span class="review-score-number" dir="ltr">{ESC(REVIEW_SNAPSHOT['rating'])}<small> / 5</small></span><span class="review-stars" role="img" aria-label="5 من 5 نجوم">{icon('star') * 5}</span></div><div class="review-summary-copy"><strong>تقييم أمين سرور على خرائط Google</strong><span>بناءً على {REVIEW_SNAPSHOT['count']} مراجعة منشورة</span><small>آخر تحقق: <time datetime="{REVIEW_SNAPSHOT['asOf']}">{arabic_date(REVIEW_SNAPSHOT['asOf'])}</time></small></div><div class="review-summary-note">تجربة حقيقية.<br><strong>وكلمة نعتز فيها.</strong></div></div><div class="review-carousel" data-review-carousel role="region" aria-roledescription="عارض تقييمات" aria-label="تقييمات العملاء"><div class="reviews-grid review-track" id="reviews-track" tabindex="0" aria-label="بطاقات تقييمات العملاء">{''.join(cards)}</div><div class="review-controls" hidden><div class="review-navigation"><button type="button" class="review-nav review-prev" aria-controls="reviews-track" aria-label="التقييم السابق">{icon('arrow')}</button><span class="review-counter" dir="rtl"></span><button type="button" class="review-nav review-next" aria-controls="reviews-track" aria-label="التقييم التالي">{icon('arrow')}</button></div><div class="review-dots" aria-label="اختر مجموعة تقييمات"></div><button type="button" class="review-playback" aria-pressed="false">إيقاف الحركة</button></div><span class="review-announcement" aria-live="polite" aria-atomic="true"></span></div><div class="reviews-footnote"><p>نعرض {len(selected)} مراجعة نصية عامة بالنص المنشور أو بمقتطف واضح منه. يشمل الإجمالي أيضًا التقييمات دون تعليق. قد يتغير العدد والتقييم على Google.</p><div class="review-invitation"><p>سبق وتعاملت مع أمين سرور؟ شارك تجربتك الصادقة؛ رأيك يساعدنا على تحسين الخدمة.</p><div class="review-invite-actions">{button(B['reviewUrl'],'شارك تجربتك على Google','outline','star')}<a href="{ESC(MAP)}" target="_blank" rel="noopener noreferrer">شاهد الملف التجاري {icon('arrow')}</a></div></div></div></div></section>'''

def home():
    featured_cards = ''.join(service_card(SERVICES_BY_SLUG[slug], i + 1, '/') for i, slug in enumerate(FEATURED))
    return f'''<section class="hero"><div class="wrap hero-grid"><div class="hero-copy"><span class="hero-location">{icon('map')} الرياض · حي النرجس <i></i> 24 / 7</span><p class="hero-business">{B['name']}</p><h1>سباك وكهربائي بالرياض.<br><span>شغل يريح بالك.</span></h1><p class="hero-lead">من أول تمديد إلى آخر لمسة إنارة. تأسيس وصيانة السباكة والكهرباء للمنازل والشقق والفلل في الرياض، بتواصل مباشر مع أمين سرور.</p><div class="hero-actions">{button(wa(),'اطلب خدمتك عبر واتساب','primary','chat')}{button('tel:'+PHONE,'اتصال مباشر','outline','phone')}</div><div class="hero-review"><span class="stars" aria-label="5 من 5 نجوم">★★★★★</span><strong dir="ltr">{REVIEW_SNAPSHOT['rating']}</strong><span>من {REVIEW_SNAPSHOT['count']} مراجعة على Google</span><a href="#reviews" aria-label="شاهد آراء العملاء وتقييمات جوجل">{icon('arrow')}</a></div></div><div class="hero-visual"><img class="hero-photo" src="/assets/interior.webp" srcset="/assets/interior-sm.webp 480w, /assets/interior.webp 960w" sizes="(max-width: 760px) 92vw, 46vw" width="720" height="960" alt="تركيبات مغاسل وإنارة داخلية من صور أعمال أمين سرور" fetchpriority="high" decoding="async"><div class="photo-label">{icon('check')} من صور أعمالنا الفعلية</div><div class="hero-ticket"><span class="ticket-icon">{icon('water')}{icon('bolt')}</span><div><strong>تأسيس. صيانة. إنارة.</strong><small>خدمات متكاملة لبيتك في الرياض</small></div>{icon('arrow')}</div><span class="visual-index" aria-hidden="true">AMEEN / HOME SERVICES</span></div></div></section>
<section class="promise-strip" aria-label="لمحة عن الخدمة"><div class="wrap"><div>{icon('tool')}<span><strong>من التأسيس للصيانة</strong><small>سباكة وكهرباء وإنارة</small></span></div><div>{icon('phone')}<span><strong>تواصل مباشر</strong><small>اتصال أو واتساب</small></span></div><div>{icon('clock')}<span><strong>طوال أيام الأسبوع</strong><small>العمل على مدار الساعة</small></span></div></div></section>
<section class="section services-section" id="services"><div class="wrap">{section_heading('وش يحتاج بيتك؟','لكل تفصيلة، خدمة تناسبها.','خدمات واضحة بصور من ملف النشاط، من تأسيس الشبكات إلى صيانة الأعطال وتركيب الأدوات الصحية والإنارة.',button('/services','كل الخدمات','outline'))}<div class="service-grid">{featured_cards}</div></div></section>
<section class="section process-section"><div class="wrap process-layout"><div><span class="eyebrow">طلبك يبدأ بخطوة بسيطة</span><h2>خلّ التفاصيل واضحة،<br>من أول تواصل.</h2><p>نوع الخدمة، صورة للمشكلة، واسم الحي. تفاصيل تساعد على فهم طلبك وتنسيق الزيارة المناسبة.</p>{button('/contact#request','جهّز طلبك على واتساب','primary','chat')}</div><ol class="process-list"><li><span>01</span><div><h3>اشرح احتياجك</h3><p>سباكة، كهرباء أو إنارة؟ أرسل وصفًا مختصرًا لما تحتاجه.</p></div></li><li><span>02</span><div><h3>أرسل الصورة والموقع</h3><p>صورة واضحة واسم الحي يوضحان طبيعة العمل ومكانه.</p></div></li><li><span>03</span><div><h3>نسّق الزيارة والتنفيذ</h3><p>تأكد من الموعد ونطاق العمل والتكلفة المتفق عليها قبل البدء.</p></div></li></ol></div></section>{service_paths()}{work()}{reviews()}{article_teasers(['best-plumber', 'best-electrician', 'plumbing-installation'])}{location()}{faq()}{cta()}'''

def services_page():
    area_options = ''.join(f'<option value="{ESC(area)}">{ESC(area)}</option>' for area in AREAS)
    area_choice = '<div class="service-area"><label class="sr-only" for="service-area">حي الخدمة</label><select id="service-area"><option value="">اختر حي الخدمة</option>' + area_options + '</select></div>'
    filters=f'<div class="catalog-toolbar"><div class="catalog-heading"><div><span class="eyebrow">صور من الملف التجاري · تفاصيل واضحة</span><h2>اختر الخدمة اللي تحتاجها.</h2></div><p class="filter-status" role="status" aria-live="polite">عرض {len(SERVICES)} خدمة</p></div><div class="catalog-controls"><div class="service-search"><label class="sr-only" for="service-search">ابحث عن خدمة</label><input id="service-search" type="search" autocomplete="off" placeholder="ابحث: تسرب، مغاسل، ثريات…"></div>{area_choice}<div class="service-filters" role="group" aria-label="تصفية الخدمات"><button data-filter="all" aria-pressed="true">كل الخدمات <span>{len(SERVICES)}</span></button><button data-filter="plumbing" aria-pressed="false">السباكة <span>{SERVICE_COUNTS["plumbing"]}</span></button><button data-filter="electrical" aria-pressed="false">الكهرباء والإنارة <span>{SERVICE_COUNTS["electrical"]}</span></button></div></div></div>'
    empty='<div class="service-empty" hidden><h3>ما لقينا خدمة مطابقة للبحث.</h3><p>جرّب كلمة أقصر، أو اعرض كل خدمات السباكة والكهرباء.</p><button type="button" id="reset-services" class="button button-primary">اعرض كل الخدمات</button></div>'
    ordered = [SERVICES_BY_SLUG[slug] for slug in FEATURED] + [s for s in SERVICES if s[0] not in FEATURED]
    cards = ''.join(service_card(service, i + 1, '/services') for i, service in enumerate(ordered))
    return page_intro('خدمات السباكة والكهرباء في الرياض.','اختر حي الخدمة ونوع العمل، أو ابحث عن الخدمة التي تحتاجها. افتح تفاصيلها أو جهّز طلبك مباشرة عبر واتساب.','الخدمات')+'<section class="section service-catalog" id="service-catalog"><div class="wrap">'+service_group_links()+filters+'<div class="service-grid">'+cards+'</div>'+empty+'</div></section>'+reviews(6)+faq()+cta()

def about():
    return page_intro('أمين سرور. عناية بتفاصيل بيتك.','أعمال التأسيس والصيانة للسباكة والكهرباء في المنازل والشقق والفلل بمدينة الرياض.','عن أمين سرور')+f'''<section class="section"><div class="wrap about-layout"><div class="about-photo"><img src="/assets/basins.webp" width="720" height="960" alt="تجهيز وتركيب المغاسل من أعمال أمين سرور" loading="lazy"><span>{icon('water')} سباكة {icon('bolt')} كهرباء</span></div><div class="prose"><span class="eyebrow">عن النشاط</span><h2>خدمات بيتك،<br>بتواصل مباشر.</h2><p>{B['description']}</p><h3>توضيح الطلب يسهّل البداية</h3><p>سواء كان احتياجك إصلاح وصلة مياه أو تأسيس شبكة كهرباء أو تركيب ثريا، ابدأ بوصف الحالة وإرسال صور المكان. بهذه التفاصيل يمكن تنسيق الزيارة ومناقشة نطاق التنفيذ.</p><div class="about-facts"><span>{icon('map')} النرجس، الرياض</span><span>{icon('clock')} على مدار الساعة</span></div>{button('/services','استكشف الخدمات','primary')}{button(MAP,'ملفنا على Google','outline','map')}</div></div></section>'''+work()+reviews()+location()+cta()

def contact():
    options=''.join(f'<option value="{ESC(s[1])}">{s[1]}</option>' for s in SERVICES)
    hours=''.join(f'<div><span>{day}</span><strong>24 ساعة</strong></div>' for day in ['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'])
    return page_intro('قل لنا وش تحتاج، ونبدأ من هنا.','اتصال مباشر أو رسالة واتساب لتوضيح الخدمة وموقع الطلب في الرياض.','تواصل معنا')+f'''<section class="section"><div class="wrap contact-layout"><div><div class="contact-choice"><span class="service-icon">{icon('phone')}</span><span>للاتصال المباشر</span><a class="big-phone" href="tel:{PHONE}" dir="ltr">{B['displayPhone']}</a><p>استفسر عن الخدمة المطلوبة والتوفر وموعد الزيارة.</p>{button('tel:'+PHONE,'اتصل بأمين سرور','primary','phone')}</div><div class="hours-card"><h2>{icon('clock')} مواعيد العمل</h2><div class="hours-list">{hours}</div><p>لتأكيد الموعد والتوفر، تواصل قبل الزيارة.</p></div></div><section class="request-card" id="request" aria-labelledby="request-title"><span class="eyebrow">رسالة مرتبة تسهّل الطلب</span><h2 id="request-title">جهّز طلبك على واتساب.</h2><p>اختر الخدمة، وأضف اسم الحي ووصفًا مختصرًا. يفتح الزر الرسالة في واتساب لمراجعتها وإرسالها.</p><label for="request-service">الخدمة المطلوبة</label><select id="request-service"><option value="خدمات السباكة وصيانة الكهرباء">اختر الخدمة</option>{options}</select><label for="request-area">اسم الحي في الرياض <span>(اختياري)</span></label><input id="request-area" name="area" autocomplete="address-level3" maxlength="80" placeholder="مثال: النرجس"><label for="request-details">تفاصيل الطلب <span>(اختياري)</span></label><textarea id="request-details" rows="4" maxlength="800" placeholder="اشرح المشكلة أو العمل المطلوب باختصار"></textarea>{button(wa(),'افتح الرسالة في واتساب','primary','chat','id="request-link"')}<p class="small-note">يمكنك إرفاق الصور بعد فتح المحادثة.</p></section></div></section>'''+location()+faq()

def client_guide():
    return '''<section class="section"><div class="wrap article-layout"><aside class="article-toc"><h2>في هذا الدليل</h2><a href="#describe">01 · حدّد المشكلة</a><a href="#prepare">02 · جهّز تفاصيل طلبك</a><a href="#agree">03 · اتفق على نطاق العمل</a><a href="#plumbing-request">04 · طلب السباكة</a><a href="#electrical-request">05 · طلب الكهرباء</a><a href="#care">06 · راجع العمل بعد التنفيذ</a><a href="/services">استكشف الخدمات ←</a></aside><article class="prose article-body"><span class="eyebrow">دليل أمين سرور للعميل</span><h2 id="describe">ابدأ بوصف ما تلاحظه.</h2><p>هل يوجد تسرب ظاهر تحت المغسلة، أم رطوبة لا تعرف مصدرها؟ وهل توقفت نقطة إنارة واحدة، أم يتكرر فصل القاطع؟ وصف العلامة ومكانها ووقت ظهورها أوضح من الاكتفاء بعبارة «السباكة خربانة» أو «الكهرباء تفصل».</p><div class="article-callout">العطل الظاهر في حنفية أو وصلة يناسب طلب صيانة السباكة. أما التسرب غير معلوم المصدر، فابدأ بالاستفسار عن فحص وكشف التسربات.</div><h2 id="prepare">جهّز ثلاث معلومات قبل التواصل.</h2><ul><li><strong>نوع الخدمة:</strong> صيانة سباكة، تأسيس كهرباء، تركيب ثريا أو غير ذلك.</li><li><strong>صورة واضحة:</strong> للمكان أو القطعة المتأثرة، دون لمس أجزاء كهربائية أو تعريض نفسك للخطر.</li><li><strong>الموقع:</strong> اسم الحي ورابط الموقع عند تنسيق الزيارة.</li></ul><p>في أعمال التأسيس، وضّح مرحلة المبنى ونوعه وعدد النقاط المطلوبة مبدئيًا، وشارك المخطط المتاح عند الحاجة. هذه التفاصيل تساعد على تحديد ما يلزم للمعاينة.</p><h2 id="agree">ناقش نطاق العمل قبل التكلفة النهائية.</h2><p>تختلف تكلفة العمل باختلاف حالة التمديدات ومكان العطل والقطع اللازمة وإمكانية الوصول. اسأل عما يشمله السعر، ومن يوفر القطع، وهل يتطلب التنفيذ أعمالًا إضافية، وما الذي سيتم فحصه وتجربته بعد الإصلاح.</p><p>إذا تغير نطاق العمل أثناء الفحص، اطلب توضيح التغيير والتكلفة قبل تنفيذه. لا تعتمد على سعر عام لخدمة تختلف تفاصيلها من موقع إلى آخر.</p><h2 id="plumbing-request">تسرب، بطء تصريف أو ضعف مياه: وش تذكر للسباك؟</h2><p>لا تحتاج إلى تحديد سبب العطل بنفسك. صف ما تلاحظه: هل الماء يظهر عند استخدام الخلاط، أو أثناء التصريف، أو يستمر بعد إغلاقه؟ وهل المشكلة في مغسلة واحدة أو في أكثر من نقطة؟ اذكر متى بدأت وما إذا سبق تنفيذ عمل في الموضع نفسه.</p><p>إذا كانت القطعة ظاهرة ويمكن تصويرها من مكان آمن، أرسل صورة عامة للمكان وصورة أقرب للوصلة. لا يلزم فك القطع لتوضيح الطلب. وعند تركيب أدوات جديدة، وضح هل القطع والمحابس والوصلات متوفرة عندك، وشارك صورها ومقاساتها إن كانت معروفة.</p><p>راجع <a href="/services#water-leaks">خدمة فحص وإصلاح تسربات المياه</a> أو <a href="/services#drain-unblocking">تسليك الأحواض وفتحات الصرف الداخلية</a> بحسب العلامة الظاهرة. وتجد نطاق أعمال التأسيس والتركيب والصيانة في <a href="/plumber-riyadh">صفحة سباك بالرياض</a>.</p><h2 id="electrical-request">قاطع يفصل أو إنارة تحتاج تركيبًا: وش يحتاج الكهربائي؟</h2><p>في طلب صيانة الكهرباء، اذكر هل المشكلة في نقطة واحدة أو غرفة أو جزء من المنزل، وما الذي كان يعمل عند ملاحظتها. لا تفتح لوحة الكهرباء ولا تفك غطاء الفيش أو المفتاح من أجل التصوير؛ يكفي الوصف والصورة الخارجية إذا أمكن التقاطها بأمان.</p><p>أما تركيب الثريات والسبوت لايت، فيحتاج توضيح عدد الوحدات ونوع السقف، وهل نقاط الكهرباء موجودة أو تحتاج إلى تجهيز. صورة القطعة وصورة مكان التركيب من الأرض تساعدان على مناقشة متطلبات التثبيت والتوصيل قبل الزيارة.</p><p>اطلع على <a href="/services#breaker-replacement">فحص القواطع الكهربائية</a> و<a href="/services#chandeliers">تركيب الثريات</a>، أو راجع <a href="/electrician-riyadh">خدمات الكهربائي بالرياض</a> لتحديد نطاق طلبك. إذا احتجت سباكة وكهرباء في الزيارة نفسها، أرسل قائمة منفصلة لكل عمل.</p><h3>مثال على رسالة طلب واضحة</h3><div class="article-callout">أحتاج صيانة في منزلي بحي النرجس. يوجد تسرب ظاهر تحت مغسلة الحمام عند استخدام الماء، وأرفقت صورة المكان دون فك القطع. أرجو تأكيد موعد الزيارة وتوضيح ما يشمله الفحص والمواد قبل التنفيذ.</div><p>هذه صيغة توضيحية للطلب، وليست توثيقًا لعمل منفذ. غيّر الحي ووصف المشكلة حسب حالتك، ويمكنك استخدام <a href="/contact#request">نموذج تجهيز رسالة واتساب</a> لتنسيق التفاصيل.</p><h2 id="care">راجع النقطة التي تم العمل عليها.</h2><p>بعد أعمال السباكة، راقب تشغيل المياه والتصريف والوصلات التي جرى إصلاحها. وبعد تركيب الإنارة أو صيانة الكهرباء، اطلب من الفني تجربة النقاط المتأثرة وشرح الملاحظات المرتبطة بالاستخدام.</p><div class="article-callout safety"><strong>عند وجود خطر واضح</strong><p>ابتعد عن المياه القريبة من الكهرباء، ولا تلمس الأسلاك أو تفتح لوحة الكهرباء. استعن بفني لتقييم الحالة، ولا تحاول إعادة تشغيل دائرة يتكرر فصلها قبل معرفة السبب.</p></div></article></div></section>'''+cta()


def blog():
    intro = page_intro('مقالات السباكة والكهرباء. معرفة أوضح، وطلب أسهل.','أدلة عملية من أمين سرور لاختيار الخدمة وتجهيز الطلب ومناقشة القطع ونطاق العمل في الرياض وأحياء النرجس والياسمين والعارض والملقا.','المقالات ودليل العميل')
    guide_heading = '<div class="wrap guide-legacy-heading" id="request-guide"><span class="eyebrow">قبل تنسيق الزيارة</span><h2>جهّز طلبك خطوة بخطوة.</h2></div>'
    return intro + article_archive() + guide_heading + client_guide()


def service_paths():
    cards = [('/plumber-riyadh', 'pipe', 'سباك بالرياض', 'إصلاح التسربات والمواسير، تركيب الأدوات الصحية والسخانات، وتأسيس وصيانة السباكة.'), ('/electrician-riyadh', 'bolt', 'كهربائي بالرياض', 'فحص أعطال الكهرباء والقواطع والأفياش، وتأسيس التمديدات وتركيب الثريات والإنارة.'), ('/north-riyadh', 'map', 'خدمتنا في شمال الرياض', 'النرجس والياسمين والعارض والملقا. اختر الحي والخدمة، وأرسل تفاصيل طلبك لتنسيق الزيارة.')]
    return '<section class="section local-paths"><div class="wrap">' + section_heading('اختر المسار المناسب لطلبك', 'سباكة، كهرباء، أو خدمة في حيّك.', 'تفاصيل الأعمال المتاحة وما تحتاج توضيحه قبل تنسيق الزيارة.') + '<div class="local-path-grid">' + ''.join('<article class="local-path-card">' + icon(glyph) + '<h3><a href="' + url + '">' + label + '</a></h3><p>' + text + '</p><a class="local-text-link" href="' + url + '">استكشف التفاصيل ' + icon('arrow') + '</a></article>' for url, glyph, label, text in cards) + '</div></div></section>'

def detail_faq(items):
    return '<section class="section faq-section"><div class="wrap faq-layout"><div><span class="eyebrow">قبل تنسيق الزيارة</span><h2>إجابات تساعدك تطلب الخدمة.</h2></div><div class="accordion">' + ''.join('<details><summary>' + ESC(q) + icon('plus') + '</summary><p>' + ESC(a) + '</p></details>' for q, a in items) + '</div></div></section>'

def service_group_links(parent=None):
    groups = sorted(SERVICE_GROUPS.items(), key=lambda item: item[1]['parent'] == '/electrician-riyadh')
    if parent:
        groups = [(path, group) for path, group in groups if group['parent'] == parent and path != parent]
    links = ''.join(
        f'<a href="{path}">{icon(group["icon"])}<span>{ESC(group["label"])}</span>{icon("arrow")}</a>'
        for path, group in groups
    )
    return f'<nav class="service-group-links" aria-label="التصفح حسب نوع العمل">{links}</nav>'


def service_detail_page(path, group):
    label = ESC(group['label'])
    parent = group['parent']
    parent_label = 'خدمات السباكة' if parent == '/plumber-riyadh' else 'خدمات الكهرباء'
    services = [SERVICES_BY_SLUG[slug] for slug in group['services']]
    shortcuts = ''.join(f'<a href="#{slug}">{ESC(name)}</a>' for slug, name, *_ in services)
    cards = ''.join(service_card(service, i + 1, path) for i, service in enumerate(services))
    preparation = ''.join(f'<li>{icon("check")}<span>{ESC(item)}</span></li>' for item in group['prepare'])

    return f'''
<section class="page-intro service-topic-intro">
  <div class="wrap">
    <nav class="breadcrumbs" aria-label="مسار التنقل">
      <a href="/">الرئيسية</a><span aria-hidden="true">/</span>
      <a href="/services">كل الخدمات</a><span aria-hidden="true">/</span>
      <span aria-current="page">{label}</span>
    </nav>
    <div class="service-topic-hero">
      <div>
        <h1>{ESC(group['title'])}</h1>
        <p>{ESC(group['intro'])}</p>
        <div class="service-topic-actions">
          {button('#service-options', 'اختر الخدمة', 'primary', group['icon'])}
          {button('tel:' + PHONE, 'اتصل بأمين سرور', 'outline', 'phone')}
        </div>
      </div>
      <div class="service-topic-photo">{article_image(group['photo'], True)}</div>
    </div>
  </div>
</section>
<section class="section service-topic-options" aria-labelledby="service-options">
  <div class="wrap">
    <h2 id="service-options">اختر العمل المطلوب</h2>
    <nav class="service-topic-shortcuts" aria-label="الخدمات في هذه الصفحة">{shortcuts}</nav>
    <div class="service-grid">{cards}</div>
  </div>
</section>
<section class="section service-topic-prep" aria-labelledby="visit-preparation">
  <div class="wrap">
    <div class="service-topic-note">
      <h2 id="visit-preparation">وش ترسل قبل الزيارة؟</h2>
      <ul>{preparation}</ul>
      <nav class="service-topic-actions" aria-label="خدمات ومناطق مرتبطة">
        {button(parent, parent_label, 'outline', group['icon'])}
        {button('/north-riyadh', 'مناطق الخدمة', 'outline', 'map')}
      </nav>
    </div>
  </div>
</section>
{detail_faq(group['faq'])}'''


def service_guidance(category):
    plumbing = category == 'plumbing'
    items = [
        ('الماء ظاهر تحت المغسلة', 'وضح هل يظهر مع فتح الخلاط، أو أثناء التصريف، أو يستمر والماء مغلق. وصف وقت التسرب ومكانه يساعد على تحديد ما يحتاج إلى فحص.', 'water-leaks', 'فحص وإصلاح تسربات المياه'),
        ('الحوض يصرف ببطء', 'اذكر هل البطء في حوض واحد أو في أكثر من نقطة، وهل بدأ فجأة أو تكرر. يختلف نطاق فحص الصرف عن استبدال خلاط أو وصلة مياه.', 'drain-unblocking', 'تسليك الأحواض وفتحات الصرف'),
        ('تدفق المياه ضعيف', 'حدد هل الضعف في نقطة واحدة أو في عدة نقاط، ومتى يظهر. تُراجع الحالة قبل تحديد الحاجة إلى إصلاح خلاط أو وصلة أو فحص المضخة.', 'water-pressure', 'فحص ضعف ضغط المياه'),
        ('تجهّز حمامًا أو مطبخًا', 'أرسل المخطط المتاح، ومرحلة التشطيب، وعدد نقاط المياه والصرف المطلوبة. تُراجع المسارات والمواد والأعمال المشمولة قبل التنفيذ.', 'plumbing-installation', 'تأسيس وتمديد شبكات السباكة'),
    ] if plumbing else [
        ('القاطع يفصل أكثر من مرة', 'اذكر الدائرة المتأثرة وما كان يعمل عند الفصل، دون فتح اللوحة أو تجربة التوصيلات. الفحص يحدد السبب؛ تكرار الفصل وحده لا يحدد القطعة المطلوب استبدالها.', 'breaker-replacement', 'فحص القواطع الكهربائية'),
        ('فيش أو مفتاح لا يعمل', 'وضح هل المشكلة في نقطة واحدة أو عدة نقاط، وهل ظهرت أثناء استخدام معين. أرسل وصفًا أو صورة خارجية من مكان آمن دون فك الغطاء.', 'switch-repair', 'إصلاح الأفياش والمفاتيح'),
        ('تحتاج تركيب ثريا', 'أرسل صورة الثريا والعدد ونوع السقف وصورة موضع التركيب المتاح من الأرض. تراجع طريقة التثبيت ونقطة الكهرباء قبل تنسيق العمل.', 'chandeliers', 'تركيب الثريات'),
        ('تجدّد إنارة المكان', 'حدد عدد الوحدات ونوعها وهل المطلوب استبدال إنارة قائمة أو إضافة نقاط جديدة. توضح هذه التفاصيل نطاق التمديدات والقطع وأعمال التركيب.', 'spotlights', 'تركيب السبوت لايت وإنارة LED'),
    ]
    cards = ''.join('<article class="service-guide-card"><h3>' + ESC(title) + '</h3><p>' + ESC(text) + '</p><a class="local-text-link" href="' + SERVICE_DESTINATIONS[slug] + '">' + ESC(label) + ' ' + icon('arrow') + '</a></article>' for title, text, slug, label in items)
    anchor = 'plumbing-request' if plumbing else 'electrical-request'
    guide_label = 'كيف تجهّز طلب السباكة؟' if plumbing else 'ما المعلومات التي يحتاجها الكهربائي؟'
    return '<section class="section service-guidance" aria-labelledby="service-guidance-title"><div class="wrap">' + section_heading('ابدأ بالعلامة التي تلاحظها', 'أي خدمة تناسب طلبك؟', 'اختر الحالة الأقرب، ثم راجع تفاصيل الخدمة. يُحدد نطاق الإصلاح بعد فحص الموقع.') + '<div class="service-guide-grid">' + cards + '</div><div class="service-guide-next"><h2 id="service-guidance-title">' + guide_label + '</h2><p>في دليل العميل أمثلة توضح وصف المشكلة والتفاصيل المطلوبة ومناقشة المواد ونطاق العمل قبل الزيارة.</p><a class="local-text-link" href="/blog#' + anchor + '">اقرأ دليل ' + ('طلب السباك' if plumbing else 'طلب الكهربائي') + ' ' + icon('arrow') + '</a></div></div></section>'

def category_page(category):
    plumbing = category == 'plumbing'
    path = '/plumber-riyadh' if plumbing else '/electrician-riyadh'
    title = 'سباك بالرياض للتأسيس والصيانة والتركيب.' if plumbing else 'كهربائي بالرياض لصيانة الأعطال وتركيب الإنارة.'
    intro = 'أمين سرور لخدمات السباكة وصيانة الكهرباء. خدمات سباكة للمنازل والشقق والفلل في النرجس والياسمين والعارض والملقا، ضمن نطاق الخدمة في الرياض. اشرح المشكلة أو أرسل صور القطع والمكان لتحديد نطاق الطلب وتنسيق الزيارة.' if plumbing else 'تواصل مباشرة مع أمين سرور لطلبات صيانة الكهرباء والتأسيس وتركيب الأفياش والقواطع والثريات والإنارة. نخدم النرجس والياسمين والعارض والملقا ضمن الرياض، ويُؤكد الموعد بعد معرفة العطل والموقع.'
    selected = [s for s in SERVICES if s[2] == category]
    needs = [('تسرب أو خلل في التصريف', 'اذكر موضع الماء أو بطء التصريف: تحت المغسلة، عند الخلاط، بجوار المرحاض أو قرب السخان. صورة الوصلات الظاهرة تساعد على فهم الطلب قبل الزيارة.'), ('تركيب قطعة أو استبدالها', 'أرسل صورة القطعة الحالية والجديدة، ووضح هل المواد متوفرة عندك. يشمل ذلك المغاسل والخلاطات وأطقم الدش والسخانات والمحابس.'), ('تأسيس أو تجديد التمديدات', 'حدد نوع الموقع ومرحلة التشطيب وعدد نقاط المياه والصرف المطلوبة. تُراجع المسارات وحالة الشبكة لتحديد الأعمال والمواد والتكلفة قبل التنفيذ.')] if plumbing else [('عطل في نقطة أو دائرة', 'وضح هل المشكلة في إنارة واحدة أو فيش أو جزء من المنزل، وهل يتكرر فصل القاطع عند تشغيل جهاز. وصف الحالة يساعد على تحديد ما يحتاج إلى فحص.'), ('تركيب إنارة أو تجهيزات', 'أرسل صورة الثريا أو وحدة الإنارة وصورة مكان التثبيت، مع العدد ونوع السقف. توضح هذه التفاصيل احتياجات التوصيل والتثبيت قبل تنسيق الموعد.'), ('تأسيس أو إضافة نقاط', 'حدد عدد الأفياش والمفاتيح ونقاط الإنارة ومرحلة التشطيب. تُراجع التمديدات والدوائر ومتطلبات الموقع قبل الاتفاق على نطاق التنفيذ.')]
    faq_items = [('هل يتوفر سباك في النرجس والياسمين والعارض والملقا؟', 'نعم، هذه الأحياء ضمن نطاق الخدمة المستهدف في شمال الرياض. أرسل اسم الحي ورابط الموقع ووصف الطلب لتأكيد التوفر والموعد المناسب.'), ('كيف تُحدد تكلفة السباكة؟', 'تختلف بحسب سبب المشكلة وحالة المواسير وإمكانية الوصول والقطع المطلوبة. وضح هل طلبك إصلاح أو تركيب أو تأسيس، وتأكد من الأعمال والمواد والتكلفة المتفق عليها قبل البدء.'), ('هل تشمل الخدمة كشف التسرب بدون تكسير أو التسليك بالضغط؟', 'المتاح هنا فحص وإصلاح التسربات وتسليك الأحواض وفتحات الصرف الداخلية حسب حالة الموقع. لا نفترض استخدام أجهزة كشف إلكترونية أو معدات ضغط أو شفط؛ تُوضح الطريقة المناسبة ونطاق العمل عند التواصل.'), ('هل يمكن طلب سباك بشكل عاجل؟', 'يستقبل النشاط طلبات السباكة على مدار الساعة وفق مواعيده الحالية. التوفر وموعد الزيارة يتأكدان عند التواصل بحسب الموقع وطبيعة الطلب.'), ('هل يمكن طلب تركيب قطع متوفرة عندي؟', 'أرسل صور القطع والمقاسات ومكان التركيب، ووضح هل التمديدات الحالية جاهزة. تساعد هذه المعلومات على تحديد متطلبات التركيب والمواد الإضافية ونطاق العمل قبل الزيارة.')] if plumbing else [('هل يتوفر كهربائي في أحياء شمال الرياض؟', 'تشمل التغطية النرجس والياسمين والعارض والملقا ضمن نطاق الرياض. أرسل اسم الحي وموقعك ونوع العطل أو عدد القطع المطلوب تركيبها لتنسيق الزيارة.'), ('هل تستبدلون القاطع بمجرد تكرار فصله؟', 'تكرار الفصل يحتاج إلى فحص السبب والدائرة والأحمال، ولا يحدد وحده أن القاطع تالف. يُحدد الإصلاح أو الاستبدال المناسب بعد الفحص.'), ('ما التفاصيل المطلوبة لتركيب ثريا أو سبوت لايت؟', 'أرسل صور القطع ومكان التركيب والعدد ونوع السقف، ووضح هل التمديدات ونقاط التعليق موجودة. يُراجع نطاق العمل ومتطلبات التثبيت والتوصيل قبل التنفيذ.'), ('هل يوجد سعر ثابت لصيانة الكهرباء؟', 'التكلفة مرتبطة بالعطل وحالة التمديدات وعدد النقاط والقطع والمواد المطلوبة. يُوضح نطاق الخدمة والتكلفة المتفق عليها قبل بدء العمل.'), ('هل الخدمة على مدار الساعة؟', 'مواعيد النشاط الحالية على مدار الساعة طوال الأسبوع. تواصل لتأكيد التوفر والموعد المناسب؛ لا تعني هذه المواعيد وعدًا بزمن وصول محدد.')]
    needs_html = ''.join('<article class="local-path-card"><h3>' + h + '</h3><p>' + p + '</p></article>' for h, p in needs)
    cards = service_group_links(path) + '<div class="service-grid">' + ''.join(
        service_card(service, i + 1, path) for i, service in enumerate(selected)
    ) + '</div>'
    request = wa('مرحبًا أمين سرور، أرغب في طلب ' + ('سباك' if plumbing else 'كهربائي') + ' في حي: . وصف الطلب: ')
    return page_intro(title, intro, 'خدمات السباكة' if plumbing else 'خدمات الكهرباء') + '<section class="section"><div class="wrap local-request"><div><span class="eyebrow">من أول تواصل، خلّ الطلب واضح</span><h2>حدد الخدمة والموقع قبل الزيارة.</h2><p>خدمة إصلاح قائمة تختلف عن تركيب جديد أو تأسيس. اذكر نوع الموقع، وصور الحالة عند الإمكان، والقطع المتوفرة لديك؛ ثم ناقش الموعد والمواد والتكلفة المتفق عليها.</p></div><div class="local-request-actions">' + button(request, 'أرسل تفاصيل طلبك على واتساب', 'primary', 'chat') + button('tel:' + PHONE, 'اتصل بأمين سرور', 'outline', 'phone') + '</div></div></section><section class="section"><div class="wrap"><h2>كيف توضح طلبك؟</h2><div class="local-path-grid">' + needs_html + '</div></div></section><section class="section services-section"><div class="wrap">' + section_heading('أعمال ضمن نطاق النشاط', 'خدمات السباكة المتاحة.' if plumbing else 'خدمات الكهرباء والإنارة.', 'صور أصلية من ملف النشاط، وتفاصيل تساعدك تختار الخدمة المناسبة. لا تعني الصورة أنها توثق الطلب نفسه أو حيًا بعينه.') + cards + '</div></section><section class="section"><div class="wrap local-coverage"><h2>نخدم أحياء شمال الرياض.</h2><p>النرجس والياسمين والعارض والملقا ضمن نطاق خدمة الرياض. تأكد من إمكانية الزيارة وموعدها عند التواصل.</p>' + button('/north-riyadh' if plumbing else '/north-riyadh#service-areas', 'تفاصيل مناطق الخدمة' if plumbing else 'جهّز طلب الكهرباء حسب الحي', 'outline', 'map') + button('/services', 'كل خدمات السباكة والكهرباء', 'outline') + '</div></section>' + service_guidance(category) + article_teasers(['best-plumber-al-narjis', 'best-plumber-al-arid', 'plumbing-repair'] if plumbing else ['best-electrician-al-narjis', 'best-electrician-al-yasmin', 'best-electrician-al-arid']) + detail_faq(faq_items) + cta()

def north_riyadh_page():
    district_guides = {
        'النرجس': (
            'فحص الأعطال والقواطع',
            'اذكر أي غرفة أو دائرة تتأثر ومتى يتكرر الفصل، وهل العطل في نقطة واحدة أو أكثر.',
            'best-electrician-al-narjis',
            'best-plumber-al-narjis',
        ),
        'الياسمين': (
            'تركيب الثريات والسبوت لايت',
            'أرسل عدد وحدات الإنارة ونوع السقف، ووضح إن كانت نقاط الإنارة جاهزة.',
            'best-electrician-al-yasmin',
            'best-plumber-al-yasmin',
        ),
        'العارض': (
            'تأسيس الكهرباء وإضافة الأفياش',
            'حدد مرحلة التشطيب والغرف التي تحتاج نقاطًا جديدة، وأرسل المخطط إن توفر.',
            'best-electrician-al-arid',
            'best-plumber-al-arid',
        ),
        'الملقا': (
            'تجديد إنارة الغرف والمجالس',
            'حدد الوحدات التي ترغب في استبدالها والغرف التي تحتاج فيها نقاطًا إضافية.',
            'best-electrician-al-malqa',
            'best-plumber-al-malqa',
        ),
    }
    area_cards = []
    for i, area in enumerate(AREAS, start=1):
        catalog_link = '/services?' + urlencode({'area': area}) + '#service-catalog'
        details = ''
        general_request = wa(f'مرحبًا أمين سرور، أحتاج خدمة في حي {area}. نوع الخدمة: . وصف الطلب: ')
        actions = button(general_request, f'اطلب خدمة في {area}', 'primary', 'chat')
        if area in district_guides:
            service, instructions, electrical_guide, plumbing_guide = district_guides[area]
            electrical_message = f'السلام عليكم، أحتاج كهربائي في حي {area}. ممكن أنسّق زيارة؟\nتفاصيل الطلب '
            plumbing_message = f'السلام عليكم، أحتاج خدمة سباكة في حي {area}. وصف الطلب: '
            details = (
                f'<h3>{ESC(service)}</h3><p>{ESC(instructions)}</p>'
                f'<nav class="local-area-actions local-request-actions" aria-label="أدلة الخدمة في {ESC(area)}">'
                f'<a class="local-text-link" href="{article_route(BY_SLUG[electrical_guide])}">'
                f'دليل الكهرباء في {ESC(area)} {icon("arrow")}</a>'
                f'<a class="local-text-link" href="{article_route(BY_SLUG[plumbing_guide])}">'
                f'دليل السباكة في {ESC(area)} {icon("arrow")}</a></nav>'
            )
            actions = (
                button(wa(electrical_message), f'اطلب كهربائي في {area}', 'primary', 'chat')
                + button(wa(plumbing_message), f'اطلب سباك في {area}', 'outline', 'chat')
            )
        area_cards.append(
            f'<article class="local-path-card" id="area-{i}">'
            '<span class="eyebrow">ضمن نطاق الخدمة</span>'
            f'<h2>حي {ESC(area)}</h2>'
            f'<p>أرسل موقع الخدمة في {ESC(area)} ووصف المشكلة أو قائمة التركيبات. '
            'يُحدد نطاق العمل والموعد بعد مراجعة التفاصيل.</p>'
            f'{details}<div class="local-area-actions">{actions}</div>'
            f'<p><a class="local-text-link" href="{ESC(catalog_link)}">'
            f'كل الخدمات في {ESC(area)} {icon("arrow")}</a></p></article>'
        )
    questions = [('هل يوجد فرع مستقل في كل حي؟', 'هذه الصفحة توضح مناطق خدمة، وليست إعلانًا عن فروع أو مقرات مستقلة. بيانات النشاط الحالية مرتبطة بالنرجس في الرياض، وتُنسّق الزيارات إلى مواقع العملاء.'), ('هل أحتاج كتابة سباك أو كهربائي فقط عند الطلب؟', 'الأفضل توضيح الخدمة الفعلية: تسرب تحت المغسلة، سخان يحتاج تركيبًا، فيش لا يعمل، قاطع يتكرر فصله أو ثريا تحتاج تثبيتًا، مع صورة واسم الحي.'), ('هل الوصول مضمون خلال عدد محدد من الدقائق؟', 'لا تعرض الصفحة زمن وصول ثابتًا. الموعد يتحدد عند التواصل بحسب المكان والخدمة والتوفر.'), ('كيف أطلب أكثر من عمل في زيارة واحدة؟', 'اكتب قائمة منفصلة بالأعمال المطلوبة وعدد القطع، وأرسل صور كل موضع إن أمكن. تُراجع القائمة والمواد المطلوبة ونطاق الزيارة قبل التنسيق.')]
    return page_intro('سباك وكهربائي في شمال الرياض.', 'خدمات أمين سرور للتأسيس والصيانة والتركيب في النرجس والياسمين والعارض والملقا. هنا توضح نطاق الخدمة وتجهّز طلبك؛ لا تحتاج إلى اختيار فرع أو الاعتماد على زمن وصول غير مؤكد.', 'مناطق الخدمة') + '<section class="section" id="service-areas"><div class="wrap"><div class="local-area-grid">' + ''.join(area_cards) + '</div></div></section><section class="section"><div class="wrap">' + section_heading('اختيار الخدمة يوضح الطلب', 'وش يحتاج موقعك؟', 'تعرف على نطاق أعمال السباكة والكهرباء والتفاصيل المطلوبة قبل الزيارة.') + '<div class="local-path-grid local-path-grid--two"><article class="local-path-card"><h2>سباكة المنازل والفلل</h2><p>إصلاح المواسير والوصلات والتسربات، صيانة وتركيب الأدوات الصحية والسخانات، وتأسيس وتمديدات المياه والصرف.</p>' + button('/plumber-riyadh', 'تفاصيل خدمات السباكة', 'outline', 'pipe') + '</article><article class="local-path-card"><h2>الكهرباء والإنارة</h2><p>فحص الأعطال والقواطع والأفياش، تمديد وتجديد الأسلاك، وتركيب الثريات والسبوت لايت ووحدات الإنارة.</p>' + button('/electrician-riyadh', 'تفاصيل خدمات الكهرباء', 'outline', 'bolt') + '</article></div></div></section>' + detail_faq(questions) + cta()


def graph(path, title, desc):
    url=BASE.rstrip('/')+path if path!='/' else BASE
    detail = DETAIL_PAGES.get(path)
    address={'@type':'PostalAddress','streetAddress':B['streetAddress'],'addressLocality':B['addressLocality'],'addressRegion':B['addressRegion'],'postalCode':B['postalCode'],'addressCountry':'SA'}
    business={'@type':['Plumber','Electrician'],'@id':BASE+'#business','name':B['name'],'alternateName':'أمين سرور للسباكة والكهرباء','url':BASE,'telephone':PHONE,'description':B['description'],'logo':{'@id':BASE+'#logo'},'image':[BASE+'assets/interior.webp',BASE+'assets/basins.webp',BASE+'assets/showroom.webp'],'address':address,'areaServed':AREA_ENTITIES,'hasMap':MAP,'sameAs':[MAP,B['instagram']],'openingHours':B['openingHours'],'openingHoursSpecification':[{'@type':'OpeningHoursSpecification','dayOfWeek':['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],'opens':'00:00','closes':'23:59'}],'contactPoint':[{'@type':'ContactPoint','telephone':PHONE,'contactType':'customer service','availableLanguage':['Arabic'],'areaServed':AREA_ENTITIES,'url':B['whatsapp']}],'hasOfferCatalog':{'@id':BASE+'services#catalog'}}
    nodes=[business,{'@type':'ImageObject','@id':BASE+'#logo','url':BASE+'assets/brand-mark.svg','contentUrl':BASE+'assets/brand-mark.svg','caption':B['name']},{'@type':'WebSite','@id':BASE+'#website','url':BASE,'name':B['name'],'inLanguage':'ar-SA','publisher':{'@id':BASE+'#business'}},{'@type':'ContactPage' if path=='/contact' else ('AboutPage' if path=='/about' else 'WebPage'),'@id':url+'#webpage','url':url,'name':title,'description':desc,'isPartOf':{'@id':BASE+'#website'},'about':{'@id':BASE+'#business'},'inLanguage':'ar-SA','primaryImageOfPage':{'@id':BASE+'#primaryimage'}},{'@type':'ImageObject','@id':BASE+'#primaryimage','url':BASE+'assets/interior.webp','contentUrl':BASE+'assets/interior.webp','width':720,'height':960,'caption':'تركيبات مغاسل وإنارة داخلية من صور أعمال أمين سرور'}]
    nodes[2].update(COMPONENTS['websiteCreator'])
    if path != '/404':
        nodes[3]['dateModified'] = B.get('pageUpdatedOn', {}).get(path, B['contentUpdatedOn'])
    if path in SERVICE_GROUPS:
        service_type = SERVICE_GROUPS[path]['label'] if detail else ('خدمات السباكة' if path == '/plumber-riyadh' else 'صيانة الكهرباء والإنارة')
        nodes[3]['mainEntity'] = {'@id': url + '#service'}
        nodes.append({'@type': 'Service', '@id': url + '#service', 'name': title.split('|')[0].strip(), 'serviceType': service_type, 'url': url, 'description': desc, 'provider': {'@id': BASE + '#business'}, 'areaServed': AREA_ENTITIES, 'hasOfferCatalog': {'@id': url + '#catalog'}})
    if path!='/':
        label={'/services':'الخدمات','/about':'عن أمين سرور','/blog':'دليل العميل','/contact':'تواصل معنا','/plumber-riyadh':'السباكة بالرياض','/electrician-riyadh':'الكهرباء بالرياض','/north-riyadh':'مناطق الخدمة'}.get(path,title)
        crumbs = [('الرئيسية', BASE)]
        if detail:
            crumbs.append(('كل الخدمات', BASE + 'services'))
            label = detail['label']
        crumbs.append((label, url))
        nodes.append({'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[
            {'@type':'ListItem','position':i,'name':name,'item':item}
            for i, (name, item) in enumerate(crumbs, 1)
        ]})
        nodes[3]['breadcrumb']={'@id':url+'#breadcrumb'}
    selected=SERVICES if path=='/services' else ([s for s in SERVICES if s[0] in FEATURED] if path=='/' else [])
    if path in CATEGORY_PAGES:
        selected = [s for s in SERVICES if s[2] == ('plumbing' if path == '/plumber-riyadh' else 'electrical')]
    if detail:
        selected = [SERVICES_BY_SLUG[slug] for slug in detail['services']]
        photo = PHOTOS[detail['photo']]
        image_id = url + '#primaryimage'
        nodes[4].update({'@id':image_id,'url':BASE+photo['src'],'contentUrl':BASE+photo['src'],'width':800,'height':500,'caption':photo['alt']})
        nodes[3]['primaryImageOfPage'] = {'@id':image_id}
    catalog_url = url if path in SERVICE_GROUPS else BASE + 'services'
    catalog_name = SERVICE_GROUPS[path]['label'] if path in SERVICE_GROUPS else 'خدمات أمين سرور للسباكة والكهرباء'
    if selected:
        nodes.append({'@type':'OfferCatalog','@id':catalog_url + '#catalog','name':catalog_name,'url':catalog_url,'itemListElement':[{'@type':'Offer','itemOffered':{'@id':BASE+'services#'+s[0]}} for s in selected]})
        for slug,name,cat,desc,_ in selected:
            photo=PHOTOS[MEDIA['services'][slug]['photo']]
            nodes.append({'@type':'Service','@id':BASE+'services#'+slug,'name':name,'image':{'@type':'ImageObject','url':BASE+photo['src'],'contentUrl':BASE+photo['src'],'width':800,'height':500,'caption':photo['alt']},'serviceType':'السباكة' if cat=='plumbing' else 'الكهرباء والإنارة','description':desc,'url':BASE.rstrip('/')+SERVICE_DESTINATIONS[slug],'provider':{'@id':BASE+'#business'},'areaServed':AREA_ENTITIES,'availableChannel':{'@type':'ServiceChannel','serviceUrl':service_request(name),'servicePhone':{'@type':'ContactPoint','telephone':PHONE,'availableLanguage':'Arabic'}}})
    post = POST_BY_ROUTE.get(path)
    if path == '/blog':
        nodes[3]['@type'] = 'CollectionPage'
        nodes[3]['mainEntity'] = {'@id': url + '#articles'}
        nodes.append({'@type': 'ItemList', '@id': url + '#articles', 'name': 'مقالات أمين سرور للسباكة والكهرباء', 'numberOfItems': len(POSTS), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': item['title'], 'url': BASE.rstrip('/') + article_route(item)} for i, item in enumerate(POSTS)]})
    if post:
        photo = PHOTOS[post['photo']]
        image_id = url + '#primaryimage'
        nodes[4].update({'@id': image_id, 'url': BASE + photo['src'], 'contentUrl': BASE + photo['src'], 'width': 800, 'height': 500, 'caption': photo['alt']})
        nodes[3].update({'datePublished': PUBLISHED, 'dateModified': post.get('modified', PUBLISHED), 'primaryImageOfPage': {'@id': image_id}, 'mainEntity': {'@id': url + '#article'}})
        breadcrumb = next(node for node in nodes if node.get('@type') == 'BreadcrumbList')
        breadcrumb['itemListElement'] = [{'@type': 'ListItem', 'position': 1, 'name': 'الرئيسية', 'item': BASE}, {'@type': 'ListItem', 'position': 2, 'name': 'المقالات ودليل العميل', 'item': BASE + 'blog'}, {'@type': 'ListItem', 'position': 3, 'name': post['title'], 'item': url}]
        nodes.append({'@type': 'BlogPosting', '@id': url + '#article', 'url': url, 'headline': post['title'], 'description': desc, 'datePublished': PUBLISHED, 'dateModified': post.get('modified', PUBLISHED), 'inLanguage': 'ar-SA', 'articleSection': 'السباكة' if post['category'] == 'plumbing' else 'الكهرباء والإنارة', 'image': [BASE + photo['src']], 'author': {'@type': 'Organization', '@id': BASE + '#business', 'name': B['name'], 'url': BASE}, 'publisher': {'@id': BASE + '#business'}, 'mainEntityOfPage': {'@id': url + '#webpage'}, 'isPartOf': {'@id': BASE + '#website'}, 'about': {'@id': BASE + '#business'}})
    return {'@context':'https://schema.org','@graph':nodes}

def render(path,title,description,body,noindex=False):
    canonical=BASE if path=='/' else BASE.rstrip('/')+path
    post = POST_BY_ROUTE.get(path)
    image_source = post or DETAIL_PAGES.get(path)
    share_photo = PHOTOS[image_source['photo']] if image_source else None
    share_url = BASE + share_photo['src'] if share_photo else BASE + 'assets/share-ameen.jpg?v=20261017-water-electric'
    share_alt = share_photo['alt'] if share_photo else 'أمين سرور للسباكة وصيانة الكهرباء في الرياض'
    share_width, share_height = (800, 500) if share_photo else (1200, 630)
    og_type = 'article' if post else 'website'
    article_meta = f'<meta property="article:published_time" content="{PUBLISHED}"><meta property="article:modified_time" content="{post.get("modified", PUBLISHED)}"><meta property="article:section" content="{"السباكة" if post["category"] == "plumbing" else "الكهرباء والإنارة"}">' if post else ''
    article_css = '<link rel="stylesheet" href="/articles.css?v=20261116-guides">' if post or path in ('/', '/blog', '/plumber-riyadh', '/electrician-riyadh') else ''
    cards_css='<link rel="stylesheet" href="/service-cards.css?v=20261123-service-areas">' if path in ('/', '/services') or path in SERVICE_GROUPS else ''
    reviews_css='<link rel="stylesheet" href="/reviews.css?v=20261116-carousel"><script src="/reviews.js?v=20261116-carousel" defer></script>' if path in ('/', '/services', '/about') else ''
    schema=json.dumps(graph(path,title,description),ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    return f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#075a77"><meta name="color-scheme" content="light"><title>{ESC(title)}</title><meta name="description" content="{ESC(description)}"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-image-preview:large'}"><link rel="canonical" href="{canonical}"><link rel="icon" href="/assets/brand-mark.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><link rel="preload" href="/assets/fonts/noto-arabic-regular.woff" as="font" type="font/woff" crossorigin><link rel="stylesheet" href="/style.css?v=20261116-service-guides">{cards_css}{reviews_css}{article_css}<meta property="og:type" content="{og_type}">{article_meta}<meta property="og:locale" content="ar_SA"><meta property="og:site_name" content="{B['name']}"><meta property="og:title" content="{ESC(title)}"><meta property="og:description" content="{ESC(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{ESC(share_url)}"><meta property="og:image:width" content="{share_width}"><meta property="og:image:height" content="{share_height}"><meta property="og:image:alt" content="{ESC(share_alt)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{ESC(title)}"><meta name="twitter:description" content="{ESC(description)}"><meta name="twitter:image" content="{ESC(share_url)}"><script type="application/ld+json">{schema}</script><script src="/script.js?v=20261125-area-url" defer></script>{COMPONENTS['developerCreditStyle']}</head><body><a class="skip-link" href="#main-content">انتقل إلى المحتوى</a>{SPRITE}{header(path)}<main id="main-content">{body}</main>{footer()}</body></html>'''

PAGES=[
 ('/','index.html','سباك وكهربائي بالرياض | أمين سرور — النرجس، 24 ساعة','أمين سرور لخدمات السباكة وصيانة الكهرباء في الرياض، حي النرجس. تأسيس وصيانة وتركيب أدوات صحية وثريات وإنارة. اتصال وواتساب: 0545350293. العمل 24 ساعة.',home()),
 ('/services','services.html','خدمات السباكة والكهرباء بالرياض | أمين سرور','خدمات تأسيس وصيانة السباكة والكهرباء وإصلاح المواسير والتسربات وتركيب السخانات والمغاسل والثريات والإنارة بالرياض. اختر خدمتك وتواصل مباشرة مع أمين سرور.',services_page()),
 ('/about','about.html','عن أمين سرور لخدمات السباكة وصيانة الكهرباء | الرياض','تعرف على أمين سرور لخدمات السباكة وصيانة الكهرباء للمنازل والفلل في الرياض. عنوان النشاط في حي النرجس، والتواصل على 0545350293 طوال أيام الأسبوع.',about()),
 ('/blog','blog.html','مقالات السباكة والكهرباء بالرياض | أمين سرور','مقالات وأدلة عملية لاختيار سباك وكهربائي وتأسيس وتصليح السباكة في النرجس والياسمين والعارض والملقا. صور من النشاط وخطوات واضحة لتجهيز طلبك.',blog()),
 ('/contact','contact.html','تواصل مع أمين سرور | سباك وكهربائي النرجس بالرياض','اتصل أو واتساب أمين سرور على 0545350293. العنوان: 6488 أنس ابن مالك، الرقم الإضافي 3571، النرجس، الرياض 13327. العمل على مدار الساعة طوال الأسبوع.',contact()),
]
PAGES += [
 ('/plumber-riyadh', 'plumber-riyadh.html', 'سباك بالرياض | صيانة وتأسيس السباكة — أمين سرور', 'سباك للمنازل والفلل في النرجس والياسمين والعارض والملقا بالرياض. إصلاح مواسير وتسربات وتركيب أدوات صحية وسخانات. تواصل مع أمين سرور على 0545350293.', category_page('plumbing')),
 ('/electrician-riyadh', 'electrician-riyadh.html', 'كهربائي بالرياض | صيانة الأعطال وتركيب الإنارة — أمين سرور', 'كهربائي للمنازل والفلل في النرجس والياسمين والعارض والملقا. صيانة أعطال وقواطع وأفياش وتركيب ثريات وإنارة. اطلب الخدمة من أمين سرور: 0545350293.', category_page('electrical')),
 ('/north-riyadh', 'north-riyadh.html', 'سباك وكهربائي شمال الرياض | النرجس والياسمين والعارض والملقا', 'خدمات أمين سرور للسباكة والكهرباء في أحياء شمال الرياض: النرجس والياسمين والعارض والملقا. تعرّف على نطاق الأعمال وجهز طلبك لتنسيق الزيارة.', north_riyadh_page()),
]
PAGES += [
    (path, path.lstrip('/') + '.html', group['title'] + ' | أمين سرور', group['description'], service_detail_page(path, group))
    for path, group in DETAIL_PAGES.items()
]
PAGES += [(article_route(post), 'blog/' + post['slug'] + '.html', post['title'] + ' | أمين سرور', post['description'], article_page(post)) for post in POSTS]
for path,filename,title,desc,body in PAGES:
    target = ROOT / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(path,title,desc,body).replace('960w','720w'),encoding='utf-8')
(ROOT/'404.html').write_text(render('/404','الصفحة غير موجودة | أمين سرور','ارجع إلى موقع أمين سرور لخدمات السباكة وصيانة الكهرباء في الرياض.',page_intro('الصفحة غير موجودة.','يمكنك العودة للرئيسية أو اختيار الخدمة التي تحتاجها.','404')+'<div class="wrap error-links">'+button('/','ارجع للرئيسية','primary','home')+button('/services','استكشف الخدمات','outline')+'</div>',True),encoding='utf-8')
entries = ''
for path, *_ in PAGES:
    loc = BASE if path == '/' else BASE.rstrip('/') + path
    post = POST_BY_ROUTE.get(path)
    modified = post.get('modified', PUBLISHED) if post else B.get('pageUpdatedOn', {}).get(path, B['contentUpdatedOn'])
    image_source = post or DETAIL_PAGES.get(path)
    image_entry = '<image:image><image:loc>' + BASE + PHOTOS[image_source['photo']]['src'] + '</image:loc></image:image>' if image_source else ''
    entries += '<url><loc>' + ESC(loc) + '</loc><lastmod>' + modified + '</lastmod>' + image_entry + '</url>'
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'+entries+'</urlset>')
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+BASE+'sitemap.xml\n')
manifest=json.loads((ROOT/'manifest.webmanifest').read_text())
manifest.update(name=B['name'],description='تأسيس وصيانة السباكة والكهرباء في الرياض — حي النرجس.',theme_color='#075a77',background_color='#f5f9fc')
(ROOT/'manifest.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(f'Built {len(PAGES) + 1} HTML pages; {len(SERVICES)} services; {len(REVIEWS["reviews"])} sourced reviews; shared business graph; clean canonical sitemap.')

