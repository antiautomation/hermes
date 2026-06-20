# Google access for Hermes

Goal: give Hermes broad ("full") access to your Google account(s) — Gmail,
Calendar, Drive, Docs, Sheets, Slides, Forms, Contacts, Tasks — via one OAuth
client and per-account consent. Writes that are irreversible (sending mail,
deleting Drive files) stay behind the Telegram `/approve` gate per the project's
hard rules; the OAuth grant is broad, the agent's *acting* surface is gated.

## One-time setup (you do this in Google Cloud Console)

1. **Create / pick a project** at <https://console.cloud.google.com>.
2. **Enable the APIs** (APIs & Services → Enable APIs): Gmail, Google Calendar,
   Google Drive, Google Docs, Google Sheets, Google Slides, Google Forms,
   People (Contacts), Google Tasks.
3. **OAuth consent screen:**
   - **Workspace org account** → set **User type: Internal**. Internal apps skip
     Google's verification review and can use restricted scopes (Gmail/Drive)
     with long-lived refresh tokens. This is the path you want for full access.
   - **Personal @gmail.com** → User type **External**, app stays in **Testing**,
     add yourself as a **Test user**. Restricted-scope refresh tokens issued in
     Testing **expire after 7 days** — fine to start, but for an always-on bot
     you'd eventually submit the app for verification (privacy policy + review).
4. **Create credentials → OAuth client ID → Application type: Desktop app.**
   Copy the **Client ID** and **Client secret**.

## Mint a refresh token (per account)

Run locally on your Mac (a browser opens):

```bash
cd hermes/agent
pip install -r requirements-google.txt
export GOOGLE_OAUTH_CLIENT_ID=...     # from step 4
export GOOGLE_OAUTH_CLIENT_SECRET=...
python google_setup.py                 # consent in the browser
```

It prints a `GOOGLE_REFRESH_TOKEN_<ACCOUNT>` line. Repeat for each Google account
you want Hermes to reach.

## Put the secrets on Railway

Set on the **hermes-agent** service (Variables tab, or ask me to set them):

- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` (shared by all accounts)
- one `GOOGLE_REFRESH_TOKEN_<ACCOUNT>` per account

The agent rebuilds credentials from `client_id + client_secret + refresh_token`
at runtime — no token files are shipped or committed.

## Scopes requested (broad by design)

| API | Scope | Access |
|---|---|---|
| Gmail | `https://mail.google.com/` | full (read/send/modify/delete) |
| Calendar | `…/auth/calendar` | full |
| Drive | `…/auth/drive` | full |
| Docs | `…/auth/documents` | read/write |
| Sheets | `…/auth/spreadsheets` | read/write |
| Slides | `…/auth/presentations` | read/write |
| Forms | `…/auth/forms.body` | read/write |
| Contacts | `…/auth/contacts` | read/write |
| Tasks | `…/auth/tasks` | read/write |
| Identity | `…/auth/userinfo.email`, `openid` | who-am-I |

> `https://mail.google.com/` and `…/auth/drive` are **restricted scopes**. With an
> **Internal** Workspace app they just work; with an **External** app in Testing
> they work for test users with the 7-day refresh-token caveat above. Edit the
> `SCOPES` list in `agent/google_setup.py` to narrow if you want less than full.
