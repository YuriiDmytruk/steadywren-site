// Steadywren site: smart product search (3-letter grams), contact dialog and form submit. No dependencies.

/** Lower-case, strip accents, keep letters and digits only. */
function normalize(text) {
    return text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
}

/** grams("flippa") -> fli, lip, ipp, ppa (n = 3). Words shorter than n stay whole (matched as a prefix). */
function grams(word, n = 3) {
    if (word.length < n) return [word];
    const out = [];
    for (let i = 0; i + n <= word.length; i++) out.push(word.slice(i, i + n));
    return out;
}

/** Search index entry: the 3-grams of each field with a weight (title counts most). */
function indexItem(item) {
    const fields = [[item.title, 3], [item.keywords || '', 2], [item.description, 1]];
    return fields.map(([text, weight]) => {
        const words = normalize(text).split(' ').filter(Boolean);
        return {
            weight, text: normalize(text), words,
            grams: { 3: new Set(words.flatMap((w) => grams(w, 3))), 2: new Set(words.flatMap((w) => grams(w, 2))) },
        };
    });
}

/**
 * Score 0..1: the share of the query's 3-grams found in the item, each counted at the weight of the best field
 * that has it. Typos and partial words still match ("flipa" finds "Flippa": fli + lip of 3 grams).
 */
function score(query, fields, n = 3) {
    const words = normalize(query).split(' ').filter(Boolean);
    if (!words.length) return 1;
    const qGrams = words.flatMap((w) => grams(w, n));
    let total = 0;
    for (const g of qGrams) {
        let best = 0;
        for (const f of fields) {
            const hit = g.length < n ? f.words.some((w) => w.startsWith(g)) : f.grams[n].has(g);
            if (hit) best = Math.max(best, f.weight);
        }
        total += best / 3;
    }
    let result = total / qGrams.length;
    if (fields.some((f) => f.text.includes(normalize(query)))) result = Math.min(1, result + 0.25); // exact phrase
    return result;
}

const MIN_SCORE = 0.34; // about a third of the query's grams must match

function setupSearch() {
    const input = document.getElementById('search');
    const indexEl = document.getElementById('search-index');
    if (!input || !indexEl) return;
    const items = JSON.parse(indexEl.textContent).map(indexItem);
    const list = document.getElementById('results');
    const cards = [...list.children];
    const count = document.getElementById('search-count');
    const empty = document.getElementById('no-results');

    function rank(q, n) {
        return cards
            .map((card, i) => ({ card, s: score(q, items[i], n), i }))
            .filter((r) => r.s >= MIN_SCORE)
            .sort((a, b) => b.s - a.s || a.i - b.i);
    }

    function run() {
        const q = input.value;
        // 3-letter grams first; letter pairs only when nothing matched (catches swapped letters: "reveiws").
        let ranked = rank(q, 3);
        if (!ranked.length) ranked = rank(q, 2);
        cards.forEach((c) => { c.hidden = true; });
        ranked.forEach((r) => { r.card.hidden = false; list.appendChild(r.card); });
        count.textContent = `${ranked.length} product${ranked.length === 1 ? '' : 's'}`;
        empty.hidden = ranked.length > 0;
    }
    input.addEventListener('input', run);
    const q = new URLSearchParams(location.search).get('q');
    if (q) { input.value = q; run(); }
}

function setupContact() {
    const dialog = document.getElementById('contact');
    const form = document.getElementById('contact-form');
    if (!dialog || !form) return;
    const status = form.querySelector('.status');
    document.querySelectorAll('[data-contact]').forEach((b) => b.addEventListener('click', () => {
        status.textContent = '';
        dialog.showModal();
    }));
    form.querySelector('[data-close]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); }); // backdrop

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const data = new FormData(form);
        const payload = {
            email: data.get('email'),
            message: data.get('message'),
            topics: data.get('topic') ? [data.get('topic')] : [], // one badge per message
            website: data.get('website'), // honeypot: real people leave it empty
            page: location.pathname,
        };
        const button = form.querySelector('[type=submit]');
        button.disabled = true;
        status.textContent = 'Sending…';
        try {
            const response = await fetch(form.dataset.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            status.textContent = 'Thanks! Your message is on its way - I will reply to your email.';
            form.reset();
        } catch {
            // The form endpoint is unreachable: hand the message to the visitor's mail app instead.
            const subject = `Project idea${payload.topics.length ? ` (${payload.topics.join(', ')})` : ''}`;
            const body = `${payload.message}\n\nReply to: ${payload.email}`;
            location.href = `mailto:${form.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
            status.textContent = `Opening your mail app… If nothing happens, write to ${form.dataset.email}.`;
        } finally {
            button.disabled = false;
        }
    });
}

if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        setupSearch();
        setupContact();
    });
}

if (typeof module !== 'undefined') module.exports = { normalize, grams, score, indexItem, MIN_SCORE };
