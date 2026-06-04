#!/usr/bin/env bash
#
# start.sh — bring up the full CogniGraph stack in one command:
#   Neo4j (Docker)  →  seed graph  →  FastAPI backend (:8000)  →  React UI (:5173)
#
# Usage:
#   ./start.sh                start everything (seeds only if the graph is empty)
#   ./start.sh --reseed       force a wipe + reload of the deterministic seed graph
#   ./start.sh --from-doc     (re)build the graph by extracting it from the company
#                             brief with Claude (doc_to_graph.py — needs ANTHROPIC_API_KEY,
#                             costs an LLM call, non-deterministic). Implies a wipe + reload.
#   ./start.sh --skip-seed    never seed
#   ./start.sh --no-ui        backend + Neo4j only (no Vite dev server)
#   ./start.sh --stop         stop API, UI, and the Neo4j container, then exit
#   ./start.sh -h | --help
#
# Ctrl+C stops the API and UI dev servers; Neo4j keeps running (stop it with
# `./start.sh --stop` or `docker compose down`).
#
# Env overrides: API_PORT, UI_PORT, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"
NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-companygraph123}"

VENV="$ROOT/.venv"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

# ── pretty output ─────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  B=$'\e[1m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; D=$'\e[2m'; X=$'\e[0m'
else B=; G=; Y=; R=; D=; X=; fi
say()  { printf '%s\n' "${B}▶ $*${X}"; }
ok()   { printf '%s\n' "${G}✓ $*${X}"; }
warn() { printf '%s\n' "${Y}! $*${X}"; }
die()  { printf '%s\n' "${R}✗ $*${X}" >&2; exit 1; }

usage() { sed -n '3,20p' "$0" | sed 's/^#\{0,1\} \{0,1\}//'; }

# ── args ──────────────────────────────────────────────────────────────────────
SEED_MODE="auto"     # auto | force | skip
SEED_SOURCE="seed"   # seed (deterministic seed.py) | doc (Claude extraction via doc_to_graph.py)
START_UI=1
DO_STOP=0
for arg in "${@:-}"; do
  case "$arg" in
    "")            ;;
    --reseed)      SEED_MODE="force" ;;
    --from-doc)    SEED_SOURCE="doc"; SEED_MODE="force" ;;
    --skip-seed)   SEED_MODE="skip" ;;
    --no-ui)       START_UI=0 ;;
    --stop)        DO_STOP=1 ;;
    -h|--help)     usage; exit 0 ;;
    *)             die "unknown option: $arg  (try --help)" ;;
  esac
done

# docker compose v2 (`docker compose`) or v1 (`docker-compose`)
if docker compose version >/dev/null 2>&1; then DC=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then DC=(docker-compose)
else DC=(); fi

# kill whatever is listening on a TCP port (precise — not a broad pkill)
free_port() {
  local port="$1" pids
  pids="$(lsof -ti "tcp:${port}" 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    warn "freeing port $port (killing: $pids)"
    kill $pids 2>/dev/null || true
    sleep 1
  fi
  return 0
}

