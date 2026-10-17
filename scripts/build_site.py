"""Build the static Arabic site from one verified business data source; no runtime dependencies."""
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
B = json.loads((ROOT / 'business-data.json').read_text())
MEDIA = json.loads((ROOT / 'service-media.json').read_text())
PHOTOS = {photo['key']: photo for photo in MEDIA['photos']}
FEATURED = ['plumbing-installation', 'water-leaks', 'basins', 'electrical-installation', 'electrical-maintenance', 'chandeliers']
BASE = B['url']
ESC = html.escape
MAP = B['mapUrl']
ADDRESS = B['streetAddress'] + '، ' + B['addressLocality'] + ' ' + B['postalCode']
PHONE = B['telephone']

# Names reflect the services currently listed on the Business Profile. The descriptions
# are public-facing explanations, without invented prices, guarantees or response times.
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

def button(href, text, kind='primary', glyph='arrow', extra=''):
    external = ' target="_blank" rel="noopener noreferrer"' if href.startswith('https://') else ''
    glyph_markup = icon('whatsapp', 'white' if kind in ('primary', 'outline-light') else ('black' if kind == 'gold' else 'green')) if href.startswith(B['whatsapp']) else icon(glyph)
    return f'<a class="button button-{kind}" href="{ESC(href)}"{external} {extra}>{glyph_markup}<span>{text}</span></a>'

NAV = [('/','الرئيسية'),('/services','الخدمات'),('/#work','أعمالنا'),('/about','عن أمين سرور'),('/blog','دليل العميل'),('/contact','تواصل معنا')]

def header(path):
    links=''.join(f'<a href="{u}"'+(' aria-current="page"' if u==path else '')+f'>{n}</a>' for u,n in NAV)
    return f'''<div class="topline"><div class="wrap"><span>{icon('map')} النرجس، الرياض</span><span>{icon('clock')} على مدار الساعة · طوال الأسبوع</span><a href="{ESC(MAP)}" target="_blank" rel="noopener noreferrer">موقعنا على الخريطة {icon('arrow')}</a></div></div>
<header class="site-header" id="top"><div class="wrap header-inner"><a class="brand" href="/" aria-label="أمين سرور، الصفحة الرئيسية"><img src="/assets/brand-mark.svg" width="52" height="52" alt=""><span><strong>أمين سرور</strong><small>للسباكة وصيانة الكهرباء</small></span></a><nav id="main-nav" aria-label="التنقل الرئيسي">{links}</nav><a class="header-call" aria-label="اتصل بأمين سرور على 0545350293" href="tel:{PHONE}">{icon('phone')}<b dir="ltr">{B['displayPhone']}</b></a><button class="menu-toggle" aria-label="فتح القائمة" aria-controls="main-nav" aria-expanded="false">{icon('menu')}</button></div></header>'''

def footer():
    return f'''<footer class="site-footer"><div class="wrap footer-grid"><div class="footer-about"><a class="brand" href="/"><img src="/assets/brand-mark.svg" width="50" height="50" alt=""><span><strong>أمين سرور</strong><small>للسباكة وصيانة الكهرباء</small></span></a><p>أعمال التأسيس والصيانة للسباكة والكهرباء في المنازل والشقق والفلل بالرياض. تواصل مباشرة واشرح طلبك لتنسيق الخدمة.</p><a class="social-link" href="{B['instagram']}" target="_blank" rel="noopener noreferrer">{icon('instagram')} تابع أعمالنا على إنستغرام</a></div><div><h2>استكشف الموقع</h2><div class="footer-links"><a href="/services">خدمات السباكة والكهرباء</a><a href="/#work">صور من أعمالنا</a><a href="/about">عن أمين سرور</a><a href="/blog">دليل العميل</a><a href="/contact">التواصل والموقع</a></div></div><div><h2>بيانات التواصل</h2><a class="contact-line" href="tel:{PHONE}">{icon('phone')}<b dir="ltr">{B['displayPhone']}</b></a><p class="contact-line">{icon('map')}<span>{ESC(ADDRESS)}</span></p><p class="contact-line">{icon('clock')}<span>24 ساعة، 7 أيام في الأسبوع</span></p></div></div><div class="wrap footer-bottom"><p>© <span id="current-year">2026</span> {B['name']}</p><a href="https://www.eslam-elshikh.com/" target="_blank" rel="noopener noreferrer">التصميم والتطوير <strong>المهندس إسلام الشيخ</strong> {icon('arrow')}</a></div></footer><nav class="contact-dock" aria-label="التواصل السريع"><a class="floating-contact floating-whatsapp" href="{ESC(wa())}" target="_blank" rel="noopener noreferrer" aria-label="تواصل مع أمين سرور عبر واتساب">{icon('whatsapp')}<span class="floating-label" aria-hidden="true">تواصل عبر واتساب</span></a><a class="floating-contact floating-phone" href="tel:{PHONE}" aria-label="اتصل بأمين سرور على 0545350293">{icon('phone')}<span class="floating-label" aria-hidden="true">اتصل الآن</span></a></nav>'''

