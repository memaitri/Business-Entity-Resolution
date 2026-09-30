import re

_non_word = re.compile(r'[^\w\s]', re.UNICODE)
_ws = re.compile(r'\s+')
LEGAL_SUFFIXES = {
    'inc','incorporated','llc','ltd','limited','corp','corporation','co','company',
    'pvt','private','pllc','llp','plc','lp','gmbh','sarl','sa','pc','group','holdings',
    'the','and','of'
}
ADDR_STOPWORDS = {
    'street','st','road','rd','avenue','ave','drive','dr','lane','ln','blvd','boulevard',
    'suite','ste','floor','fl','unit','apt','apartment','building','bldg',
    'north','south','east','west','n','s','e','w','ne','nw','se','sw',
    'the','and','of','no','p','o','box'
}

def normalize_text(s):
    s = s.lower().strip()
    s = _non_word.sub(' ', s)
    s = _ws.sub(' ', s).strip()
    return s

def norm_name_key(name):
    n = normalize_text(name)
    toks = [t for t in n.split() if t not in LEGAL_SUFFIXES]
    if not toks:
        toks = n.split()
    return ' '.join(sorted(toks))

def extract_zip(addr):
    digits = re.findall(r'\d{4,}', addr)
    return max(digits, key=len) if digits else ''

def addr_tokens(addr):
    n = normalize_text(addr)
    toks = set()
    for t in n.split():
        if t.isdigit():
            continue
        if len(t) < 3:
            continue
        if t in ADDR_STOPWORDS:
            continue
        toks.add(t)
    return toks
