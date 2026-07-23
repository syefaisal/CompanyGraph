#!/usr/bin/env bash
#
# smoke-test-otel.sh — prove the OTLP path works without running CogniGraph.
#
# Posts one synthetic span to the agent collector's OTLP/HTTP receiver. If the
# collector is wired correctly you'll see it printed in `docker compose logs
# otel-agent` with service.name=cogni-graph and collector.tier=agent attached
# by the resource processor.
#
# Usage:
#   ./deploy/smoke-test-otel.sh              # defaults to 127.0.0.1:4318
#   OTLP_HTTP=host:4318 ./deploy/smoke-test-otel.sh
set -euo pipefail

OTLP_HTTP="${OTLP_HTTP:-127.0.0.1:4318}"
URL="http://${OTLP_HTTP}/v1/traces"

# 16-byte trace id / 8-byte span id, hex.
TRACE_ID=$(printf '%032x' $((RANDOM * RANDOM * RANDOM)))
SPAN_ID=$(printf '%016x' $((RANDOM * RANDOM)))
NOW_NS=$(( $(date +%s) * 1000000000 ))

read -r -d '' PAYLOAD <<EOF || true
{
  "resourceSpans": [{
    "resource": { "attributes": [
      { "key": "service.name", "value": { "stringValue": "smoke-test" } }
    ]},
    "scopeSpans": [{
      "scope": { "name": "smoke-test" },
      "spans": [{
        "traceId": "${TRACE_ID}",
        "spanId": "${SPAN_ID}",
        "name": "otel-smoke-test",
        "kind": 1,
        "startTimeUnixNano": "${NOW_NS}",
        "endTimeUnixNano": "$(( NOW_NS + 1000000 ))",
        "attributes": [
          { "key": "test.marker", "value": { "stringValue": "hello-lgtm" } }
        ]
      }]
    }]
  }]
}
EOF

echo "POST ${URL}"
CODE=$(curl -s -o /tmp/otel-smoke.out -w '%{http_code}' \
  -X POST "${URL}" \
  -H 'Content-Type: application/json' \
  -d "${PAYLOAD}")

echo "HTTP ${CODE}"
cat /tmp/otel-smoke.out; echo

if [[ "${CODE}" == "200" ]]; then
  echo
  echo "Accepted. Now confirm the collector actually emitted it:"
  echo "  docker compose logs otel-agent | grep -A5 otel-smoke-test"
  echo
  echo "A 200 only means the receiver took it — the debug exporter log is the"
  echo "proof it traversed the pipeline."
else
  echo
  echo "Not accepted. Check the collector is up and the port is published:"
  echo "  docker compose -f docker-compose.yml -f docker-compose.debug.yml ps"
  exit 1
fi
