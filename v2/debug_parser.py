import pdfplumber, re

t = ''
with pdfplumber.open('regulamin.pdf') as pdf:
    for i, s in enumerate(pdf.pages):
        if i < 2:
            continue
        x = s.extract_text()
        if x:
            t += x + '\n'

t = re.sub(r'Strona \d+ z \d+', '', t)
l = t.split('\n')
l = [x for x in l if not re.match(r'^[\s.\d]+$', x)]
t = '\n'.join(l)
t = re.sub(r'[ \t]+', ' ', t)
t = re.sub(r'\n{3,}', '\n\n', t)

idx = t.find('§ 34. Wznowienia')
print("Znak przed §34:", repr(t[idx-3:idx+50]))

koniec = t.find('\n§', idx+1)
print("Długość sekcji §34:", len(t[idx:koniec]))
print("Pierwsze 200 znaków §34:")
print(t[idx:idx+200])
