# Country Availability: full details

[Back to the short README](../README.md)

A small web app that answers one question: **"Can people in country X open this website right now?"**

You enter URLs and pick countries. The app asks probe servers in those countries to fetch each URL, judges each answer with rules stored in a database, and shows the availability per country (for example "China 0%, Thailand 100%"). A scheduler can repeat the check every hour and keep a history.

> **This repository is a demo.** The real system SSHes into probe servers abroad. Here every probe is **simulated** inside the backend (`backend/simulation.py`), so the app runs anywhere with no remote servers. All hosts, IPs and names in the demo data are made up (documentation IP ranges, `.example` domains).

## Why it matters for an SRE job

| Skill | Where to see it |
|-------|-----------------|
| Containers | One Dockerfile per component, a self-contained `docker-compose.yml` |
| CI/CD | `.github/workflows/ci.yml`: test, build and push images to GHCR, then update the GitOps repo |
| GitOps | Argo CD watches [`Albertycl/gitops-apps`](https://github.com/Albertycl/gitops-apps) (`manifests/country-availability/`); nobody runs `kubectl apply` for releases |
| Kubernetes | Deployments, Services, a MariaDB StatefulSet with a PVC, Secrets created by hand, readiness probes, resource limits |
| Rollback | `git revert` of one commit in the GitOps repo |
| Observability of the app itself | Health and scheduler status endpoints, logs on stdout |
| Demo without the real world | A fake transport layer lets the real logic (rules, maths, scheduler) run with no remote servers |

Deliberately simple: one replica of everything, no authentication, no metrics endpoint. On K3s it is published over HTTPS (Traefik and a Let's Encrypt certificate) at https://availability.albertycliu.xyz.

## Architecture

| Component | Tech | Notes |
|-----------|------|-------|
| frontend | Vue 3 + Quasar, served by nginx | nginx proxies `/be/` to the backend, so the browser only talks to one origin |
| backend | Flask, SQLAlchemy, Waitress, APScheduler | Blueprints for the test flow, whitelist rules and scheduled monitoring |
| database | MariaDB 11.1 | Probe list, URLs, results, whitelist rules, scheduled domains and history |
| probes | Simulated (`SIMULATION_MODE=1`) | With `0` the backend uses Paramiko to SSH into real probes and curl from there |

Request flow:

1. The browser sends URLs and countries to the frontend nginx, which forwards `/be/...` to the backend.
2. The backend takes the probes of those countries from the database and runs `curl` on each probe. (Simulated: a fake SSH client answers in-process.)
3. The backend reads each probe's curl output and judges it with the whitelist rules in the database: failure rules (error text such as "Could not resolve host") and success rules (a marker in the page). Anything else counts as "unknown".
4. It stores the result per probe, calculates availability per country and returns it to the UI.

### Simulation rules

The host name of the URL decides what the fake probes see:

| Keyword in the host | Result |
|---------------------|--------|
| `down` | fails from every country |
| `blocked` | fails from China only |
| `partial` | about half of the probes fail |
| `unknown` | Malaysia and Thailand get a page that no rule recognises |
| anything else | decided by a hash of the name: mostly healthy, sometimes blocked in one country |

Try `https://www.blocked-demo.example` and `https://www.demo-site-one.example` with China and Thailand selected.

## Install and run

### A. Locally with Docker Compose

Prerequisites: Docker with the Compose plugin.

```bash
cp .env.example .env        # set DB_PASSWORD and DB_ROOT_PASSWORD; FRONTEND_PORT is optional (default 5440)
docker compose up --build
```

Open `http://localhost:5440`. The first start creates the tables and loads the demo probes and rules (`backend/demo/seed_demo_data.sql`) because `SEED_DEMO=1` and the database is empty. Pages: `/filtered` (run a test), `/whitelist` (rules). The scheduled-monitoring page is at `/scheduled`; it is not in the menu.

Stop with `docker compose down` (add `-v` to delete the database volume).

### B. On Kubernetes (K3s) with Argo CD

1. Install Argo CD, then apply the app-of-apps once (from the GitOps repo): `kubectl apply -f argocd/root-app.yaml`. Argo CD then creates the application from `apps/country-availability.yaml` and the `country-availability` namespace.
2. Create the Secret by hand, once the namespace exists (names and keys only; choose your own values):
   ```bash
   kubectl -n country-availability create secret generic country-db \
     --from-literal=root-password='<choose>' \
     --from-literal=database-url='mysql+pymysql://root:<same password>@mariadb:3306/country_availability'
   ```
   The pods wait until the Secret exists.
3. After the first CI run, set both GHCR packages (`country-availability-backend`, `country-availability-frontend`) to **public**. The manifests use no `imagePullSecrets`, so until then pods show `ImagePullBackOff`.
4. Check: `kubectl get applications -n argocd` should show `country-availability` as `Synced` and `Healthy`, and `kubectl get pods -n country-availability` should show all pods `Running`.
5. Open it through the Traefik IngressRoute and the `country-availability-tls` certificate (the hostname is in `manifests/country-availability/ingress.yaml`), or for a quick look: `kubectl -n country-availability port-forward svc/frontend 8080:80`, then `http://localhost:8080`.

## CI/CD and rollback

On every push to `main`, `.github/workflows/ci.yml` runs:

1. **test** (also on pull requests): backend `import` check and a full Quasar build.
2. **build**: builds the two images and pushes them to `ghcr.io/albertycl/country-availability-{backend,frontend}` tagged with the commit SHA and `latest`.
3. **update-gitops**: runs `kustomize edit set image` in `manifests/country-availability/` of the GitOps repo and pushes a commit named `country-availability: deploy <sha>` using a deploy key (repo secret `GITOPS_DEPLOY_KEY`).
4. Argo CD sees the commit and syncs (automated, with prune and self-heal).

**Rollback:** `git revert` the `deploy <sha>` commit in `Albertycl/gitops-apps`. Do not use `kubectl rollout undo`; self-heal would undo it.

## Monitoring and known limits

- Monitoring that exists: container logs, the readiness probes, and the backend's scheduler status endpoint (`/be/scheduled/api/scheduler-health` through the frontend). There is no Prometheus endpoint and no alert rules for this app.
- Probes are simulated; real probing needs your own SSH probe servers (the SSH password is read from `SSH_PASSWORD`). There are no automated tests: CI only checks that the backend imports and the frontend builds. Python dependencies are not pinned.
- No authentication. The public demo is open on purpose: the probes are simulated and the data is made up. Add authentication before using real probes or data.
- Single replica. The database runs in the same namespace on a 2 Gi volume and is not backed up.
- Some leftover pages (`/old`, paping monitoring) come from the original project and are not part of the demo.