def section_heading(kicker, title, intro='', link=''):
    return f'<div class="section-heading"><div><span class="eyebrow">{kicker}</span><h2>{title}</h2>'+ (f'<p>{intro}</p>' if intro else '') + '</div>' + link + '</div>'

def page_intro(title, intro, label):
    return f'<section class="page-intro"><div class="wrap"><nav class="breadcrumbs" aria-label="مسار التنقل"><a href="/">الرئيسية</a><span>/</span><span aria-current="page">{label}</span></nav><span class="eyebrow">أمين سرور · الرياض</span><h1>{title}</h1><p>{intro}</p></div></section>'

def service_card(service, index, full=False):
    slug, name, cat, desc, glyph=service
    href=wa(f'مرحبًا، أرغب في طلب خدمة {name}. الموقع في حي: ')
    details=MEDIA['services'][slug]
    photo=PHOTOS[details['photo']]
    category='أعمال السباكة' if cat=='plumbing' else 'الكهرباء والإنارة'
    points=''.join(f'<li>{icon("check")}<span>{ESC(point)}</span></li>' for point in details['points'])
    variant='white' if cat=='plumbing' else 'black'
    return f'''<article class="service-card service-card--{cat}" id="{slug}" data-category="{cat}"><div class="service-media"><img src="/{photo['src']}" srcset="/{photo['small']} 480w, /{photo['src']} 800w" sizes="(max-width: 600px) 92vw, (max-width: 920px) 46vw, 410px" width="800" height="500" alt="{ESC(photo['alt'])}" loading="lazy" decoding="async"><span class="service-photo-badge">{icon(glyph)}{category}</span><span class="service-photo-number" aria-hidden="true">{index:02d}</span></div><div class="service-copy"><h3>{name}</h3><p>{desc}</p><ul class="service-points" aria-label="تفاصيل الخدمة">{points}</ul><div class="service-actions"><a class="service-order" href="{ESC(href)}" target="_blank" rel="noopener noreferrer" aria-label="اطلب خدمة {ESC(name)} عبر واتساب">{icon('whatsapp',variant)}<span>اطلب الخدمة</span>{icon('arrow')}</a><a class="service-phone" href="tel:{PHONE}" aria-label="اتصل لطلب خدمة {ESC(name)} على 0545350293">{icon('phone')}</a></div></div></article>'''

def cta():
    return f'<section class="section cta-section" id="contact"><div class="wrap cta-panel"><div><span class="eyebrow">خلّنا نعرف وش تحتاج</span><h2>عطل بسيط أو تأسيس جديد؟<br>ابدأ بتواصل مباشر.</h2><p>اشرح طلبك وأرسل صور المكان واسم الحي. ننسّق معك الخدمة والموعد حسب تفاصيل الطلب.</p></div><div class="cta-actions">{button(wa(),'أرسل تفاصيل طلبك','gold','chat')}{button("tel:"+PHONE,'<b dir="ltr">'+B['displayPhone']+'</b>','outline-light','phone')}<span>{icon('clock')} العمل على مدار الساعة</span></div></div></section>'

