"""Builds Car_Dealership_Website_Essay.docx."""
from docx import Document
from docx.enum.section import WD_ORIENT  # noqa: F401
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FIGMA = ("https://www.figma.com/design/9o7bNFBTzlAQ5sV0kwD5D5/"
         "%D0%90%D0%B2%D1%82%D0%BE%D0%AF%D1%81%D0%BD%D0%BE-%E2%80%94-%D0%BF%D1%80%D0%BE%D1%82%D0%BE%D1%82%D0%B8%D0%BF-"
         "%D1%81%D0%B0%D0%B9%D1%82%D0%B0-%D0%B0%D0%B2%D1%82%D0%BE%D1%81%D0%B0%D0%BB%D0%BE%D0%BD%D0%B0?node-id=0-1")
FIGMA_SHORT = "https://www.figma.com/design/9o7bNFBTzlAQ5sV0kwD5D5"
BLACK = RGBColor(0, 0, 0)
FONT = "Times New Roman"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin, sec.right_margin = Cm(3), Cm(1)
sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)

normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(14)
normal.font.color.rgb = BLACK
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
pf = normal.paragraph_format
pf.line_spacing = 1.15
pf.space_before = Pt(0)
pf.space_after = Pt(0)


def _run(p, text, bold=False, italic=False, size=None):
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.name = FONT
    r.font.color.rgb = BLACK
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if size:
        r.font.size = Pt(size)
    return r


def para(text="", bold_lead=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True):
    p = doc.add_paragraph()
    p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    if bold_lead:
        _run(p, bold_lead, bold=True)
    _run(p, text)
    return p


def heading(text, page_break=False):
    p = doc.add_paragraph()
    if page_break:
        p.paragraph_format.page_break_before = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    _run(p, text, bold=True)


