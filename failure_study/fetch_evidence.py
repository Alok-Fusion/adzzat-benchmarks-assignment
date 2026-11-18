"""Re-download the public logs behind failure_study/FAILURE_STUDY.md and recompute every number in it.

    python failure_study/fetch_evidence.py

Source: the SWE-bench Verified leaderboard run "mini-SWE-agent v1.0.0 + Qwen2.5-Coder-32B-Instruct"
(open-weight model, bash-only scaffold, 1 attempt per task). Its logs are public:
  metadata : github.com/SWE-bench/experiments/tree/main/evaluation/verified/20250803_mini-v1.0.0_qwen2-5-coder-32b-instruct
  logs     : https://swe-bench-submissions.s3.amazonaws.com/bash-only/20250803_mini-v1.0.0_qwen2-5-coder-32b-instruct/
Writes small summaries to failure_study/evidence/. Full trajectories are not committed because of their size,
but they come from the same URLs.
"""
import json
import os
import re
import urllib.request
from collections import Counter
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, "evidence")
RUN = "20250803_mini-v1.0.0_qwen2-5-coder-32b-instruct"
S3 = f"https://swe-bench-submissions.s3.amazonaws.com/bash-only/{RUN}"
GH = "https://raw.githubusercontent.com/SWE-bench/experiments/main/evaluation/verified"
COMPARE = ["20250929_mini-v1.13.3_sonnet-4-5-20250929", "20250807_mini-v1.7.0_gpt-5",
           "20251124_mini-v1.16.0_claude-opus-4-5-20251101", "20250726_mini-v1.0.0_gemini-2.5-pro",
           "20250802_mini-v1.0.0_qwen3-coder-480b-a35b-instruct"]
CASES = ["django__django-11141", "django__django-10999", "matplotlib__matplotlib-25479",
         "django__django-13128", "scikit-learn__scikit-learn-25232", "django__django-11133",
         "django__django-10914", "django__django-11179"]


def get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read().decode("utf-8", errors="replace")


def commands(traj):
    out = []
    for m in traj["messages"]:
        if m["role"] == "assistant":
            c = m["content"] if isinstance(m["content"], str) else str(m["content"])
            f = re.findall(r"```bash\n(.*?)```", c, re.S)
            out.append(f[0].strip() if f else "<no command>")
    return out


def main():
    os.makedirs(EV, exist_ok=True)
    qwen = json.loads(get(f"{GH}/{RUN}/per_instance_details.json"))
    others = {s: json.loads(get(f"{GH}/{s}/per_instance_details.json")) for s in COMPARE}

    # 1. Whole-run statistics: how many "patches" are really API error text?
    preds = [json.loads(l) for l in get(f"{S3}/all_preds.jsonl").splitlines() if l.strip()]
    api = [p["instance_id"] for p in preds if (p.get("model_patch") or "").lstrip().startswith("litellm.")]
    empty = [p["instance_id"] for p in preds if not (p.get("model_patch") or "").strip()]
    resolved = sum(v["resolved"] for v in qwen.values())
    stats = {"instances_in_results": len(qwen), "predictions_in_all_preds": len(preds),
             "resolved": resolved, "reported_rate": resolved / len(qwen),
             "patch_is_api_error_text": len(api), "patch_empty": len(empty),
             "resolved_among_api_error": sum(qwen[i]["resolved"] for i in api if i in qwen),
             "rate_if_api_errors_excluded": resolved / (len(qwen) - len(api))}
    json.dump({"stats": stats, "api_error_instances": api}, open(os.path.join(EV, "run_stats.json"), "w"), indent=1)
    print(json.dumps(stats, indent=1))

    # 2. Per-case summaries
    for iid in CASES:
        rep = json.loads(get(f"{S3}/logs/{iid}/report.json"))[iid]
        traj = json.loads(get(f"{S3}/trajs/{iid}/{iid}.traj.json"))
        patch = get(f"{S3}/logs/{iid}/patch.diff")
        cmds = commands(traj)
        summary = {
            "instance": iid,
            "exit_status": traj.get("info", {}).get("exit_status"),
            "agent_turns": len(cmds),
            "most_repeated_commands": Counter(cmds).most_common(3),
            "patch_chars": len(patch),
            "patch_head": patch[:400],
            "FAIL_TO_PASS_failed": rep["tests_status"]["FAIL_TO_PASS"]["failure"],
            "PASS_TO_PASS_failed_count": len(rep["tests_status"]["PASS_TO_PASS"]["failure"]),
            "strong_models_that_solved_it": [s for s, d in others.items() if d.get(iid, {}).get("resolved")],
            "commands": [c[:300] for c in cmds],
        }
        json.dump(summary, open(os.path.join(EV, f"{iid}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"{iid:34s} exit={summary['exit_status']:15s} turns={len(cmds):3d} patch={len(patch):6d}ch "
              f"F2P_fail={len(summary['FAIL_TO_PASS_failed'])} P2P_fail={summary['PASS_TO_PASS_failed_count']} "
              f"strong_solved={len(summary['strong_models_that_solved_it'])}/5")

    # 3. django-10999: does the regex the issue itself suggests pass the hidden test's expectations?
    #    The expected values below are copied from the failing assertions in that instance's test_output.txt.
    num = r"(?:(?P<days>-?\d+) (days?, )?)?"
    tail = r"(?:(?P<minutes>-?\d+):)?(?P<seconds>-?\d+)(?:\.(?P<microseconds>\d{1,6})\d{0,6})?$"
    original = re.compile("^" + num + r"((?:(?P<hours>-?\d+):)(?=\d+:\d+))?" + tail)
    suggested = re.compile("^" + num + r"((?:(?P<hours>-?\d+):)(?=-?\d+:-?\d+))?" + tail)

    def parse(rx, s):  # same arithmetic as django.utils.dateparse.parse_duration for these inputs
        m = rx.match(s)
        if not m:
            return None
        kw = {k: float(v) for k, v in m.groupdict().items() if v and k != "microseconds"}
        return timedelta(**kw)

    expected = {"-15:30": timedelta(seconds=-930), "-1:15:30": timedelta(seconds=-4530),
                "-00:01:01": timedelta(seconds=-61), "-01:01": timedelta(seconds=-61), "-01:-01": None}
    rows = [{"input": s, "expected_by_hidden_test": str(e), "original_code": str(parse(original, s)),
             "issue_suggested_fix": str(parse(suggested, s)), "suggested_fix_passes": parse(suggested, s) == e}
            for s, e in expected.items()]
    json.dump(rows, open(os.path.join(EV, "django-10999_issue_fix_check.json"), "w"), indent=1)
    print("\ndjango-10999: the issue's own suggested regex passes", sum(r["suggested_fix_passes"] for r in rows),
          "of", len(rows), "negative-duration cases in the hidden test")


if __name__ == "__main__":
    main()
