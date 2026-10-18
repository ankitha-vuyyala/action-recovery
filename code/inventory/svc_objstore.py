"""Step 4 — S3 object stores (SeaweedFS; MinIO if an image is available): metadata, If-None-Match, list by prefix.

Usage: svc_objstore.py <name> <endpoint>   e.g.  svc_objstore.py seaweedfs http://localhost:8333
"""
from __future__ import annotations

import json
import sys
import time
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from common import save_part
from svc_common import S3_KEY, S3_SECRET, exc_info


def err(e: Exception) -> dict:
    if isinstance(e, ClientError):
        return {"http_status": e.response["ResponseMetadata"].get("HTTPStatusCode"),
                "code": e.response["Error"].get("Code"), "message": e.response["Error"].get("Message")}
    return exc_info(e)


def main(name: str, endpoint: str) -> None:
    d: dict = {"endpoint": endpoint}
    s3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=S3_KEY, aws_secret_access_key=S3_SECRET,
                      region_name="us-east-1", config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 1}))
    bucket = "inv-probe"
    try:
        s3.create_bucket(Bucket=bucket)
        d["create_bucket"] = "ok"
    except Exception as e:
        d["create_bucket"] = err(e)
    op = str(uuid.uuid4())
    key = f"ops/{op}/result.json"
    try:
        t = time.perf_counter()
        s3.put_object(Bucket=bucket, Key=key, Body=b'{"v":1}', Metadata={"op-id": op})
        d["put_s"] = round(time.perf_counter() - t, 3)
        h = s3.head_object(Bucket=bucket, Key=key)
        d["head_metadata"] = h.get("Metadata")
        d["metadata_roundtrip_ok"] = h.get("Metadata", {}).get("op-id") == op
    except Exception as e:
        d["put_head_error"] = err(e)

    ckey = f"ops/{op}/conditional.json"
    cond = {}
    for attempt, body in (("first", b"A"), ("second", b"B")):
        try:
            s3.put_object(Bucket=bucket, Key=ckey, Body=body, IfNoneMatch="*")
            cond[attempt] = "accepted"
        except Exception as e:
            cond[attempt] = err(e)
    try:
        cond["stored_body_after"] = s3.get_object(Bucket=bucket, Key=ckey)["Body"].read().decode()
    except Exception as e:
        cond["stored_body_after"] = err(e)
    second = cond.get("second")
    cond["second_rejected_412"] = isinstance(second, dict) and second.get("http_status") == 412
    cond["silently_overwrote"] = second == "accepted" and cond["stored_body_after"] == "B"
    d["if_none_match_star"] = cond

    try:
        for i in range(3):
            s3.put_object(Bucket=bucket, Key=f"ops/{op}/extra-{i}", Body=b"x")
        s3.put_object(Bucket=bucket, Key=f"other/{op}", Body=b"x")
        lst = s3.list_objects_v2(Bucket=bucket, Prefix=f"ops/{op}/")
        keys = [o["Key"] for o in lst.get("Contents", [])]
        d["list_by_prefix"] = {"count": len(keys), "expected": 5, "ok": len(keys) == 5}
    except Exception as e:
        d["list_by_prefix"] = err(e)
    save_part(f"04_objstore_{name}", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
