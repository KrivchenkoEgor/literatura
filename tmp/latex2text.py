# -*- coding: utf-8 -*-
"""Конвертер LaTeX-формул в обычный текст (Unicode) для MD-баз знаний."""
import re, sys, pathlib

SUP = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','-':'⁻','+':'⁺'}

def find_arg(s, i):
    """Прочитать аргумент {…} с балансировкой скобок, начиная с s[i]=='{'."""
    assert s[i] == '{'
    depth, j = 0, i
    while j < len(s):
        if s[j] == '{': depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0: return s[i+1:j], j+1
        j += 1
    raise ValueError('unbalanced braces: ' + s)

def needs_paren(x):
    y = x.strip()
    return bool(re.search(r'[+−\-±]', y))

def resolve_fracs(s):
    while '\\frac' in s:
        m = re.search(r'\\frac', s)
        i = m.end()
        while i < len(s) and s[i] == ' ': i += 1
        num, i2 = find_arg(s, i)
        while i2 < len(s) and s[i2] == ' ': i2 += 1
        den, i3 = find_arg(s, i2)
        num = resolve_fracs(num); den = resolve_fracs(den)
        d = '(' + den + ')' if needs_paren(den) else den
        n = '(' + num + ')' if (needs_paren(num) or '/' in num) else num
        s = s[:m.start()] + n + '/' + d + s[i3:]
    return s

def sup_sub(s):
    def sub_brace(m):
        inner = m.group(1)
        return '_' + (inner if re.fullmatch(r'\w{1,2}|[а-яёА-ЯЁ]{1,3}', inner) else inner)
    s = re.sub(r'_\{([^{}]*)\}', sub_brace, s)
    def sup_brace(m):
        inner = m.group(1)
        if re.fullmatch(r'[-+0-9]+', inner):
            return ''.join(SUP[c] for c in inner)
        return '^' + inner
    s = re.sub(r'\^\{([^{}]*)\}', sup_brace, s)
    s = re.sub(r'\^(\d)', lambda m: SUP[m.group(1)], s)
    s = re.sub(r'_\^?(\d)', r'_\1', s)  # F_1 остаётся F_1
    return s

def convert_math(s):
    s = s.replace('\\!', '').replace('\\%', '%')
    s = resolve_fracs(s)
    s = re.sub(r'\\text\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\vec\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\(?:hat|tilde)\{([^{}]*)\}', r'\1', s)
    s = sup_sub(s)
    s = s.replace('\\Delta', 'Δ').replace('\\rho', 'ρ').replace('\\eta', 'η')
    s = s.replace('\\alpha', 'α').replace('\\beta', 'β').replace('\\gamma', 'γ')
    s = s.replace('\\cdot', '·').replace('\\times', '×').replace('\\pm', '±')
    s = s.replace('\\sim', '~').replace('\\approx', '≈').replace('\\le', '≤').replace('\\ge', '≥')
    s = s.replace('\\qquad', ' ').replace('\\quad', ' ')
    s = s.replace('\\left', '').replace('\\right', '')
    s = s.replace('\\,', ' ').replace('\\ ', ' ').replace(';', '; ').replace('\\;', ' ')
    s = re.sub(r'\{,\}', ',', s)          # 0{,}5 -> 0,5
    s = re.sub(r'[ ]{2,}', ' ', s)
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\s+([.,;:])', r'\1', s)  # пробел перед знаком препинания
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.replace('  ', ' ')
    return s

def convert_line(line):
    # не трогаем строки-заголовки ключевых слов? нет — там тоже надо чистить
    def rep_display(m): return convert_math(m.group(1))
    def rep_inline(m): return convert_math(m.group(1))
    line = re.sub(r'\$\$(.+?)\$\$', rep_display, line)
    line = re.sub(r'\$([^$]+?)\$', rep_inline, line)
    return line

changed, files_changed = 0, 0
for d in sys.argv[1:]:
    for p in sorted(pathlib.Path(d).glob('*.md')):
        src = p.read_text(encoding='utf-8')
        out_lines = []
        n = 0
        for ln in src.split('\n'):
            if '$' in ln:
                new = convert_line(ln)
                if new != ln: n += 1
                out_lines.append(new)
            else:
                out_lines.append(ln)
        if n:
            p.write_text('\n'.join(out_lines), encoding='utf-8')
            files_changed += 1; changed += n
            print(f'{p}: {n} строк')
print(f'ИТОГО: {files_changed} файлов, {changed} строк')