def faq():
    return '<section class="section faq-section" id="faq"><div class="wrap faq-layout"><div>'+section_heading('إجابات تهمك','قبل ما تطلب الخدمة','معلومات واضحة عن الخدمات والتواصل والمواعيد.')+button('/contact','عندك استفسار آخر؟','outline','chat')+'</div><div class="accordion">'+''.join(f'<details><summary>{q}{icon("plus")}</summary><p>{a}</p></details>' for q,a in FAQ)+'</div></div></section>'

def location():
    return f'''<section class="section location-section" id="areas"><div class="wrap location-layout"><div>{section_heading('قريب من تفاصيل بيتك','في النرجس، ونخدم الرياض.','تأسيس وصيانة السباكة والكهرباء داخل مدينة الرياض. أرسل موقعك ونوع الخدمة لتنسيق الزيارة.')}<address>{icon('map')}<span>{ADDRESS}</span></address><div class="location-actions">{button(MAP,'افتح الموقع على خرائط Google','primary','map')}{button('/contact','تفاصيل التواصل','outline')}</div><p class="small-note">لتنسيق الزيارة أو الاستفسار عن الوصول، تواصل معنا أولًا.</p></div><div class="map-card"><div class="map-card-head"><span>{icon('map')} موقع أمين سرور</span><span>الرياض · النرجس</span></div><iframe title="موقع أمين سرور في حي النرجس بالرياض" src="https://www.google.com/maps?q=أمين%20سرور%20لخدمات%20السباكة%20وصيانة%20الكهرباء&amp;cid=809316932329652691&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe><a href="{ESC(MAP)}" target="_blank" rel="noopener noreferrer">عرض الموقع والاتجاهات {icon('arrow')}</a></div></div></section>'''

def work():
    images=[('interior','تركيبات مغاسل وإنارة داخلية','مغاسل وتجهيزات إنارة داخلية من صور أعمال أمين سرور'),('basins','تركيب وتجهيز المغاسل','تركيب مغاسل وخلاطات من أعمال أمين سرور'),('showroom','الأدوات وتجهيزات السباكة','أدوات وتجهيزات السباكة الظاهرة في صور ملف أمين سرور')]
    return '<section class="section work-section" id="work"><div class="wrap">'+section_heading('الصورة توضح التفاصيل','من أعمالنا وتجهيزاتنا.','صور حقيقية من الملف التجاري لأمين سرور.',button(B['instagram'],'شاهد المزيد','outline','instagram'))+'<div class="work-grid">'+''.join(f'<figure><img src="/assets/{name}.webp" srcset="/assets/{name}-sm.webp 480w, /assets/{name}.webp 960w" sizes="(max-width: 600px) 90vw, 33vw" width="720" height="960" alt="{alt}" loading="lazy" decoding="async"><figcaption><span>0{i+1}</span><h3>{title}</h3></figcaption></figure>' for i,(name,title,alt) in enumerate(images))+'</div></div></section>'

