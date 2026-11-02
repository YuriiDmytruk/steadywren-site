// Contact form -> email. Pure logic (no Cloudflare imports) so it can be tested with plain Node.

const MAX_MESSAGE = 5000;
const EMAIL_RE = /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/;

/** CORS headers for the site's own origin(s) only. */
export function cors(origin, allowed) {
    const ok = allowed.split(',').map((s) => s.trim()).includes(origin);
    return {
        'Access-Control-Allow-Origin': ok ? origin : allowed.split(',')[0].trim(),
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        Vary: 'Origin',
    };
}

/** Validates the form payload. Returns { error } or { email, message, topics, page }. */
export function validate(body) {
    if (!body || typeof body !== 'object') return { error: 'bad request' };
    if (body.website) return { spam: true }; // honeypot filled: a bot
    const email = String(body.email || '').trim();
    const message = String(body.message || '').trim();
    const topics = Array.isArray(body.topics) ? body.topics.map(String).slice(0, 8) : [];
    if (!EMAIL_RE.test(email) || email.length > 200) return { error: 'invalid email' };
    if (message.length < 10 || message.length > MAX_MESSAGE) return { error: 'message must be 10-5000 characters' };
    return { email, message, topics, page: String(body.page || '').slice(0, 200) };
}

/** Plain-text MIME message; Reply-To is the visitor, so answering from the mail app reaches them. */
export function mime({ from, to, replyTo, subject, text, date = new Date(), id = crypto.randomUUID() }) {
    const encode = (s) => `=?UTF-8?B?${Buffer.from(s, 'utf8').toString('base64')}?=`;
    return [
        `From: Steadywren site <${from}>`,
        `To: ${to}`,
        `Reply-To: ${replyTo}`,
        `Subject: ${encode(subject)}`,
        `Date: ${date.toUTCString()}`,
        `Message-ID: <${id}@steadywren.com>`,
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: base64',
        '',
        Buffer.from(text, 'utf8').toString('base64').replace(/.{76}/g, '$&\r\n'),
    ].join('\r\n');
}

/**
 * Handles one request. `send(from, to, raw)` delivers the email (Cloudflare send_email binding in production).
 * env: FROM (address on the domain), TO (verified Email Routing destination), ALLOWED_ORIGINS.
 */
export async function handle(request, env, send) {
    const headers = cors(request.headers.get('Origin') || '', env.ALLOWED_ORIGINS);
    const reply = (status, data) => new Response(JSON.stringify(data), {
        status, headers: { ...headers, 'Content-Type': 'application/json' },
    });
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });
    if (request.method !== 'POST' || new URL(request.url).pathname !== '/contact') return reply(404, { error: 'not found' });

    let body;
    try { body = await request.json(); } catch { return reply(400, { error: 'bad request' }); }
    const form = validate(body);
    if (form.spam) return reply(200, { ok: true }); // pretend success, send nothing
    if (form.error) return reply(400, { error: form.error });

    const topics = form.topics.length ? form.topics.join(', ') : 'not specified';
    const text = `New message from the steadywren.com contact form\n\nFrom: ${form.email}\nAbout: ${topics}\n`
        + `Page: ${form.page}\n\n${form.message}\n`;
    const raw = mime({
        from: env.FROM, to: env.TO, replyTo: form.email,
        subject: `Project idea: ${topics}`, text,
    });
    try {
        await send(env.FROM, env.TO, raw);
    } catch (error) {
        console.error('send failed', error);
        return reply(502, { error: 'could not send, please email support@steadywren.com' });
    }
    return reply(200, { ok: true });
}
