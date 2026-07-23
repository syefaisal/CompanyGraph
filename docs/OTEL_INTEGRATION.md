# OpenTelemetry Integration — LangSmith → OTel Gateway → LGTM

**Status:** verified end-to-end locally (2026-07-23) against a debug collector.
Not yet pointed at a real gateway.
**Context:** the org is migrating observability from ELK/OpenSearch to an
OTel-native LGTM stack (Loki / Tempo / Mimir / Grafana). CogniGraph is a
telemetry *producer* in that architecture — this document covers how its traces
get there.

> Companion to `PRODUCTION_TRANSITION.md` §observability. The stack-level
> decisions live in the observability ADR
> (`LGTM_thought_process/docs/adr/ADR-observability-pipeline-lgtm-opensearch.md`).

---

## 1. What this changes — and what it doesn't

**No application code changed.** `backend/api.py` keeps
`wrap_anthropic(AsyncAnthropic())` and its `@traceable` decorators exactly as
they were. Setting `LANGSMITH_OTEL_ENABLED=true` swaps the *transport*
underneath the LangSmith SDK: the same runs it used to POST to LangSmith Cloud
are emitted as OTLP spans instead. The three instrumentation points from
`README.md` are unchanged:

| Instrumentation | Mechanism | Emitted span |
|---|---|---|
| Every agent-loop LLM call | `wrap_anthropic` patches `messages.create` | `ChatAnthropic` |
| Every tool execution | `@traceable` on `_execute_agent_tool` | `execute_graph_tool` |
| Query routing decision | `@traceable` on `route_query` | `route_query` |

This project has **no LangChain dependency** — it drives the Anthropic SDK
directly. That makes no difference to the OTel path; `wrap_anthropic` is what
produces the runs.

## 2. Topology

```
CogniGraph API (host, uvicorn :8000)
  │  OTLP/HTTP, plaintext, loopback only
  ▼
otel-agent collector (docker-compose, 127.0.0.1:4317/4318)
  │  OTLP/gRPC over mTLS
  ▼
LGTM gateway  ──►  Tempo (traces) / Loki (logs) / Mimir (metrics)
```

The sidecar exists so the application holds **no TLS material** and gets a
disk-backed send queue it doesn't otherwise have. Per the ADR, fan-out and
routing to multiple backends live at the **gateway** tier only; this tier is a
plain forwarder to one endpoint.

**Traces, not logs.** LangSmith emits spans — they land in **Tempo**. Loki
receives application log lines, which are a separate signal this project does
not yet emit over OTLP.

## 3. Files

| Path | Role |
|---|---|
| `deploy/otel-agent-config.yaml` | Production collector config (mTLS → gateway, disk queue) |
| `deploy/otel-agent-config.debug.yaml` | Debug variant — spans to stdout, no TLS, no gateway |
| `deploy/Dockerfile.otel` | Bakes the debug config into an image (see §6, file sharing) |
| `deploy/smoke-test-otel.sh` | Posts one synthetic span; isolates collector from app |
| `docker-compose.yml` | `otel-agent` service, behind the `otel` profile |
| `docker-compose.debug.yml` | Override that swaps to the debug config |
| `requirements.txt` | `langsmith[otel]>=0.4.25` — the extra is load-bearing |
| `.env.example` | Env reference (§4) |

## 4. Configuration

```bash
LANGSMITH_TRACING=true            # modern spelling; the OTel path checks this,
                                  # not the legacy LANGSMITH_TRACING_V2
LANGSMITH_OTEL_ENABLED=true       # emit OTLP instead of LangSmith-native
LANGSMITH_OTEL_ONLY=false         # false = dual-ship to LangSmith Cloud too

OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318   # BASE URL — see §5

# Consumed by the collector container, not the app:
OTEL_SERVICE_NAME=cogni-graph
ENVIRONMENT=dev
LGTM_GATEWAY_ENDPOINT=otelcol-gateway.observability.svc:4317
```

`LANGSMITH_TRACING_V2=true` is kept alongside `LANGSMITH_TRACING` so existing
behaviour is unaffected during migration.

Keep `LANGSMITH_OTEL_ONLY=false` through the ADR's pilot parallel-run so both
backends receive the same traces and can be compared. Flip to `true` only once
Tempo is trusted as the system of record.

## 5. Two silent failure modes

Both were hit during this integration. Neither produces an error at the
collector, and one produces no error anywhere the operator is likely to look.

### 5.1 `langsmith` alone is not enough — the `[otel]` extra is required

The OTel SDK and OTLP exporter ship in the extra. Without them,
`LANGSMITH_OTEL_ENABLED=true` is **ignored with no warning** and traces continue
to LangSmith Cloud.

```bash
# Diagnostic — must not raise:
.venv/bin/python -c "from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter"
```

Fix: `langsmith[otel]>=0.4.25` in `requirements.txt`. (`>=0.4.25` is separately
required for `LANGSMITH_OTEL_ONLY`; OTLP export landed in 0.4.1.)