def home():
    featured=FEATURED
    featured_cards=''.join(service_card(next(s for s in SERVICES if s[0]==slug),i+1) for i,slug in enumerate(featured))
    return f'''<section class="hero"><div class="wrap hero-grid"><div class="hero-copy"><span class="hero-location">{icon('map')} الرياض · حي النرجس <i></i> 24 / 7</span><p class="hero-business">{B['name']}</p><h1>سباكة وكهرباء.<br><span>شغل يريح بالك.</span></h1><p class="hero-lead">من أول تمديد إلى آخر لمسة إنارة. تأسيس وصيانة السباكة والكهرباء للمنازل والشقق والفلل في الرياض، بتواصل مباشر مع أمين سرور.</p><div class="hero-actions">{button(wa(),'اطلب خدمتك عبر واتساب','primary','chat')}{button('tel:'+PHONE,'اتصال مباشر','outline','phone')}</div><div class="hero-review"><span class="stars" aria-label="5 من 5 نجوم">★★★★★</span><strong dir="ltr">5.0</strong><span>من 14 مراجعة على Google</span><a href="{MAP}" target="_blank" rel="noopener noreferrer" aria-label="اقرأ مراجعات أمين سرور على Google">{icon('arrow')}</a></div></div><div class="hero-visual"><img class="hero-photo" src="/assets/interior.webp" srcset="/assets/interior-sm.webp 480w, /assets/interior.webp 960w" sizes="(max-width: 760px) 92vw, 46vw" width="720" height="960" alt="تركيبات مغاسل وإنارة داخلية من صور أعمال أمين سرور" fetchpriority="high" decoding="async"><div class="photo-label">{icon('check')} من صور أعمالنا الفعلية</div><div class="hero-ticket"><span class="ticket-icon">{icon('water')}{icon('bolt')}</span><div><strong>تأسيس. صيانة. إنارة.</strong><small>خدمات متكاملة لبيتك في الرياض</small></div>{icon('arrow')}</div><span class="visual-index" aria-hidden="true">AMEEN / HOME SERVICES</span></div></div></section>
<section class="promise-strip" aria-label="لمحة عن الخدمة"><div class="wrap"><div>{icon('tool')}<span><strong>من التأسيس للصيانة</strong><small>سباكة وكهرباء وإنارة</small></span></div><div>{icon('phone')}<span><strong>تواصل مباشر</strong><small>اتصال أو واتساب</small></span></div><div>{icon('clock')}<span><strong>طوال أيام الأسبوع</strong><small>العمل على مدار الساعة</small></span></div></div></section>
<section class="section services-section" id="services"><div class="wrap">{section_heading('وش يحتاج بيتك؟','لكل تفصيلة، خدمة تناسبها.','خدمات واضحة بصور من ملف النشاط، من تأسيس الشبكات إلى صيانة الأعطال وتركيب الأدوات الصحية والإنارة.',button('/services','كل الخدمات','outline'))}<div class="service-grid">{featured_cards}</div></div></section>
<section class="section process-section"><div class="wrap process-layout"><div><span class="eyebrow">طلبك يبدأ بخطوة بسيطة</span><h2>خلّ التفاصيل واضحة،<br>من أول تواصل.</h2><p>نوع الخدمة، صورة للمشكلة، واسم الحي. تفاصيل تساعد على فهم طلبك وتنسيق الزيارة المناسبة.</p>{button('/contact#request','جهّز طلبك على واتساب','primary','chat')}</div><ol class="process-list"><li><span>01</span><div><h3>اشرح احتياجك</h3><p>سباكة، كهرباء أو إنارة؟ أرسل وصفًا مختصرًا لما تحتاجه.</p></div></li><li><span>02</span><div><h3>أرسل الصورة والموقع</h3><p>صورة واضحة واسم الحي يوضحان طبيعة العمل ومكانه.</p></div></li><li><span>03</span><div><h3>نسّق الزيارة والتنفيذ</h3><p>تأكد من الموعد ونطاق العمل والتكلفة المتفق عليها قبل البدء.</p></div></li></ol></div></section>{work()}{location()}{faq()}{cta()}'''

def services_page():
    filters='<div class="catalog-toolbar"><div class="catalog-heading"><div><span class="eyebrow">صور من الملف التجاري · تفاصيل واضحة</span><h2>اختر الخدمة اللي تحتاجها.</h2></div><p class="filter-status" role="status" aria-live="polite">عرض 26 خدمة</p></div><div class="catalog-controls"><div class="service-search"><label class="sr-only" for="service-search">ابحث عن خدمة</label><input id="service-search" type="search" autocomplete="off" placeholder="ابحث: تسرب، مغاسل، ثريات…"></div><div class="service-filters" role="group" aria-label="تصفية الخدمات"><button data-filter="all" aria-pressed="true">كل الخدمات <span>26</span></button><button data-filter="plumbing" aria-pressed="false">السباكة <span>14</span></button><button data-filter="electrical" aria-pressed="false">الكهرباء والإنارة <span>12</span></button></div></div></div>'
    empty='<div class="service-empty" hidden><h3>ما لقينا خدمة مطابقة للبحث.</h3><p>جرّب كلمة أقصر، أو اعرض كل خدمات السباكة والكهرباء.</p><button type="button" id="reset-services" class="button button-primary">اعرض كل الخدمات</button></div>'
    return page_intro('خدمات السباكة والكهرباء في الرياض.','صور وتفاصيل تساعدك تختار الخدمة الأقرب لاحتياجك. ابحث أو صفّ الخدمات، ثم تواصل معنا لشرح الطلب وتنسيق الزيارة.','الخدمات')+'<section class="section service-catalog"><div class="wrap">'+filters+'<div class="service-grid">'+''.join(service_card(s,i+1,True) for i,s in enumerate(SERVICES))+'</div>'+empty+'</div></section>'+faq()+cta()

