// Cloudflare Worker entry: the steadywren.com contact form endpoint (POST https://api.steadywren.com/contact).
import { EmailMessage } from 'cloudflare:email';
import { handle } from './handler.js';

export default {
    async fetch(request, env) {
        return handle(request, env, (from, to, raw) => env.CONTACT_EMAIL.send(new EmailMessage(from, to, raw)));
    },
};
