#!/usr/bin/env python3
"""Готовит тему и htmlBody черновика Gmail из файла письма.

Запуск: python3 инструменты/черновик.py письма/Название.md
Печатает JSON: subject, htmlBody, body, errors. Если errors не пустой,
черновик НЕ создавать: сначала исправить файл письма.

Почему так: при копировании из Gmail в WhatsApp абзацы в тегах <p>
слипаются («ждут.Зашла»). Поэтому абзацы только через <br><br>,
а в конце каждой строки стоит пробел.
"""
import html, json, re, sys

URL = re.compile(r'(https?://[^\s<>()«»,;]+[^\s<>()«»,;.:!?])')
BANNED_SUBJECTS = ['заметила одну вещь', 'заметила пару вещей', 'заметила кое-что', 'смотрела вашу', 'коммерческое предложение', 'предложение для']
OK_DOTS = ['Яндекс.Карт', 'Яндекс.Дирек', 'Яндекс.Бизнес', 'Яндекс.Еда', 'Яндекс.Услуг']

def link(t):
    t = html.escape(t, quote=False)
    return URL.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', t)

def main(path):
    s = open(path, encoding='utf-8').read()
    errors = []
    where = re.search(r'\*\*Куда отправлять:\*\*\s*(.+)', s)
    subj = re.search(r'\*\*Тема:\*\*\s*(.+)', s)
    where = re.sub(r'\s*Черновик в Gmail: да\.?', '', where.group(1).replace('**', '')).strip() if where else ''
    subj = subj.group(1).strip() if subj else ''
    parts = s.split('\n---\n')
    body = parts[1].strip() if len(parts) > 1 else ''
    if not subj:
        errors.append('нет строки **Тема:**')
    if any(b in subj.lower() for b in BANNED_SUBJECTS):
        errors.append(f'шаблонная тема: «{subj}». Вынеси в тему главную найденную ошибку')
    if not body:
        errors.append('не найден текст письма между линиями ---')
    for bad in ['—', '→', 'utm_', '?text=', 'ysclid', 'zoon.ru/redirect', 'google.com/url']:
        if bad in body or bad in subj:
            errors.append(f'запрещённое в тексте: {bad}')
    plain = URL.sub('ССЫЛКА', body)
    for ok in OK_DOTS:
        plain = plain.replace(ok, ok.replace('.', '_'))
    for m in re.finditer(r'[а-яёa-z0-9»)][.!?][А-ЯЁA-Z«]', plain):
        errors.append(f'нет пробела после точки: «{plain[max(0,m.start()-15):m.end()+15]}»')
    paras = [' '.join(x.split('\n')).strip() for x in body.split('\n\n') if x.strip()]
    # подпись: строки подписи оставляем отдельными строками
    out = []
    for p in body.split('\n\n'):
        lines = [l.strip() for l in p.strip().split('\n') if l.strip()]
        if not lines:
            continue
        sig = len(lines) > 1 and all(len(l) < 70 for l in lines)
        out.append('<br>'.join(link(l) + ' ' for l in lines) if sig else link(' '.join(lines)) + ' ')
    head = ('<b>Куда отправить:</b> ' + link(where) + ' <br>-----<br><br>') if where else ''
    html_body = head + '<br><br>'.join(out)
    if '<p' in html_body:
        errors.append('в htmlBody не должно быть <p>')
    text_body = (('Куда отправить: ' + where + '\n-----\n\n') if where else '') + '\n\n'.join(
        '\n'.join(l.strip() for l in p.strip().split('\n') if l.strip()) for p in body.split('\n\n') if p.strip())
    print(json.dumps({'subject': subj, 'htmlBody': html_body, 'body': text_body, 'errors': errors}, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(sys.argv[1])
