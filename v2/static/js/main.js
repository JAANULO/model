const chatEl= document.getElementById('chat');
    const inputEl = document.getElementById('input');
    const btnEl = document.getElementById('btn');

    // Obsługa motywu jasny/ciemny
    const THEME_KEY = 'pwr_chat_theme';
    function ladujMotyw() {
      if (localStorage.getItem(THEME_KEY) === 'light') {
        document.body.classList.add('light-theme');
      }
    }
    function przelaczMotyw() {
      document.body.classList.toggle('light-theme');
      const isLight = document.body.classList.contains('light-theme');
      localStorage.setItem(THEME_KEY, isLight ? 'light' : 'dark');
    }
    // Zarządzanie bazami zrodlowymi
    let aktywneZrodla = new Set(['Wszystkie dokumenty']);
    let wybraneZrodloIndywidualne = null;

    ladujMotyw();

    // pamięć kontekstu – ostatni paragraf i pytanie
    let ostatniKontekstTytul = null;
    let ostatniKontekstPytanie = null;

    // Przywróć historię po odświeżeniu strony (Przeniesiono do pamięci trwalszej)
    const HISTORIA_KEY = 'pwr_chat_historia';
    function zapiszHistorie(pytanie, odpowiedz) {
      const hist = JSON.parse(localStorage.getItem(HISTORIA_KEY) || '[]');
      hist.push({ pytanie, odpowiedz, czas: new Date().toLocaleTimeString() });
      if (hist.length > 20) hist.shift(); // max 20 wpisów
      localStorage.setItem(HISTORIA_KEY, JSON.stringify(hist));
    }
    function wczytajHistorie() {
      const hist = JSON.parse(localStorage.getItem(HISTORIA_KEY) || '[]');
      if (hist.length === 0) return;

      ukryjWitajke();
      hist.forEach(({ pytanie, odpowiedz, czas }) => {
        dodajWiadomoscUzytkownika(pytanie, czas);
        // uproszczone odtworzenie — tylko tekst
        const wrap = document.createElement('div');
        wrap.className = 'message-wrap';
        wrap.dataset.ts = czas || new Date().toLocaleString('pl-PL');
        wrap.innerHTML = `<div class="msg-bot"><div class="bot-avatar"><img src="/static/logo.png" alt="Logo"></div>
        <div class="bot-content"><div class="bubble">${escHtml(odpowiedz)}</div></div></div>`;
        chatEl.appendChild(wrap);
      });
      scrollDol();
    }
    window.addEventListener('load', wczytajHistorie);

    // auto-resize textarea
    inputEl.addEventListener('input', () => {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
      const len = inputEl.value.length;
      const hint = document.getElementById('hint');
      if (len > 200) {
        hint.textContent = `⚠ Za długie pytanie (${len}/200)`;
        hint.style.color = 'var(--danger)';
      } else {
        hint.textContent = 'Enter – wyślij · Shift+Enter – nowa linia';
        hint.style.color = '';
      }
    });

    // Enter wyślij, Shift+Enter nowa linia
    inputEl.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        wyslij();
      }
    });

    function zadaj(chip) {
      inputEl.value = chip.textContent;
      wyslij();
    }

    function ukryjWitajke() {
      const w = document.getElementById('welcome');
      if (w) w.remove();
    }

    function dodajWiadomoscUzytkownika(tekst, znacznikCzasu = null) {
      ukryjWitajke();
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      wrap.dataset.ts = znacznikCzasu || new Date().toLocaleString('pl-PL');
      wrap.innerHTML = `
      <div class="msg-user">
        <div class="bubble">${escHtml(tekst)}</div>
      </div>`;
      chatEl.appendChild(wrap);
      scrollDol();
    }

    function pokazTyping() {
      const el = document.createElement('div');
      el.className = 'typing-wrap';
      el.id = 'typing';
      el.innerHTML = `
      <div class="typing">
        <div class="bot-avatar"><img src="/static/logo.png" alt="Logo"></div>
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
        <div class="typing-text">Szukam informacji...</div>
      </div>`;
      chatEl.appendChild(el);
      scrollDol();
    }

    function ukryjTyping() {
      const el = document.getElementById('typing');
      if (el) el.remove();
    }

    function renderujOdpowiedz(dane) {
      if (dane.punkty) {
        const punktyHtml = dane.punkty.map(item => '<li>' + escHtml(item) + '</li>').join('');
        const zachetaHtml = dane.zacheta
          ? '<div class="odp-zacheta">💡 ' + escHtml(dane.zacheta) + '</div>'
          : '';
        return '<div class="odp-wstep">' + escHtml(dane.wstep) + '</div>' +
          '<ul class="odp-punkty">' + punktyHtml + '</ul>' +
          zachetaHtml;
      }
      return '<div>' + escHtml(dane.odpowiedz || '') + '</div>';
    }

    function rozwinTresc(btn) {
      const div = btn.nextElementSibling;
      div.hidden = !div.hidden;
      btn.textContent = div.hidden ? '▼ pokaż pełny paragraf' : '▲ zwiń';
    }

    async function kopiujOdpowiedz(btn) {
      try {
        const tekstData = btn.getAttribute('data-copy');
        await navigator.clipboard.writeText(tekstData);
        const oldHtml = btn.innerHTML;
        btn.innerHTML = '✓';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.innerHTML = oldHtml;
          btn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        console.error('Nie udało się skopiować', err);
      }
    }
    function dodajOdpowiedzBota(dane) {
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      wrap.dataset.ts = new Date().toLocaleString('pl-PL');
      const pct = Math.round((dane.podobienstwo || 0) * 100);
      const pct2 = Math.round((dane.podobienstwo2 || 0) * 100);
      let sourcesHtml = '';
      if (dane.tytul) {
        sourcesHtml += '<div class="source-tag">' +
          '<span class="dot"></span>' +
          '<span class="title-text">' + escHtml(dane.tytul) + '</span>' +
          '</div>';
      }
      if (dane.tytul2) {
        sourcesHtml += '<div class="source-tag">' +
          '<span class="dot secondary"></span>' +
          '<span class="title-text">' + escHtml(dane.tytul2) + '</span>' +
          '</div>';
      }
      let barsHtml = '';
      if (dane.tytul) {
        barsHtml += '<div class="sim-row">' +
          '<span class="sim-label">dopasowanie</span>' +
          '<div class="sim-track"><div class="sim-fill" data-pct="' + pct + '"></div></div>' +
          '<span class="sim-pct">' + pct + '%</span>' +
          '</div>';
      }
      if (dane.tytul2) {
        barsHtml += '<div class="sim-row">' +
          '<span class="sim-label">powiązany</span>' +
          '<div class="sim-track"><div class="sim-fill secondary" data-pct="' + pct2 + '"></div></div>' +
          '<span class="sim-pct secondary">' + pct2 + '%</span>' +
          '</div>';
      }
      // Przygotowanie czystego tekstu do schowka bez wciągania markerów oraz HTML-owych tagów
      let czystyKopiowanyTekst = dane.wstep || dane.odpowiedz || '';
      if (dane.punkty && dane.punkty.length > 0) {
        czystyKopiowanyTekst += '\n' + dane.punkty.map(p => '- ' + p).join('\n');
      }

      const skrzyneczkacopyHtml = escHtml(czystyKopiowanyTekst);

      // Zgodnie z decyzją projektową rezygnujemy z powiązań przy odpowiadaniu przez bota
      let sformatowanaPelnaTresc = escHtml(dane.pelna_tresc || '');
      if (dane.najlepsze_zdanie && sformatowanaPelnaTresc) {
        const czysteNajlepszeZdanie = escHtml(dane.najlepsze_zdanie);
        if (sformatowanaPelnaTresc.includes(czysteNajlepszeZdanie)) {
          sformatowanaPelnaTresc = sformatowanaPelnaTresc.replace(
            czysteNajlepszeZdanie,
            '<mark class="highlight-zdanie">' + czysteNajlepszeZdanie + '</mark>'
          );
        }
      }

      // Optymalizacja UX: złamania html & Markowanie (Highlight) Wyrazów kluczowych
      let sformatowanaZlamanaTresc = sformatowanaPelnaTresc.replace(/\n+/g, '<br><br>');
      if (dane.slowa_kluczowe && dane.slowa_kluczowe.length > 0) {
        dane.slowa_kluczowe.forEach(slowo => {
          if (slowo.length >= 3) {
            const regex = new RegExp(`(${slowo})`, 'gi');
            sformatowanaZlamanaTresc = sformatowanaZlamanaTresc.replace(regex, '<mark class="highlight-zdanie" style="background-color: var(--accent); color: #000;">$1</mark>');
          }
        });
      }

      const natychmiastowyParagraf = dane.pelna_tresc
        ? '<div style="margin-top: 8px;"><button class="btn-rozwin" onclick="rozwinTresc(this)">▼ pokaż pełny paragraf</button>' +
        '<div class="pelna-tresc" style="display: none; line-height: 1.5; font-size: 0.9em; margin-top: 8px;">' +
        sformatowanaZlamanaTresc + '</div></div>'
        : '';

      wrap.innerHTML = '<div class="msg-bot">' +

        '<div class="bot-avatar"><img src="/static/logo.png" alt="Logo"></div>' +
        '<div class="bot-content">' +
        '<div class="bubble type-target"></div>' + // Pusta bańka na efekt literowania
        natychmiastowyParagraf + // Wrzutka paragrafu natężona na stałe do DOM, odporna na pętle
        (sourcesHtml ? '<div class="source-row" style="opacity:0">' + sourcesHtml + '</div>' : '') +
        '<div style="opacity:0">' + barsHtml + '</div>' + // Paski statystyk
        '<div class="feedback-row" style="opacity:0">' +
        '<button class="btn-feedback" data-ocena="1" onclick="wyslijFeedback(this)">👍</button>' +
        '<button class="btn-feedback" data-ocena="-1" onclick="wyslijFeedback(this)">👎</button>' +
        '<button class="btn-copy" onclick="kopiujOdpowiedz(this)" data-copy="' + skrzyneczkacopyHtml + '" data-tooltip="Skopiuj odpowiedź">📋</button>' +
        '</div>' +
        '</div>' +
        '</div>';
      if (dane.pytanie_id) {
        wrap.querySelectorAll('.btn-feedback').forEach(btn => {
          btn.dataset.pid = dane.pytanie_id;
        });
      }
      chatEl.appendChild(wrap);
      scrollDol();
      // === Animacja Maszyny piszącej (Typewriter) ===
      const docelowyHtml = renderujOdpowiedz(dane);
      const targetBubble = wrap.querySelector('.type-target');
      let stalyHtml = '';
      let kursorWTagu = false;
      let zapamietywanyTag = '';
      let i = 0;
      function streamujZnak() {
        if (i >= docelowyHtml.length) {
          targetBubble.innerHTML = docelowyHtml;
          wrap.querySelectorAll('[style*="opacity"]').forEach(el => {
            el.style.opacity = '1';
            el.style.transition = 'opacity 0.6s ease';
          });
          requestAnimationFrame(() => {
            wrap.querySelectorAll('.sim-fill').forEach(bar => {
              setTimeout(() => { bar.style.width = bar.dataset.pct + '%'; }, 100);
            });
          });
          scrollDol();
          return;
        }
        const litera = docelowyHtml[i];
        if (litera === '<') kursorWTagu = true;
        if (kursorWTagu) {
          zapamietywanyTag += litera;
          if (litera === '>') {
            kursorWTagu = false;
            stalyHtml += zapamietywanyTag;
            zapamietywanyTag = '';
          }
        } else {
          stalyHtml += litera;
          targetBubble.innerHTML = stalyHtml;
          // Zapobiega gubieniu ostrości podczas czytania
          if (i % 10 === 0) scrollDol();
        }

        i++;
        // Zatrzymujemy się na 5 minimilisekund po znakach w słowach, i unikamy zacięcia w kodowaniu DOM
        setTimeout(streamujZnak, kursorWTagu ? 0 : 5);
      }

      // Odpal magię
      streamujZnak();
    }
    async function wyslij() {
      const tekst = inputEl.value.trim();
      if (tekst.length < 3) {
        const hint = document.getElementById('hint');
        hint.textContent = '⚠ Twoje pytanie jest za krótkie!';
        hint.style.color = 'var(--danger)';
        setTimeout(() => {
          hint.textContent = 'Enter – wyślij · Shift+Enter – nowa linia';
          hint.style.color = '';
        }, 3000);
        return;
      }
      inputEl.value = '';
      inputEl.style.height = 'auto';
      btnEl.disabled = true;

      dodajWiadomoscUzytkownika(tekst);
      pokazTyping();

      try {
        let aktZrodlo = wybraneZrodloIndywidualne || "Wszystkie dokumenty";
        if (aktZrodlo === "odlacz") {
          ukryjTyping();
          dodajOdpowiedzBota({ odpowiedz: "Baza wiedzy jest odłączona. Podłącz ją w opcjach.", tytul: null, podobienstwo: 0 });
          btnEl.disabled = false;
          return;
        }
        const res = await fetch('/zapytaj', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pytanie: tekst,
            zrodlo: aktZrodlo,
            kontekst_tytul: ostatniKontekstTytul,
            kontekst_pytanie: ostatniKontekstPytanie,
          }),
        });


        const dane = await res.json();
        ukryjTyping();

        if (dane.disambiguation) {
          let opcjeHtml = '';
          dane.opcje.forEach(opcja => {
            opcjeHtml += `<button class="btn-chip" onclick="zadaj(this)">${escHtml(opcja)}</button>`;
          });
          const disambigHtml = `<div style="margin-bottom: 8px;">${escHtml(dane.komunikat)}</div><div class="chips-container" style="flex-wrap: wrap;">${opcjeHtml}</div>`;

          const wrap = document.createElement('div');
          wrap.className = 'message-wrap';
          wrap.dataset.ts = new Date().toLocaleString('pl-PL');
          wrap.innerHTML = `<div class="msg-bot"><div class="bot-avatar"><img src="/static/logo.png" alt="Logo"></div><div class="bot-content"><div class="bubble">${disambigHtml}</div></div></div>`;
          chatEl.appendChild(wrap);
          scrollDol();
          zapiszHistorie(tekst, dane.komunikat);
          return;
        }

        dodajOdpowiedzBota(dane);

        // zapamiętaj kontekst dla następnego pytania
        if (dane.kontekst_tytul) {
          ostatniKontekstTytul = dane.kontekst_tytul;
          ostatniKontekstPytanie = tekst;
        }
      } catch (err) {
        ukryjTyping();
        dodajOdpowiedzBota({
          odpowiedz: '⚠ Serwer niedostępny. Odśwież stronę lub spróbuj za chwilę.',
          tytul: null,
          podobienstwo: 0,
        });
      } finally {
        btnEl.disabled = false;
        inputEl.focus();
      }
    }

    async function wyslijFeedback(btn) {
      const pid = btn.dataset.pid;
      const ocena = parseInt(btn.dataset.ocena);
      if (!pid) return;
      btn.closest('.feedback-row').innerHTML =
        ocena === 1 ? '<span style="color:var(--accent)">Dzięki! ✓</span>'
          : '<span style="color:var(--muted)">Zapisano, poprawimy ✓</span>';
      await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pytanie_id: parseInt(pid), ocena })
      });
    }

    function scrollDol() {
      chatEl.scrollTop = chatEl.scrollHeight;
    }

    // Obsługa przycisku "Wróć w dół"
    const btnScrollDown = document.getElementById('btn-scroll-down');
    if (btnScrollDown) {
      chatEl.addEventListener('scroll', () => {
        // Pokaż guzik, jeśli użytkownik podjechał więcej niż 150px od spodu do góry
        if (chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight > 150) {
          btnScrollDown.classList.add('show');
        } else {
          btnScrollDown.classList.remove('show');
        }
      });
    }

    function wyczyscChat() {
      sessionStorage.removeItem(HISTORIA_KEY);
      ostatniKontekstTytul = null;
      ostatniKontekstPytanie = null;
      chatEl.innerHTML = `<div class="welcome" id="welcome">
      <div class="big">Zapytaj o <span>regulamin</span></div>
      <p>Przeszukuję regulamin studiów PWr i zwracam właściwy paragraf wraz ze źródłem.</p>
      <div class="chips">
        <div class="chip" onclick="zadaj(this)">ile razy można podejść do egzaminu?</div>
        <div class="chip" onclick="zadaj(this)">kiedy można wziąć urlop dziekański?</div>
        <div class="chip" onclick="zadaj(this)">co grozi za nieobecności?</div>
        <div class="chip" onclick="zadaj(this)">jak wznowić studia po skreśleniu?</div>
        <div class="chip" onclick="zadaj(this)">jak oblicza się średnią ocen?</div>
      </div></div>`;
    }

    function escHtml(s) {
      return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    async function pokazBazeWiedzy() {
      const infoDiv = document.getElementById('infoBazaWidzy');
      if (infoDiv.style.display === 'block') {
        infoDiv.style.display = 'none';
        return;
      }
      infoDiv.style.display = 'block';
      infoDiv.innerHTML = '<div style="color:var(--accent);font-size:12px;padding:10px;">🔍 Przeszukiwanie dysku...</div>';

      try {
        const res = await fetch('/zrodla');
        const pliki = await res.json();

        let html = '<div style="font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;font-weight:700;">📂 Zarządzanie Wiedzą</div>';

        // Opcja: Wszystkie dokumenty
        const jestWszystko = wybraneZrodloIndywidualne === null || wybraneZrodloIndywidualne === "Wszystkie dokumenty";
        html += `
          <div class="sb-toggle-row">
            <div>
              <div style="font-size:13px;color:var(--accent);font-weight:600;">📚 Wszystkie bazy (tryb zbiorczy)</div>
              <div style="font-size:10px;color:var(--muted);margin-top:2px;">Przeszukuje wszystkie dostępne pliki naraz</div>
            </div>
            <label class="sb-toggle-sw">
              <input type="checkbox" ${jestWszystko ? 'checked' : ''} onchange="przelaczTrybZbiorczy(this)">
              <span class="sb-slider"></span>
            </label>
          </div>`;

        // Poszczególne pliki
        pliki.forEach(plik => {
          if (plik === 'dane.json') return; // Ukrywamy plik techniczny 'dane'

          const aktywny = (wybraneZrodloIndywidualne === plik);
          let nazwaWyswietlana = plik.replace('.json', '.pdf');
          if (plik === 'baza_wiedzy.json') nazwaWyswietlana = 'regulamin.pdf';

          html += `
          <div class="sb-toggle-row" style="opacity: ${jestWszystko ? '0.5' : '1'}">
            <div>
              <div style="font-size:13px;color:var(--text);">📄 ${nazwaWyswietlana}</div>
              <div style="font-size:10px;color:var(--muted);margin-top:2px;">Wczytany dokument regulaminowy</div>
            </div>
            <label class="sb-toggle-sw">
              <input type="checkbox" ${aktywny && !jestWszystko ? 'checked' : ''} ${jestWszystko ? 'disabled' : ''} data-plik="${plik}" onchange="przelaczBaze(this)">
              <span class="sb-slider"></span>
            </label>
          </div>`;
        });


        html += `
        <div style="margin-top:10px;padding-top:10px;">
          <button class="btn-rozwin" style="border-color:var(--accent2);color:var(--accent2);display:block;width:100%;font-weight:700;" onclick="window.open('/graf_widok','_blank')">🌐 Otwórz mapę powiązań</button>
        </div>`;

        infoDiv.innerHTML = html;
      } catch (e) {
        infoDiv.innerHTML = '<div style="color:var(--danger);font-size:12px;">Nie udało się wczytać listy baz.</div>';
      }
    }

    function przelaczTrybZbiorczy(cb) {
      if (cb.checked) {
        wybraneZrodloIndywiduallo = null;
        wybraneZrodloIndywidualne = "Wszystkie dokumenty";
      } else {
        wybraneZrodloIndywidualne = "baza_wiedzy.json"; // fallback
      }
      pokazBazeWiedzy(); // odśwież widok
    }

    function przelaczBaze(cb) {
      if (cb.checked) {
        wybraneZrodloIndywidualne = cb.dataset.plik;
      } else {
        wybraneZrodloIndywidualne = "odlacz";
      }
      // odznacz inne checkboxy w widoku (zachowanie radia)
      const inputs = document.querySelectorAll('#infoBazaWidzy input[data-plik]');
      inputs.forEach(i => { if (i !== cb) i.checked = false; });
    }

    function otworzOpcje() {
      document.getElementById('opcjeModal').classList.add('active');
    }
    function zamknijOpcje(event) {
      if (!event || event.target === document.getElementById('opcjeModal') || event.target.className === 'btn-close') {
        document.getElementById('opcjeModal').classList.remove('active');
        document.getElementById('infoBazaWidzy').style.display = 'none';
      }
    }
    function zapiszPdf() {
      // 1. Zamknij menu opcji żeby nie wpadło do wydruku PDF
      zamknijOpcje();

      // 2. Chwytamy cały nasz box chatu
      const element = document.getElementById('chat');

      // 3. Konfigurujemy perfekcyjny zrzut HTML na wektory i Canvas
      const kolorTla = document.body.classList.contains('light-theme') ? '#f5f5f7' : '#0d0d0f';
      const opt = {
        margin: [10, 5, 10, 5],
        filename: 'rozmowa_regulamin_pwr.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: kolorTla },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };
      // 4. Transformujemy kod DOM w gotowy, czytelny PDF ze stylami CSS i UTF-8!
      html2pdf().set(opt).from(element).save();
    }

    function toggleSidebar() {
      const sidebar = document.getElementById('sidebar');
      sidebar.classList.toggle('open');
      if (sidebar.classList.contains('open')) {
        zaladujHistorie();
      }
    }

    async function zaladujHistorie() {
      const content = document.getElementById('sidebar-content');
      content.innerHTML = '<p style="padding:16px;color:var(--muted);font-size:12px;">Ładowanie historii...</p>';

      try {
        const res = await fetch('/historia');
        const dane = await res.json();

        if (dane.error) {
          content.innerHTML = '<p style="padding:16px;color:var(--danger);font-size:12px;">Błąd bazy: ' + escHtml(dane.error) + '</p>';
          return;
        }


        if (!Array.isArray(dane) || dane.length === 0) {
          content.innerHTML = '<p style="padding:16px;color:var(--muted);font-size:12px;">Brak wpisów w bazie.</p>';
          return;
        }

        content.innerHTML = dane.map(d => {
          // Zabezpieczenie apostrofów dla onclick
          const escapedValue = escHtml(d.pytanie).replace(/'/g, "\\'");
          return '<div class="sidebar-item" onclick="wybierzZHistorii(\'' + escapedValue + '\')">' + escHtml(d.pytanie) + '</div>';
        }).join('');

      } catch (err) {
        content.innerHTML = '<p style="padding:16px;color:var(--danger);font-size:12px;">Błąd pobierania historii.</p>';
      }
    }


    function wybierzZHistorii(pytanie) {
      toggleSidebar();       // Zamknij pasek
      inputEl.value = pytanie; // Wstaw treść
      wyslij();              // Przekaż od razu do bota
    }

    function walidatorZrodla() {
      const select = document.getElementById('wyborZrodla').value;
      const input = document.getElementById('input');
      const btn = document.getElementById('btn');
      if (select === "odlacz") {
        input.disabled = true;
        btn.disabled = true;
        input.placeholder = "Brak podpiętej bazy wiedzy! Wybierz źródło...";
        input.style.opacity = 0.5;
      } else {
        input.disabled = false;
        btn.disabled = false;
        input.placeholder = "Zadaj pytanie o regulamin studiów…";
        input.style.opacity = 1;
      }
    }