def subheading(text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    _run(p, text, bold=True)


def bullets(items):
    for it in items:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.first_line_indent = Cm(-0.5)
        if isinstance(it, tuple):
            _run(p, "– ")
            _run(p, it[0], bold=True)
            _run(p, it[1])
        else:
            _run(p, "– " + it)


def hyperlink(p, url, label):
    rid = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                           is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    for tag, val in (("w:rFonts", FONT), ("w:u", "single"), ("w:color", "000000")):
        e = OxmlElement(tag)
        if tag == "w:rFonts":
            e.set(qn("w:ascii"), val); e.set(qn("w:hAnsi"), val)
        else:
            e.set(qn("w:val"), val)
        rpr.append(e)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = label
    r.append(t)
    h.append(r)
    p._p.append(h)


fig_no = [0]


def figure(path, caption, width=16):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(path, width=Cm(width))
    fig_no[0] += 1
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    c.paragraph_format.line_spacing = 1.0
    _run(c, f"Рисунок {fig_no[0]} — {caption}", size=12)


def figure_grid(paths, labels, caption, cols=2, width=8.0):
    t = doc.add_table(rows=(len(paths) + cols - 1) // cols, cols=cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (path, lab) in enumerate(zip(paths, labels)):
        cell = t.rows[i // cols].cells[i % cols]
        cell.width = Cm(width + 0.3)
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.line_spacing = 1.0
        cp.paragraph_format.keep_with_next = True
        cp.add_run().add_picture(path, width=Cm(width))
        lp = cell.add_paragraph()
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lp.paragraph_format.line_spacing = 1.0
        lp.paragraph_format.space_after = Pt(4)
        _run(lp, lab, size=11)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    fig_no[0] += 1
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(6)
    c.paragraph_format.line_spacing = 1.0
    _run(c, f"Рисунок {fig_no[0]} — {caption}", size=12)


tab_no = [0]


def table(caption, header, rows, widths):
    tab_no[0] += 1
    c = doc.add_paragraph()
    c.paragraph_format.keep_with_next = True
    c.paragraph_format.space_before = Pt(6)
    _run(c, f"Таблица {tab_no[0]} — {caption}", size=12)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row_cells, data, is_head in [(t.rows[0].cells, header, True)] + [
            (t.add_row().cells, r, False) for r in rows]:
        for i, (cell, val) in enumerate(zip(row_cells, data)):
            cell.width = Cm(widths[i])
            cp = cell.paragraphs[0]
            cp.paragraph_format.line_spacing = 1.0
            cp.paragraph_format.first_line_indent = Cm(0)
            if is_head:
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _run(cp, val, bold=is_head or i == 0, size=11)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    hdr = t.rows[0]._tr.get_or_add_trPr()
    rep = OxmlElement("w:tblHeader")
    rep.set(qn("w:val"), "true")
    hdr.append(rep)
    doc.add_paragraph()


def page_numbers():
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = _run(p, "", size=12)
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        r._r.append(el)


page_numbers()
S = "shots/"


# ------------------------------------------------------------------ Заголовок
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
_run(p, "Эссе: проектирование сайта мультибрендового автосалона «АвтоЯсно»", bold=True)

heading("Введение")
para("Тема работы — сайт вымышленного мультибрендового автосалона «АвтоЯсно». Салон продаёт новые "
     "автомобили нескольких марок и автомобили с пробегом, принимает машины в зачёт (трейд-ин), помогает "
     "оформить кредит и записывает на тест-драйв. Название учебное, проверка торговой марки не проводилась.")
para("Покупатель автомобиля сегодня выбирает модель и сравнивает цены онлайн ещё до визита в салон. Поэтому "
     "сайт должен быстро ответить на три вопроса: какие машины есть в наличии, сколько они стоят в итоге и "
     "как быстро можно их посмотреть. Отсюда идея бренда: «АвтоЯсно» — сайт, на котором всё понятно.")

heading("Цели и тип сайта")
bullets([
    "показать каталог автомобилей в наличии с удобными фильтрами;",
    "указывать честную итоговую цену и пример ежемесячного платежа без скрытых условий;",
    "дать записаться на тест-драйв, рассчитать кредит и оценить свой автомобиль в 2–3 шага;",
    "вызвать доверие: реальные фото, гарантия, адрес и телефон салона на виду.",
])
para("Тип сайта — корпоративный сайт-каталог дилера с сервисными формами. Это не интернет-магазин: договор "
     "заключается в салоне, а сайт помогает выбрать автомобиль и привести клиента на осмотр и тест-драйв.")

heading("Целевая аудитория")
para("Основная аудитория — жители города и области 25–55 лет, которые планируют покупку в ближайшие месяцы. "
     "Многие заходят со смартфона, поэтому мобильная версия так же важна, как десктопная.")
table("Типовые пользователи",
      ["Профиль", "Цель", "Что важно на сайте"],
      [["Андрей, 32 года", "Первый новый автомобиль в кредит до 2,5 млн ₽", "Фильтр по цене и платежу, честная цена"],
       ["Ольга, 41 год", "Обменять старую машину на семейную", "Онлайн-оценка трейд-ина, сравнение моделей"],
       ["Игорь, 27 лет", "Недорогой автомобиль с пробегом", "Фото конкретной машины, история, гарантия"],
       ["Марина, 50 лет", "Нужна консультация", "Крупный текст, телефон и обратный звонок"]],
      [3.5, 6.5, 7.0])

heading("Основные сценарии", page_break=True)
bullets([
    ("Подбор и тест-драйв: ", "главная → быстрый подбор → каталог с фильтрами → карточка автомобиля → "
                              "форма тест-драйва с уже выбранной машиной."),
    ("Кредит: ", "карточка автомобиля → «В кредит от … ₽/мес» → калькулятор → заявка."),
    ("Трейд-ин: ", "карточка автомобиля → оценка по госномеру или VIN → запись на осмотр."),
])

# ------------------------------------------------------------------ Структура
heading("Структура сайта")
table("Разделы сайта",
      ["Раздел", "Содержание"],
      [["Главная", "Ценностное предложение, две главные кнопки, быстрый подбор, автомобили в наличии, преимущества"],
       ["Каталог", "Фильтры слева, поиск и сортировка, выбранные фильтры, сетка карточек, страницы"],
       ["Карточка автомобиля", "Фото, итоговая цена, платёж, тест-драйв, трейд-ин, характеристики"],
       ["Сравнение", "Таблица 2–4 автомобилей с выделением различий"],
       ["Кредит и трейд-ин", "Калькулятор кредита, оценка автомобиля по госномеру или VIN"],
       ["Тест-драйв", "Форма с выбранной машиной, датой и временем"],
       ["О салоне и контакты", "Адрес, карта, часы работы, гарантия, отзывы"]],
      [4.5, 12.5])


# ------------------------------------------------------------------ Конкуренты (не более 2 страниц)
heading("Анализ сайтов конкурентов", page_break=True)
para("Рассмотрены сайты четырёх крупных российских дилеров. Сайты просмотрены 13.11.2026; ниже описано только "
     "то, что удалось увидеть на открытых страницах.")
table("Сравнение сайтов конкурентов",
      ["Критерий", "РОЛЬФ", "Major Auto", "АВИЛОН", "FAVORIT MOTORS"],
      [["Каталог", "2 549 новых авто, платёж в списке", "По моделям, цены «от»", "2 148 авто, 5 сортировок",
        "641 авто, фильтр по платежу"],
       ["Цена в карточке", "—", "Со сносками и звёздочками", "С заранее отмеченным трейд-ином",
        "С тремя заранее отмеченными скидками"],
       ["Тест-драйв из карточки", "Не проверялся", "Не найден", "Есть", "Есть, выбор времени"],
       ["Трейд-ин онлайн", "Раздел «Продать»", "Форма не проверялась", "3 шага, госномер или VIN",
        "Только «Выкуп авто»"],
       ["Главная помеха", "Cookie поверх поиска", "Окно города, cookie, 7 виджетов", "Cookie до 45% экрана",
        "Перегруженное меню"]],
      [3.2, 3.4, 3.4, 3.5, 3.5])


def competitor(title, url, plus, ux, crit, idea):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(4)
    _run(p, title + " — ", bold=True)
    _run(p, url)
    for lead, txt in (("Плюсы: ", plus), ("Проблемы удобства: ", ux),
                      ("Критические недостатки: ", crit), ("Что взять: ", idea)):
        q = doc.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        q.paragraph_format.left_indent = Cm(0.75)
        _run(q, lead, bold=True)
        _run(q, txt)


competitor("РОЛЬФ", "https://www.rolf.ru/",
           "меню построено по действиям («Купить», «Продать», «Обслужить»); 60 брендов и 54 салона; в каталоге "
           "подробные фильтры и платёж в месяц.",
           "первый экран занят рекламным слайдером с темами не про выбор машины; плашка cookie закрывает поиск.",
           "на просмотренных страницах не выявлены.",
           "меню по действиям пользователя и ежемесячный платёж прямо в списке автомобилей.")
competitor("Major Auto", "https://www.major-auto.ru/",
           "много марок, сравнение и избранное, кнопка «Резерв онлайн».",
           "одновременно всплывают окно выбора города и крупная плашка cookie, сбоку висят семь виджетов; "
           "цены «от» со звёздочками.",
           "в карточке автомобиля не найдена запись на тест-драйв; на странице кредита указаны условия "
           "«до 30.04.2026», которые уже истекли.",
           "сравнение, избранное и онлайн-резерв автомобиля.")
competitor("АВИЛОН", "https://avilon.ru/",
           "поиск на главной с вкладками «Купить / Продать / Обменять / Сервис»; кредитный калькулятор "
           "в карточке; трейд-ин по госномеру или VIN.",
           "плашка cookie закрывает около трети экрана на компьютере и до 45% на телефоне; в карточках "
           "каталога нет кнопок.",
           "скидка за трейд-ин «−200 000 ₽» отмечена заранее; ставка в карточке (от 21,2%) не совпадает "
           "со ставкой на странице кредита (14%).",
           "вкладки поиска по цели посетителя и короткая оценка трейд-ина.")
competitor("FAVORIT MOTORS", "https://favorit-motors.ru/",
           "фильтр по ежемесячному платежу; кнопки «Записаться на тест-драйв» и «Проверить доступность»; "
           "в форме тест-драйва можно выбрать время.",
           "очень длинные выпадающие меню; яркая кнопка «Музей» и реклама шин рядом с фильтрами отвлекают.",
           "в карточке заранее отмечены три скидки (кредит, трейд-ин, КАСКО), поэтому крупная цена не "
           "подходит покупателю за наличные.",
           "фильтр по платежу и выбор времени тест-драйва готовыми интервалами.")

subheading("Вывод: что повлияет на проект")
para("Функций у конкурентов много, но им не хватает прозрачности и чистого интерфейса. Поэтому в «АвтоЯсно»: "
     "одна итоговая цена без заранее отмеченных скидок; кнопка тест-драйва в каждой карточке; не больше одного "
     "всплывающего элемента; меню по действиям; фильтр по платежу, сравнение и оценка трейд-ина по VIN.")

heading("Визуальная концепция")
para("Стиль спокойный и деловой: белый фон, светло-серые блоки, графитовый текст и один синий акцент для "
     "кнопок и ссылок. Шрифт — Inter с поддержкой кириллицы. Подробно фирменный стиль описан в брендбуке на "
     "странице «Brand Book» того же Figma-файла: логотип, цвета, шрифты, компоненты и примеры носителей.")
table("Цветовая палитра",
      ["Цвет", "HEX", "Назначение"],
      [["Белый", "#FFFFFF", "Фон страниц и карточек"],
       ["Светло-серый", "#F1F4F8", "Подложки блоков, панель фильтров"],
       ["Графитовый", "#17202C", "Текст и заголовки"],
       ["Синий", "#1A56DB", "Кнопки, ссылки, активные элементы"],
       ["Серо-голубой", "#D3DAE3", "Рамки и разделители"]],
      [4.0, 3.0, 10.0])

# ------------------------------------------------------------------ Прототип
heading("Схематичный прототип в Figma")
para("Схемы главной страницы и каталога нарисованы в Figma из редактируемых элементов: прямоугольников, "
     "подписей, кнопок, полей и заглушек фотографий. Они показывают расположение блоков, а не окончательный "
     "дизайн. В том же файле есть цветной прототип ключевых страниц и брендбук.")
p = para("Ссылка на Figma-файл: ", align=WD_ALIGN_PARAGRAPH.LEFT)
hyperlink(p, FIGMA, FIGMA_SHORT)
_run(p, ".")
figure(S + "wf_home.png", "Схема главной страницы: шапка с меню, первый экран, быстрый подбор, "
       "автомобили в наличии, преимущества, подвал", width=15.5)
figure(S + "wf_catalog.png", "Схема каталога: фильтры слева, поиск и сортировка, выбранные фильтры, "
       "сетка карточек, переключатель страниц", width=15.5)

heading("Заключение")
para("Разработана концепция сайта автосалона «АвтоЯсно». Анализ сайтов РОЛЬФ, Major Auto, АВИЛОН и FAVORIT "
     "MOTORS показал, что главные проблемы дилерских сайтов — непрозрачная цена и перегруженный интерфейс. "
     "Проект берёт у конкурентов удачные решения (меню по действиям, фильтр по платежу, сравнение, оценку "
     "трейд-ина) и добавляет к ним одну итоговую цену, короткий путь к тест-драйву и спокойный визуальный стиль.")

doc.save("Car_Dealership_Website_Essay.docx")
print("saved")
