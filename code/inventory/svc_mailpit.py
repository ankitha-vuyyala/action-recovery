"""Step 4 — Mailpit: SMTP with X-Op-Id + custom Message-ID, API list/search/headers/delete."""
from __future__ import annotations

import json
import smtplib
import time
import uuid
from email.message import EmailMessage

import httpx

from common import save_part
from svc_common import exc_info

API = "http://localhost:8025/api/v1"


def main() -> None:
    d: dict = {}
    c = httpx.Client(base_url=API, timeout=10)
    d["version"] = c.get("/info").json().get("Version")
    c.delete("/messages")  # start from an empty capture store
    run_id = uuid.uuid4().hex[:8]
    sent = []
    # 1: uuid only in the header; 2: uuid also in body; 3: uuid also in subject
    for i, where in enumerate(["header-only", "header+body", "header+subject"], 1):
        op = str(uuid.uuid4())
        mid = f"<inv-{run_id}-{i}.{op}@inventory.invalid>"
        m = EmailMessage()
        m["From"] = "agent@inventory.invalid"
        m["To"] = "customer@inventory.invalid"
        m["Subject"] = f"Inventory probe {i}" + (f" {op}" if where == "header+subject" else "")
        m["Message-ID"] = mid
        m["X-Op-Id"] = op
        m.set_content("Hello from the inventory." + (f"\nop-id: {op}" if where == "header+body" else ""))
        t = time.perf_counter()
        with smtplib.SMTP("localhost", 1025, timeout=10) as s:
            s.send_message(m)
        sent.append({"i": i, "where": where, "op": op, "mid": mid, "smtp_s": round(time.perf_counter() - t, 3)})
    time.sleep(0.5)
    lst = c.get("/messages").json()
    d["list_total"] = lst.get("total")
    d["list_ok"] = lst.get("total") == 3
    by_mid = {}
    for msg in lst.get("messages", []):
        by_mid[msg["MessageID"]] = msg["ID"]
    results = []
    for s in sent:
        r: dict = {"where_uuid": s["where"], "smtp_send_s": s["smtp_s"]}
        stored_mid = s["mid"].strip("<>")
        r["message_id_listed_exact"] = stored_mid in by_mid
        mid_internal = by_mid.get(stored_mid)
        if mid_internal:
            hd = c.get(f"/message/{mid_internal}/headers").json()
            r["x_op_id_header_exact"] = hd.get("X-Op-Id") == [s["op"]]
            r["message_id_header_exact"] = hd.get("Message-Id", hd.get("Message-ID")) == [s["mid"]]
        q = c.get("/search", params={"query": s["op"]}).json()
        r["plain_search_finds"] = any(m["MessageID"] == stored_mid for m in q.get("messages", []))
        q = c.get("/search", params={"query": f"message-id:{stored_mid}"}).json()
        r["message_id_filter_finds"] = any(m["MessageID"] == stored_mid for m in q.get("messages", []))
        q = c.get("/search", params={"query": f'header:"X-Op-Id: {s["op"]}"'})
        r["header_filter_status"] = q.status_code
        r["header_filter_finds"] = q.status_code == 200 and any(m["MessageID"] == stored_mid for m in q.json().get("messages", []))
        results.append(r)
    d["messages"] = results
    ho = results[0]
    d["plain_search_matches_header_values"] = ho["plain_search_finds"]
    d["search_summary"] = ("plain search matches header values" if ho["plain_search_finds"]
                           else "plain search matches subject/body only (header-only uuid not found)")
    first_internal = by_mid.get(sent[0]["mid"].strip("<>"))
    r = c.request("DELETE", "/messages", json={"IDs": [first_internal]})
    after = c.get("/messages").json().get("total")
    d["delete_via_api"] = {"status": r.status_code, "total_after": after, "ok": r.status_code == 200 and after == 2,
                           "note": "deletes from the capture store only; this is not 'unsending'"}
    save_part("04_mailpit", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        save_part("04_mailpit_error", {"error": exc_info(e)})
        raise