# ── --stop ────────────────────────────────────────────────────────────────────
if [[ "$DO_STOP" == 1 ]]; then
  say "Stopping CogniGraph…"
  for f in "$LOG_DIR/api.pid" "$LOG_DIR/ui.pid"; do
    if [[ -f "$f" ]]; then kill "$(cat "$f")" 2>/dev/null || true; rm -f "$f"; fi
  done
  free_port "$API_PORT"; [[ "$START_UI" == 1 ]] && free_port "$UI_PORT"
  [[ ${#DC[@]} -gt 0 ]] && "${DC[@]}" stop >/dev/null 2>&1 || true
  ok "Stopped API, UI, and Neo4j container."
  exit 0
fi

# ── preflight ─────────────────────────────────────────────────────────────────
say "Preflight checks"
command -v docker >/dev/null 2>&1 || die "docker not found — install Docker Desktop"
docker info >/dev/null 2>&1 || die "Docker daemon not running — start Docker Desktop"
[[ ${#DC[@]} -gt 0 ]] || die "neither 'docker compose' nor 'docker-compose' found"

# Python venv (create + install on first run)
if [[ ! -x "$VENV/bin/uvicorn" ]]; then
  warn "no .venv found — creating it and installing requirements (first-time setup, may take a few minutes)…"
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet -r "$ROOT/requirements.txt"
  ok "venv ready"
else
  ok "venv present"
fi
PY="$VENV/bin/python"

# UI dependencies
if [[ "$START_UI" == 1 ]]; then
  command -v npm >/dev/null 2>&1 || die "npm not found — install Node.js (needed for the UI; or run with --no-ui)"
  if [[ ! -d "$ROOT/UI/node_modules" ]]; then
    warn "UI/node_modules missing — running npm install…"
    ( cd "$ROOT/UI" && npm install --silent )
    ok "UI deps installed"
  else ok "UI deps present"; fi
fi

[[ -f "$ROOT/.env" ]] || warn ".env not found — LLM query endpoints need ANTHROPIC_API_KEY (graph + search still work without it)"
grep -q "ANTHROPIC_API_KEY" "$ROOT/.env" 2>/dev/null || warn "ANTHROPIC_API_KEY not set in .env — /query, /query/agent, /query/orchestrate will error until it is"

# ── 1. Neo4j ──────────────────────────────────────────────────────────────────
say "Starting Neo4j (Docker)"
"${DC[@]}" up -d
printf '%s' "${D}  waiting for Neo4j to accept connections${X}"
for i in $(seq 1 60); do
  if "$PY" - <<PYEOF >/dev/null 2>&1
from neo4j import GraphDatabase
GraphDatabase.driver("$NEO4J_URI", auth=("$NEO4J_USER", "$NEO4J_PASSWORD")).verify_connectivity()
PYEOF
  then printf '\n'; ok "Neo4j ready (bolt $NEO4J_URI)"; break; fi
  printf '.'; sleep 2
  if [[ "$i" -eq 60 ]]; then printf '\n'; die "Neo4j did not become ready in 120s — check: ${DC[*]} logs neo4j"; fi
done

# ── 2. Seed ───────────────────────────────────────────────────────────────────
node_count() {
  "$PY" - <<PYEOF 2>/dev/null
from neo4j import GraphDatabase
d = GraphDatabase.driver("$NEO4J_URI", auth=("$NEO4J_USER", "$NEO4J_PASSWORD"))
with d.session() as s:
    print(s.run("MATCH (n) RETURN count(n) AS c").single()["c"])
PYEOF
}
# Load the graph using the chosen source: deterministic seed.py, or Claude
# extraction from the company brief (doc_to_graph.py --clear).
run_seed() {
  if [[ "$SEED_SOURCE" == "doc" ]]; then
    grep -q "ANTHROPIC_API_KEY" "$ROOT/.env" 2>/dev/null \
      || die "--from-doc needs ANTHROPIC_API_KEY in .env (it calls Claude to extract the graph)"
    say "Building graph from company brief via Claude (doc_to_graph.py — costs an LLM call)"
    ( cd "$ROOT/backend" && "$PY" doc_to_graph.py --clear ) | tail -4
  else
    ( cd "$ROOT/backend" && "$PY" seed.py ) | tail -3
  fi
}
case "$SEED_MODE" in
  skip)  warn "skipping seed (--skip-seed)";;
  force)
    [[ "$SEED_SOURCE" == "doc" ]] || say "Re-seeding graph (wipes existing data)"
    run_seed; ok "graph loaded";;
  auto)
    count="$(node_count || echo 0)"
    if [[ "${count:-0}" -gt 0 ]]; then
      ok "graph already has $count nodes — skipping seed (use --reseed or --from-doc to rebuild)"
    else
      say "Graph is empty — seeding Meridian Property Group data"
      run_seed; ok "graph loaded"
    fi;;
esac

# ── 3. Backend API ────────────────────────────────────────────────────────────
say "Starting FastAPI backend (:$API_PORT)"
free_port "$API_PORT"
( cd "$ROOT/backend" && exec "$VENV/bin/uvicorn" api:app --host 0.0.0.0 --port "$API_PORT" ) \
  > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!
echo "$API_PID" > "$LOG_DIR/api.pid"
for i in $(seq 1 40); do
  if curl -fsS "http://localhost:$API_PORT/" >/dev/null 2>&1; then ok "API ready (http://localhost:$API_PORT)"; break; fi
  kill -0 "$API_PID" 2>/dev/null || die "API process died — see $LOG_DIR/api.log"
  sleep 1
  if [[ "$i" -eq 40 ]]; then die "API did not respond in 40s — see $LOG_DIR/api.log"; fi
done

# ── 4. UI dev server ──────────────────────────────────────────────────────────
UI_PID=""
if [[ "$START_UI" == 1 ]]; then
  say "Starting React UI (:$UI_PORT)"
  free_port "$UI_PORT"
  ( cd "$ROOT/UI" && exec npm run dev -- --port "$UI_PORT" --strictPort ) \
    > "$LOG_DIR/ui.log" 2>&1 &
  UI_PID=$!
  echo "$UI_PID" > "$LOG_DIR/ui.pid"
  for i in $(seq 1 40); do
    if curl -fsS "http://localhost:$UI_PORT/" >/dev/null 2>&1; then ok "UI ready (http://localhost:$UI_PORT)"; break; fi
    kill -0 "$UI_PID" 2>/dev/null || die "UI process died — see $LOG_DIR/ui.log"
    sleep 1
    if [[ "$i" -eq 40 ]]; then warn "UI not responding yet — check $LOG_DIR/ui.log"; fi
  done
fi

# ── summary + wait ────────────────────────────────────────────────────────────
cleanup() {
  printf '\n'; say "Shutting down API and UI…"
  [[ -n "${UI_PID:-}" ]] && kill "$UI_PID" 2>/dev/null || true
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  rm -f "$LOG_DIR/api.pid" "$LOG_DIR/ui.pid"
  ok "Stopped. Neo4j is still running — './start.sh --stop' to stop it too."
  exit 0
}
trap cleanup INT TERM

cat <<EOF

${G}${B}CogniGraph is up.${X}
  ${B}UI${X}        http://localhost:$UI_PORT            ${D}(Graph · Query · Observe)${X}
  ${B}API${X}       http://localhost:$API_PORT            ${D}(/query · /query/agent · /query/orchestrate · /search)${X}
  ${B}Neo4j${X}     http://localhost:7474           ${D}(neo4j / $NEO4J_PASSWORD)${X}
  ${B}logs${X}      $LOG_DIR/api.log · $LOG_DIR/ui.log

${D}Press Ctrl+C to stop the API and UI. Neo4j stays up (./start.sh --stop to stop everything).${X}
EOF

# Keep running in the foreground so Ctrl+C triggers cleanup; stream both logs.
if [[ "$START_UI" == 1 ]]; then tail -f "$LOG_DIR/api.log" "$LOG_DIR/ui.log" &
else tail -f "$LOG_DIR/api.log" & fi
TAIL_PID=$!
wait "$API_PID"
kill "$TAIL_PID" 2>/dev/null || true
cleanup
