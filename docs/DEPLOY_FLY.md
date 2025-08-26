### Deploy the GitHub App on Fly.io

This repo includes a minimal Probot server at `github-app/` and a Fly config at `fly.toml`.

#### 1) Prereqs

- Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
- Log in: `fly auth login`
- Have a GitHub App created (Settings → Developer settings → GitHub Apps)
  - Get: `APP_ID`, `WEBHOOK_SECRET`, and download the private key `.pem` file

#### 2) Create/confirm the Fly app

- Option A (use provided fly.toml):
  - Edit `app = "ci-auto-rescue-github-app"` in `fly.toml` to a unique name
  - Create the app: `fly apps create <your-unique-app-name>`
- Option B (let Fly generate):
  - `fly launch --no-deploy --copy-config` and confirm the app name

#### 3) Set secrets (required)

Use your real values. For the private key, pass it from the file so multiline PEM is handled correctly.

```bash
flyctl secrets set APP_ID=<your-app-id> WEBHOOK_SECRET=<your-webhook-secret>
flyctl secrets set PRIVATE_KEY="$(cat /absolute/path/to/your-private-key.pem)"
```

#### 4) Deploy

```bash
flyctl deploy
```

#### 5) Configure GitHub App webhook URL

- Set the Webhook URL to: `https://<your-unique-app-name>.fly.dev/api/github/webhooks`
  - Probot’s default webhook path is `/api/github/webhooks`.

#### 6) Install the App on repos

- Share the App's Install link (from your GitHub App settings)
- Users click Install → pick repositories → done

#### Notes

- The server listens on port 8080 internally (see `github-app/index.js` and `fly.toml`).
- Required env vars: `APP_ID`, `PRIVATE_KEY`, `WEBHOOK_SECRET`.
- To update: modify code, then `fly deploy` again.