### 5.2 `OTEL_EXPORTER_OTLP_ENDPOINT` must be a base URL

The OTLP exporter appends the signal path itself. Supplying
`http://127.0.0.1:4318/v1/traces` yields a request to
`/v1/traces/v1/traces` and the collector returns 404:

```
Failed to export span batch code: 404, reason: Not Found
```

This appears on **stderr of the application process only** — the collector logs
nothing, so it reads as "spans never sent" rather than "spans rejected." The
LangSmith documentation shows the suffixed form; it is wrong for this variable.

Correct value: `http://127.0.0.1:4318`.

## 6. Environment-specific gotchas

**Docker Desktop file sharing.** `/Users/syefai/workspace` is not in the
file-sharing list, so bind-mounting the collector config is denied
(`mounts denied: ... not shared from the host`). The debug path works around it
via `deploy/Dockerfile.otel`, because build contexts stream over the API and
need no sharing entry. Consequence: editing the debug config requires
`--build`, not just a restart. The production config still bind-mounts and needs
the path added under Docker Desktop → Settings → Resources → File Sharing.

**Compose profile.** `start.sh:127` runs a bare `docker compose up -d`, which
would recreate the collector using the production config (and its TLS bind
mount), killing whatever collector is already running. The `otel-agent` service
is therefore behind `profiles: ["otel"]`; naming it explicitly on the command
line auto-enables the profile.

**`volumes: []` does not clear a merged list.** Compose appends sequences across
override files. Use `volumes: !reset []` (Compose ≥2.24) to drop the base file's
mounts in an override.

**Neo4j stale pid.** `./start.sh --stop` followed by a restart leaves a pid file
in the container and Neo4j fails its 120s readiness check with
`Neo4j is already running (pid:7)`. Recover by recreating the container — the
data volume is untouched:

```bash
docker compose rm -sf neo4j && docker compose up -d neo4j
```

To restart only the API, avoid `--stop` entirely:

```bash
pkill -f "uvicorn.*api:app" && ./start.sh --no-ui --skip-seed
```

## 7. Verification procedure

```bash
# 1. collector (debug: spans → stdout)
docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d --build otel-agent
docker compose -f docker-compose.yml -f docker-compose.debug.yml logs -f otel-agent

# 2. transport only — no app required
./deploy/smoke-test-otel.sh          # expect HTTP 200 + a span in the log

# 3. full path
uv pip install --python .venv/bin/python -r requirements.txt
docker compose up -d neo4j
./start.sh --no-ui --skip-seed
curl -s -X POST http://127.0.0.1:8000/query/agent \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which teams depend on the billing service?"}'
```

Step 2 isolates the collector. If it passes and step 3 does not, the fault is in
the LangSmith configuration (§5), not the collector.

### Observed result

One `/query/agent` call produced 18 spans; a second, broader query produced 33:

```
 21 execute_graph_tool
 10 ChatAnthropic
  1 route_query
  1 agent_query
```

Attributes present on LLM spans:

```
gen_ai.request.model          gen_ai.usage.input_tokens
gen_ai.system                 gen_ai.usage.output_tokens
gen_ai.operation.name         gen_ai.usage.total_tokens
langsmith.metadata.*          (domain, revision_id, ls_provider, ls_model_name, …)
service.name / deployment.environment / collector.tier   ← stamped by the collector
```

Token counts and model id (`claude-sonnet-4-6`) arrive intact, so per-query cost
dashboards can be built in Grafana from span data without reading `/metrics`.

## 8. Dependency note

Installing `langsmith[otel]` outside the constraints file lets the resolver
upgrade transitive pins — it bumped `pydantic` 2.10.3 → 2.13.4. That bump was
**not** required (`langsmith` needs only `pydantic>=2.7.4`); the pin was restored
to `2.10.3` and the full path re-verified on it. Install via
`-r requirements.txt` to avoid the drift.

## 9. Remaining work before the real gateway

1. **TLS material** in `deploy/otel-tls/` (`ca.crt`, `tls.crt`, `tls.key`) for the
   gateway's mTLS receiver.
2. **`LGTM_GATEWAY_ENDPOINT`** — currently the k8s service DNS default,
   unreachable off-cluster.
3. **Docker Desktop file sharing** for the production bind mount (§6), or extend
   the Dockerfile approach to the production config.
4. **`service.name` uses `action: upsert`** in the collector config, overriding
   whatever the app sends. Correct for a single-app sidecar; switch to `insert`
   if this collector ever fronts a second service, or everything will be
   mislabelled `cogni-graph` in Tempo and Loki.
5. **Flip `LANGSMITH_OTEL_ONLY=true`** at cutover.
6. **Application logs over OTLP** — currently only traces are exported. Loki gets
   nothing from this service until stdlib `logging` is bridged to OTLP with the
   trace context attached, which is what enables Grafana's log↔trace pivot.
