"""
One-time Google OAuth bootstrap for Hermes — run LOCALLY (where a browser opens).

    pip install -r requirements-google.txt
    python google_setup.py            # uses GOOGLE_OAUTH_CLIENT_ID/SECRET from env
    #   or: python google_setup.py path/to/client_secret.json

You consent once per Google account; it prints a **refresh token** to paste into
Railway as a variable (the agent builds credentials from client id/secret +
refresh token at runtime — no token files to ship). Repeat per account.

Scopes are intentionally broad ("full access") — see docs/GOOGLE.md for the
verification/Internal-app caveats that broad scopes imply.
"""
import json
import os
import sys

# Broad Google Workspace access. Trim in docs/GOOGLE.md if you want less.
SCOPES = [
    "https://mail.google.com/",                                # Gmail: full (read/send/modify/delete)
    "https://www.googleapis.com/auth/calendar",                # Calendar: full
    "https://www.googleapis.com/auth/drive",                   # Drive: full
    "https://www.googleapis.com/auth/documents",               # Docs
    "https://www.googleapis.com/auth/spreadsheets",            # Sheets
    "https://www.googleapis.com/auth/presentations",           # Slides
    "https://www.googleapis.com/auth/forms.body",              # Forms
    "https://www.googleapis.com/auth/contacts",                # Contacts (People API)
    "https://www.googleapis.com/auth/tasks",                   # Tasks
    "https://www.googleapis.com/auth/userinfo.email",          # who am I
    "openid",
]


def main() -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    if len(sys.argv) > 1:                      # client_secret.json path given
        flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    else:                                      # build client config from env
        cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        csec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        if not (cid and csec):
            sys.exit(
                "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET, or pass a "
                "client_secret.json path. See docs/GOOGLE.md."
            )
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": cid,
                    "client_secret": csec,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            },
            SCOPES,
        )

    # access_type=offline + prompt=consent guarantees a refresh token every run.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    email = "unknown"
    try:
        info = build("oauth2", "v2", credentials=creds).userinfo().get().execute()
        email = info.get("email", "unknown")
    except Exception:
        pass

    if not creds.refresh_token:
        sys.exit("No refresh token returned — revoke the app's access and re-run.")

    label = email.split("@")[0].upper().replace(".", "_").replace("-", "_")
    print("\n" + "=" * 64)
    print(f"Authorized: {email}")
    print("Set these in Railway (Variables tab) for the hermes-agent service:")
    print(f"  GOOGLE_REFRESH_TOKEN_{label} = {creds.refresh_token}")
    print("(and GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET once, shared by all accounts)")
    print("=" * 64)

    os.makedirs("tokens", exist_ok=True)
    out = os.path.join("tokens", f"google-{email}.json")
    with open(out, "w") as f:
        json.dump(
            {"email": email, "refresh_token": creds.refresh_token, "scopes": SCOPES}, f, indent=2
        )
    print(f"Also saved locally (gitignored): {out}")


if __name__ == "__main__":
    main()