def about():
    return page_intro('أمين سرور. عناية بتفاصيل بيتك.','أعمال التأسيس والصيانة للسباكة والكهرباء في المنازل والشقق والفلل بمدينة الرياض.','عن أمين سرور')+f'''<section class="section"><div class="wrap about-layout"><div class="about-photo"><img src="/assets/basins.webp" width="720" height="960" alt="تجهيز وتركيب المغاسل من أعمال أمين سرور" loading="lazy"><span>{icon('water')} سباكة {icon('bolt')} كهرباء</span></div><div class="prose"><span class="eyebrow">عن النشاط</span><h2>خدمات بيتك،<br>بتواصل مباشر.</h2><p>{B['description']}</p><h3>توضيح الطلب يسهّل البداية</h3><p>سواء كان احتياجك إصلاح وصلة مياه أو تأسيس شبكة كهرباء أو تركيب ثريا، ابدأ بوصف الحالة وإرسال صور المكان. بهذه التفاصيل يمكن تنسيق الزيارة ومناقشة نطاق التنفيذ.</p><div class="about-facts"><span>{icon('map')} النرجس، الرياض</span><span>{icon('clock')} على مدار الساعة</span></div>{button('/services','استكشف الخدمات','primary')}{button(MAP,'ملفنا على Google','outline','map')}</div></div></section>'''+work()+location()+cta()

def contact():
    options=''.join(f'<option value="{ESC(s[1])}">{s[1]}</option>' for s in SERVICES)
    hours=''.join(f'<div><span>{day}</span><strong>24 ساعة</strong></div>' for day in ['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'])
    return page_intro('قل لنا وش تحتاج، ونبدأ من هنا.','اتصال مباشر أو رسالة واتساب لتوضيح الخدمة وموقع الطلب في الرياض.','تواصل معنا')+f'''<section class="section"><div class="wrap contact-layout"><div><div class="contact-choice"><span class="service-icon">{icon('phone')}</span><span>للاتصال المباشر</span><a class="big-phone" href="tel:{PHONE}" dir="ltr">{B['displayPhone']}</a><p>استفسر عن الخدمة المطلوبة والتوفر وموعد الزيارة.</p>{button('tel:'+PHONE,'اتصل بأمين سرور','primary','phone')}</div><div class="hours-card"><h2>{icon('clock')} مواعيد العمل</h2><div class="hours-list">{hours}</div><p>لتأكيد الموعد والتوفر، تواصل قبل الزيارة.</p></div></div><section class="request-card" id="request" aria-labelledby="request-title"><span class="eyebrow">رسالة مرتبة تسهّل الطلب</span><h2 id="request-title">جهّز طلبك على واتساب.</h2><p>اختر الخدمة، وأضف اسم الحي ووصفًا مختصرًا. يفتح الزر الرسالة في واتساب لمراجعتها وإرسالها.</p><label for="request-service">الخدمة المطلوبة</label><select id="request-service"><option value="خدمات السباكة وصيانة الكهرباء">اختر الخدمة</option>{options}</select><label for="request-area">اسم الحي في الرياض <span>(اختياري)</span></label><input id="request-area" name="area" autocomplete="address-level3" maxlength="80" placeholder="مثال: النرجس"><label for="request-details">تفاصيل الطلب <span>(اختياري)</span></label><textarea id="request-details" rows="4" maxlength="800" placeholder="اشرح المشكلة أو العمل المطلوب باختصار"></textarea>{button(wa(),'افتح الرسالة في واتساب','primary','chat','id="request-link"')}<p class="small-note">يمكنك إرفاق الصور بعد فتح المحادثة.</p></section></div></section>'''+location()+faq()

