"""Offline logic tests of the follow-up conditions (docs/07_followup_plan.md) on the in-memory fake services.
No Docker, no network, no models. Run:  python -m pytest code/tests -q"""
from __future__ import annotations

import tempfile
import threading
import time

import pytest

import test_layers_fake as F
from actrec.driver_scripted import run_scripted
from actrec.episode import EpisodeConfig
from actrec.layers import make_layer
from actrec.services.base import CallResult
from actrec.tasks import make, resolve_args

LATE_REDELIVER = 0.3       # fake: the duplicate lands after S has finished but before S2's sweep (Δ = 0.7 s)


class FakeTB2(F.FakeTB):
    def by_content(self, tool, args, own_only=False):
        if not own_only or tool not in ("issue_create", "issue_comment"):
            return super().by_content(tool, args)
        return [e["id"] for e in self.eff[tool] if e["alive"] and not e.get("other") and self._match(tool, e, args)]


class FakeDisp2(F.FakeDisp):
    def dispatch(self, step, tool, args, *, tag=None, key=None, batch_only=None, deadline_s=None):
        focal = step == self.cfg.focal_step and not self.fired
        if focal and self.cfg.variant == "lookalike_other" and tool in ("issue_create", "issue_comment"):
            self.fired = True
            self.tb.apply(tool, args, actor=True)
            self.tb.eff[tool][-1]["other"] = True
            mode = self.cfg.mode
            return self._mode(mode, tool, args, tag, key, batch_only)
        if focal and self.cfg.variant == "lookalike" and tool == "mail_send_plain":
            self.tb.apply(tool, args, actor=True)
        if focal and self.cfg.mode == "redelivery_late":
            self.fired = True
            th = threading.Timer(LATE_REDELIVER, lambda: self.tb.apply(tool, args, tag, key, batch_only))
            th.start()
            self.threads.append(th)
            return CallResult("ok", 0.01, value=self.tb.apply(tool, args, tag, key, batch_only))
        return super().dispatch(step, tool, args, tag=tag, key=key, batch_only=batch_only, deadline_s=deadline_s)

    def _mode(self, mode, tool, args, tag, key, batch_only):
        saved, self.fired = self.fired, False
        self.cfg_variant = self.cfg.variant
        v = self.cfg.variant
        self.cfg.variant = "exact"                  # the look-alike is already there; inject the fault only
        try:
            return super().dispatch(self.cfg.focal_step, tool, args, tag=tag, key=key, batch_only=batch_only)
        finally:
            self.cfg.variant, self.fired = v, True


def run(template, focal, mode, condition, variant="exact"):
    task = make(template, 0)
    with tempfile.TemporaryDirectory() as d:
        cfg = EpisodeConfig(episode_id="t", run="t", task=task.to_dict(), focal_step=focal, mode=mode,
                            variant=variant, condition=condition, delta_assumed_s=F.DELAY + 0.3, state_dir=d)
        tb = FakeTB2(variant)
        disp = FakeDisp2(cfg, tb)
        rep = run_scripted(cfg, tb, disp, False)
        for th in disp.threads:
            th.join()
        time.sleep(0.05)
        bad = []
        for st in task.steps:
            if st.tool == "batch_insert":
                ok = all(len([e for e in tb.eff[st.tool] if e["alive"] and not e["actor"] and e["args"] == it]) == 1
                         for it in st.args["items"])
            else:
                a = resolve_args(st.args, {k: {"number": 1} for k in ["open_ticket"]}) or st.args
                ok = tb.standing(st.tool, a if st.tool != "issue_comment" else st.args) == 1
            if not ok:
                bad.append(st.name)
        return {"bad": bad, "collateral": tb.collateral(), "claimed": rep["claimed"], "uncertain": rep["uncertain"],
                "dups": rep.get("duplicates_reported", [])}


@pytest.mark.parametrize("mode", ["lost_ack", "not_exec_err", "late"])
@pytest.mark.parametrize("template,focal", [("T1", "open_issue"), ("T1", "log_row"), ("T4", "stock_1")])
def test_wait_then_count_prevents(template, focal, mode):
    r = run(template, focal, mode, "Sp")
    assert r["bad"] == [] and r["collateral"] == 0, r


def test_wait_then_count_misses_redelivery():
    r = run("T1", "open_issue", "redelivery", "Sp")
    assert "open_issue" in r["bad"]          # no sweep: the transport's duplicate stays


def test_settle_misses_delayed_redelivery_and_s2_catches_it():
    assert "open_issue" in run("T1", "open_issue", "redelivery_late", "S")["bad"]
    r = run("T1", "open_issue", "redelivery_late", "S2")
    assert r["bad"] == [] and r["collateral"] == 0, r


def test_s2_reports_delayed_redelivery_of_irreversible_mail():
    r = run("T1", "page_oncall", "redelivery_late", "S2")
    assert "page_oncall" in r["dups"] and r["claimed"] != "completed", r


@pytest.mark.parametrize("mode", ["lost_ack", "not_exec_err"])
def test_s2_abstains_on_content_only_lookalike(mode):
    r = run("T3", "announce", mode, "S2", variant="lookalike")
    assert "announce" in r["uncertain"] and r["claimed"] != "completed", r


@pytest.mark.parametrize("cond", ["C5", "Gw"])
def test_unfiltered_content_check_fooled_by_other_account(cond):
    r = run("T1", "open_issue", "not_exec_err", cond, variant="lookalike_other")
    assert "open_issue" in r["bad"], r


@pytest.mark.parametrize("cond", ["C5a", "Gwa"])
def test_author_filter_not_fooled_by_other_account(cond):
    r = run("T1", "open_issue", "not_exec_err", cond, variant="lookalike_other")
    assert "open_issue" not in r["bad"] and r["collateral"] == 0, r


def test_plan_free_intent_identity():
    task = make("T1", 0)
    with tempfile.TemporaryDirectory() as d:
        cfg = EpisodeConfig(episode_id="t", run="t", task=task.to_dict(), focal_step="open_issue", mode="none",
                            condition="S-np", state_dir=d)
        lay = make_layer(cfg, FakeTB2(), None)
        a = {"title": "Disk  full on db-1.", "body": "x"}
        b = {"title": "disk full on db-1", "body": "y"}
        assert lay.intent("whatever", "issue_create", a) == lay.intent("other", "issue_create", b)
        assert lay.intent("s", "issue_create", a) != lay.intent("s", "issue_create", {"title": "another", "body": "x"})
