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

**Option A: Manual Deploy**

```bash
flyctl deploy
```

**Option B: Automated Deploy (Recommended)**

Set up GitHub Actions for one-click deploy on every push to main:

1. Generate a Fly API token:

   ```bash
   flyctl auth token
   ```

2. Add the token as a GitHub secret:

   - Go to your repo: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `FLY_API_TOKEN`
   - Value: (paste the token from step 1)

3. The workflow is already configured in `.github/workflows/deploy.yml`

Now every push to `main` will automatically redeploy your app! 🚀

#### 5) Configure GitHub App webhook URL

- Set the Webhook URL to: `https://<your-unique-app-name>.fly.dev/api/github/webhooks`
  - Probot’s default webhook path is `/api/github/webhooks`.

#### 6) Install the App on repos

- Share the App's Install link (from your GitHub App settings)
- Users click Install → pick repositories → done

#### 7) Health Check

Your app includes a health check endpoint at `/health` that returns:

```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "nova-ci-rescue-github-app",
  "version": "1.0.0"
}
```

Test it: `curl https://<your-app-name>.fly.dev/health`

#### Notes

- The server listens on port 8080 internally (see `github-app/index.js` and `fly.toml`).
- Required env vars: `APP_ID`, `PRIVATE_KEY`, `WEBHOOK_SECRET`.
- Manual updates: modify code, then `fly deploy` again.
- Automated updates: push to `main` branch (if GitHub Actions is configured).