def blog():
    return page_intro('دليل عملي قبل طلب السباك أو الكهربائي.','أسئلة وتجهيزات بسيطة تساعدك على توضيح العطل واختيار الخدمة ومناقشة نطاق العمل.','دليل العميل')+'''<section class="section"><div class="wrap article-layout"><aside class="article-toc"><h2>في هذا الدليل</h2><a href="#describe">01 · حدّد المشكلة</a><a href="#prepare">02 · جهّز تفاصيل طلبك</a><a href="#agree">03 · اتفق على نطاق العمل</a><a href="#care">04 · راجع العمل بعد التنفيذ</a><a href="/services">استكشف الخدمات ←</a></aside><article class="prose article-body"><span class="eyebrow">دليل أمين سرور للعميل</span><h2 id="describe">ابدأ بوصف ما تلاحظه.</h2><p>هل يوجد تسرب ظاهر تحت المغسلة، أم رطوبة لا تعرف مصدرها؟ وهل توقفت نقطة إنارة واحدة، أم يتكرر فصل القاطع؟ وصف العلامة ومكانها ووقت ظهورها أوضح من الاكتفاء بعبارة «السباكة خربانة» أو «الكهرباء تفصل».</p><div class="article-callout">العطل الظاهر في حنفية أو وصلة يناسب طلب صيانة السباكة. أما التسرب غير معلوم المصدر، فابدأ بالاستفسار عن فحص وكشف التسربات.</div><h2 id="prepare">جهّز ثلاث معلومات قبل التواصل.</h2><ul><li><strong>نوع الخدمة:</strong> صيانة سباكة، تأسيس كهرباء، تركيب ثريا أو غير ذلك.</li><li><strong>صورة واضحة:</strong> للمكان أو القطعة المتأثرة، دون لمس أجزاء كهربائية أو تعريض نفسك للخطر.</li><li><strong>الموقع:</strong> اسم الحي ورابط الموقع عند تنسيق الزيارة.</li></ul><p>في أعمال التأسيس، وضّح مرحلة المبنى ونوعه وعدد النقاط المطلوبة مبدئيًا، وشارك المخطط المتاح عند الحاجة. هذه التفاصيل تساعد على تحديد ما يلزم للمعاينة.</p><h2 id="agree">ناقش نطاق العمل قبل التكلفة النهائية.</h2><p>تختلف تكلفة العمل باختلاف حالة التمديدات ومكان العطل والقطع اللازمة وإمكانية الوصول. اسأل عما يشمله السعر، ومن يوفر القطع، وهل يتطلب التنفيذ أعمالًا إضافية، وما الذي سيتم فحصه وتجربته بعد الإصلاح.</p><p>إذا تغير نطاق العمل أثناء الفحص، اطلب توضيح التغيير والتكلفة قبل تنفيذه. لا تعتمد على سعر عام لخدمة تختلف تفاصيلها من موقع إلى آخر.</p><h2 id="care">راجع النقطة التي تم العمل عليها.</h2><p>بعد أعمال السباكة، راقب تشغيل المياه والتصريف والوصلات التي جرى إصلاحها. وبعد تركيب الإنارة أو صيانة الكهرباء، اطلب من الفني تجربة النقاط المتأثرة وشرح الملاحظات المرتبطة بالاستخدام.</p><div class="article-callout safety"><strong>عند وجود خطر واضح</strong><p>ابتعد عن المياه القريبة من الكهرباء، ولا تلمس الأسلاك أو تفتح لوحة الكهرباء. استعن بفني لتقييم الحالة، ولا تحاول إعادة تشغيل دائرة يتكرر فصلها قبل معرفة السبب.</p></div></article></div></section>'''+cta()

def graph(path, title, desc):
    url=BASE.rstrip('/')+path if path!='/' else BASE
    address={'@type':'PostalAddress','streetAddress':B['streetAddress'],'addressLocality':B['addressLocality'],'addressRegion':B['addressRegion'],'postalCode':B['postalCode'],'addressCountry':'SA'}
    business={'@type':['Plumber','Electrician'],'@id':BASE+'#business','name':B['name'],'alternateName':'أمين سرور للسباكة والكهرباء','url':BASE,'telephone':PHONE,'description':B['description'],'logo':{'@id':BASE+'#logo'},'image':[BASE+'assets/interior.webp',BASE+'assets/basins.webp',BASE+'assets/showroom.webp'],'address':address,'areaServed':{'@type':'City','name':'الرياض'},'hasMap':MAP,'sameAs':[MAP,B['instagram']],'openingHours':B['openingHours'],'openingHoursSpecification':[{'@type':'OpeningHoursSpecification','dayOfWeek':['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],'opens':'00:00','closes':'23:59'}],'contactPoint':[{'@type':'ContactPoint','telephone':PHONE,'contactType':'customer service','availableLanguage':['Arabic'],'areaServed':{'@type':'City','name':'الرياض'},'url':B['whatsapp']}],'hasOfferCatalog':{'@id':BASE+'services#catalog'}}
    nodes=[business,{'@type':'ImageObject','@id':BASE+'#logo','url':BASE+'assets/brand-mark.svg','contentUrl':BASE+'assets/brand-mark.svg','caption':B['name']},{'@type':'WebSite','@id':BASE+'#website','url':BASE,'name':B['name'],'inLanguage':'ar-SA','publisher':{'@id':BASE+'#business'}},{'@type':'ContactPage' if path=='/contact' else ('AboutPage' if path=='/about' else 'WebPage'),'@id':url+'#webpage','url':url,'name':title,'description':desc,'isPartOf':{'@id':BASE+'#website'},'about':{'@id':BASE+'#business'},'inLanguage':'ar-SA','primaryImageOfPage':{'@id':BASE+'#primaryimage'}},{'@type':'ImageObject','@id':BASE+'#primaryimage','url':BASE+'assets/interior.webp','contentUrl':BASE+'assets/interior.webp','width':720,'height':960,'caption':'تركيبات مغاسل وإنارة داخلية من صور أعمال أمين سرور'}]
    if path!='/':
        label={'/services':'الخدمات','/about':'عن أمين سرور','/blog':'دليل العميل','/contact':'تواصل معنا'}.get(path,title)
        nodes.append({'@type':'BreadcrumbList','@id':url+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':1,'name':'الرئيسية','item':BASE},{'@type':'ListItem','position':2,'name':label,'item':url}]})
        nodes[3]['breadcrumb']={'@id':url+'#breadcrumb'}
    selected=SERVICES if path=='/services' else ([s for s in SERVICES if s[0] in FEATURED] if path=='/' else [])
    if selected:
        nodes.append({'@type':'OfferCatalog','@id':BASE+'services#catalog','name':'خدمات أمين سرور للسباكة والكهرباء','url':BASE+'services','itemListElement':[{'@type':'Offer','itemOffered':{'@id':BASE+'services#'+s[0]}} for s in selected]})
        for slug,name,cat,desc,glyph in selected:
            photo=PHOTOS[MEDIA['services'][slug]['photo']]
            nodes.append({'@type':'Service','@id':BASE+'services#'+slug,'name':name,'image':{'@type':'ImageObject','url':BASE+photo['src'],'contentUrl':BASE+photo['src'],'width':800,'height':500,'caption':photo['alt']},'serviceType':'السباكة' if cat=='plumbing' else 'الكهرباء والإنارة','description':desc,'url':BASE+'services#'+slug,'provider':{'@id':BASE+'#business'},'areaServed':{'@type':'City','name':'الرياض'},'availableChannel':{'@type':'ServiceChannel','serviceUrl':wa('مرحبًا، أرغب في طلب خدمة '+name),'servicePhone':{'@type':'ContactPoint','telephone':PHONE,'availableLanguage':'Arabic'}}})
    return {'@context':'https://schema.org','@graph':nodes}

def render(path,title,description,body,noindex=False):
    canonical=BASE if path=='/' else BASE.rstrip('/')+path
    cards_css='<link rel="stylesheet" href="/service-cards.css?v=20261017-photos">' if path in ('/', '/services') else ''
    schema=json.dumps(graph(path,title,description),ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    return f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#075a77"><meta name="color-scheme" content="light"><title>{ESC(title)}</title><meta name="description" content="{ESC(description)}"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-image-preview:large'}"><link rel="canonical" href="{canonical}"><link rel="icon" href="/assets/brand-mark.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><link rel="preload" href="/assets/fonts/noto-arabic-regular.woff" as="font" type="font/woff" crossorigin><link rel="stylesheet" href="/style.css?v=20261017-water-electric">{cards_css}<meta property="og:type" content="website"><meta property="og:locale" content="ar_SA"><meta property="og:site_name" content="{B['name']}"><meta property="og:title" content="{ESC(title)}"><meta property="og:description" content="{ESC(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{BASE}assets/share-ameen.jpg?v=20261017-water-electric"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="أمين سرور للسباكة وصيانة الكهرباء في الرياض"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{ESC(title)}"><meta name="twitter:description" content="{ESC(description)}"><meta name="twitter:image" content="{BASE}assets/share-ameen.jpg?v=20261017-water-electric"><script type="application/ld+json">{schema}</script><script src="/script.js?v=20261017-services" defer></script></head><body><a class="skip-link" href="#main-content">انتقل إلى المحتوى</a>{SPRITE}{header(path)}<main id="main-content">{body}</main>{footer()}</body></html>'''

PAGES=[
 ('/','index.html','سباك وكهربائي بالرياض | أمين سرور — النرجس، 24 ساعة','أمين سرور لخدمات السباكة وصيانة الكهرباء في الرياض، حي النرجس. تأسيس وصيانة وتركيب أدوات صحية وثريات وإنارة. اتصال وواتساب: 0545350293. العمل 24 ساعة.',home()),
 ('/services','services.html','خدمات السباكة والكهرباء بالرياض | أمين سرور','خدمات تأسيس وصيانة السباكة والكهرباء وإصلاح المواسير والتسربات وتركيب السخانات والمغاسل والثريات والإنارة بالرياض. اختر خدمتك وتواصل مباشرة مع أمين سرور.',services_page()),
 ('/about','about.html','عن أمين سرور لخدمات السباكة وصيانة الكهرباء | الرياض','تعرف على أمين سرور لخدمات السباكة وصيانة الكهرباء للمنازل والفلل في الرياض. عنوان النشاط في حي النرجس، والتواصل على 0545350293 طوال أيام الأسبوع.',about()),
 ('/blog','blog.html','دليل طلب سباك وكهربائي في الرياض | أمين سرور','دليل عملي لوصف أعطال السباكة والكهرباء وتجهيز تفاصيل الطلب ومناقشة نطاق العمل والتكلفة قبل التنفيذ مع أمين سرور في الرياض.',blog()),
 ('/contact','contact.html','تواصل مع أمين سرور | سباك وكهربائي النرجس بالرياض','اتصل أو واتساب أمين سرور على 0545350293. العنوان: 6488 أنس ابن مالك، الرقم الإضافي 3571، النرجس، الرياض 13327. العمل على مدار الساعة طوال الأسبوع.',contact()),
]
for path,filename,title,desc,body in PAGES:
    (ROOT/filename).write_text(render(path,title,desc,body).replace('960w','720w'),encoding='utf-8')
(ROOT/'404.html').write_text(render('/404','الصفحة غير موجودة | أمين سرور','ارجع إلى موقع أمين سرور لخدمات السباكة وصيانة الكهرباء في الرياض.',page_intro('الصفحة غير موجودة.','يمكنك العودة للرئيسية أو اختيار الخدمة التي تحتاجها.','404')+'<div class="wrap error-links">'+button('/','ارجع للرئيسية','primary','home')+button('/services','استكشف الخدمات','outline')+'</div>',True),encoding='utf-8')
entries=''.join(f'<url><loc>{BASE if p=="/" else BASE.rstrip("/")+p}</loc><lastmod>2026-10-17</lastmod></url>' for p,*rest in PAGES)
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+entries+'</urlset>')
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+BASE+'sitemap.xml\n')
manifest=json.loads((ROOT/'manifest.webmanifest').read_text())
manifest.update(name=B['name'],description='تأسيس وصيانة السباكة والكهرباء في الرياض — حي النرجس.',theme_color='#075a77',background_color='#f5f9fc')
(ROOT/'manifest.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Built 6 HTML pages; 26 services; shared business graph; clean canonical sitemap.')
