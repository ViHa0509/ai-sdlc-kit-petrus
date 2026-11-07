"""Tests for hooks/sdlc_hooks.py: feed hook JSON on stdin, assert the decisions.

Run from the repo root: python -m unittest -v
Test secrets are built at runtime from pieces so no real-looking secret sits in this file.
"""

import base64
import json
import os
import random
import shutil
import string
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "hooks", "sdlc_hooks.py")
SHIM = os.path.join(ROOT, "hooks", "run.sh")
PY = sys.executable.replace("\\", "/")
_rng = random.SystemRandom()


def rnd(n, alphabet=string.ascii_letters + string.digits):
    while True:
        s = "".join(_rng.choice(alphabet) for _ in range(n))
        if any(c.isdigit() for c in s) and any(c.isalpha() for c in s):
            return s


def anthropic_key():
    return "sk" + "-ant-" + "api03-" + rnd(60)


def github_token():
    return "gh" + "p_" + rnd(36)


def aws_key():
    return "AK" + "IA" + rnd(16, string.ascii_uppercase + string.digits)


def pem_block():
    body = base64.b64encode(os.urandom(120)).decode()
    return "-----BEGIN " + "RSA PRIVATE" + " KEY-----\n" + body[:64] + "\n" + body[64:] + "\n-----END RSA PRIVATE KEY-----\n"


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in ("SDLC_HOOKS", "SDLC_PYTHON")}
    env.update(extra)
    return env


def hook(sub, payload, cwd=None, env=None, raw=None):
    data = raw if raw is not None else json.dumps(payload).encode()
    p = subprocess.run([sys.executable, SCRIPT, sub], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       cwd=cwd or ROOT, env=env or clean_env(), timeout=120)
    out = p.stdout.decode().strip()
    return p.returncode, (json.loads(out) if out else None), p.stderr.decode()


def manual(args, cwd):
    p = subprocess.run([sys.executable, SCRIPT] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                       env=clean_env(), timeout=120)
    return p.returncode, p.stdout.decode()


def denied(result):
    out = result[1]
    return bool(out) and out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def reason(result):
    return result[1]["hookSpecificOutput"]["permissionDecisionReason"]


class RepoCase(unittest.TestCase):
    """Each test gets a fresh git repo on branch main with one commit."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="sdlc-hooks-")
        self.outside = tempfile.mkdtemp(prefix="sdlc-out-")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        self.write("README.md", "hello\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)
        shutil.rmtree(self.outside, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git"] + list(args), cwd=self.repo, check=True, env=clean_env(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return path

    def config(self, cfg):
        self.write(".sdlc/gates.json", json.dumps(cfg))

    def write_call(self, rel, content, tool="Write"):
        ti = {"file_path": os.path.join(self.repo, rel), "content": content}
        return hook("pre-write", {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti,
                                  "cwd": self.repo, "session_id": "s1"})

    def bash(self, command, session="s1"):
        return hook("pre-bash", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                 "tool_input": {"command": command}, "cwd": self.repo, "session_id": session})

    def counter_gate(self, name, kind, on, code=0, text="ok"):
        """A gate whose command appends to a counter file outside the repo, prints text and exits with code."""
        counter = os.path.join(self.outside, name + ".count").replace("\\", "/")
        prog = "open(%r,'a').write('x'); print(%r); raise SystemExit(%d)" % (counter, text, code)
        return {"name": name, "kind": kind, "on": on, "cmd": '"%s" -c "%s"' % (PY, prog)}, counter

    @staticmethod
    def runs(counter):
        try:
            with open(counter) as f:
                return len(f.read())
        except OSError:
            return 0


class SecretGuardTest(RepoCase):
    def test_anthropic_key_denied_with_type_and_line_only(self):
        key = anthropic_key()
        r = self.write_call("app/config.py", "a = 1\nb = 2\nKEY = '%s'\n" % key)
        self.assertTrue(denied(r))
        self.assertIn("Anthropic API key at line 3", reason(r))
        self.assertNotIn(key, reason(r))
        self.assertNotIn(key[10:30], reason(r))

    def test_private_key_block_denied(self):
        r = self.write_call("deploy/id.txt", "x\n" + pem_block())
        self.assertTrue(denied(r))
        self.assertIn("private key block at line 2", reason(r))

    def test_aws_and_generic_assignment_denied(self):
        self.assertTrue(denied(self.write_call("a.py", "aws = '%s'\n" % aws_key())))
        r = self.write_call("b.py", 'api_key = "%s"\n' % rnd(32))
        self.assertTrue(denied(r))
        self.assertIn("line 1", reason(r))

    def test_placeholders_allowed(self):
        content = ("ANTHROPIC_API_KEY=\nOPENAI_API_KEY=sk-...\nSECRET_KEY=changeme\n"
                   "API_TOKEN=<your-token>\nGITHUB_TOKEN=gh" + "p_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
                   "AWS=AKIAIOSFODNN7EXAMPLE\n")
        r = self.write_call(".env.example", content)
        self.assertIsNone(r[1])
        self.assertEqual(r[0], 0)

    def test_code_reading_env_allowed(self):
        content = 'api_key = os.environ["ANTHROPIC_API_KEY"]\ntoken = get_token_from_store()\npassword = settings.DB_PASSWORD\n'
        self.assertIsNone(self.write_call("c.py", content)[1])

    def test_allow_pattern_and_inline_marker(self):
        key = anthropic_key()
        self.config({"secrets": {"allow": ["FIXTURE_KEY"]}})
        self.assertIsNone(self.write_call("t.py", "FIXTURE_KEY = '%s'\n" % key)[1])
        self.assertIsNone(self.write_call("u.py", "k = '%s'  # sdlc:allow-secret\n" % key)[1])
        self.assertTrue(denied(self.write_call("v.py", "k = '%s'\n" % key)))

    def test_ignore_paths(self):
        self.config({"secrets": {"ignore_paths": ["tests/fixtures/**"]}})
        self.assertIsNone(self.write_call("tests/fixtures/keys.txt", github_token() + "\n")[1])

    def test_edit_reports_line_in_file(self):
        path = self.write("svc.py", "l1\nl2\nl3\nPLACE = None\nl5\n")
        ti = {"file_path": path, "old_string": "PLACE = None", "new_string": "PLACE = '%s'" % github_token()}
        r = hook("pre-write", {"tool_name": "Edit", "tool_input": ti, "cwd": self.repo})
        self.assertTrue(denied(r))
        self.assertIn("GitHub token at line 4", reason(r))

    def test_multiedit_and_notebook(self):
        ti = {"file_path": os.path.join(self.repo, "m.py"),
              "edits": [{"old_string": "a", "new_string": "b"}, {"old_string": "c", "new_string": "t = '%s'" % aws_key()}]}
        self.assertTrue(denied(hook("pre-write", {"tool_name": "MultiEdit", "tool_input": ti, "cwd": self.repo})))
        ti = {"notebook_path": os.path.join(self.repo, "n.ipynb"), "new_source": "k = '%s'" % anthropic_key()}
        self.assertTrue(denied(hook("pre-write", {"tool_name": "NotebookEdit", "tool_input": ti, "cwd": self.repo})))

    def test_staged_secret_blocks_commit(self):
        tok = github_token()
        self.write("ci/deploy.sh", "#!/bin/sh\nexport GH=%s\n" % tok)
        self.git("add", "ci/deploy.sh")
        r = self.bash('git commit -m "add deploy"')
        self.assertTrue(denied(r))
        self.assertIn("ci/deploy.sh line 2: GitHub token", reason(r))
        self.assertNotIn(tok, reason(r))

    def test_add_and_commit_scans_untracked(self):
        self.write("notes.txt", "k: %s\n" % anthropic_key())
        self.assertTrue(denied(self.bash("git add -A && git commit -m x")))
        self.assertIsNone(self.bash("git commit -m x")[1])  # nothing staged: staged diff is clean


class ProtectedPathTest(RepoCase):
    def test_existing_protected_file_denied_new_file_allowed(self):
        self.config({"protected": ["backend/alembic/versions/*"]})
        self.write("backend/alembic/versions/0001_init.py", "rev = '0001'\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "migration")
        r = self.write_call("backend/alembic/versions/0001_init.py", "rev = '0001'\n# changed\n")
        self.assertTrue(denied(r))
        self.assertIn("Protected path", reason(r))
        self.assertIsNone(self.write_call("backend/alembic/versions/0002_add.py", "rev = '0002'\n")[1])
        self.write("backend/alembic/versions/0003_wip.py", "rev = '0003'\n")  # exists but not committed yet
        self.assertIsNone(self.write_call("backend/alembic/versions/0003_wip.py", "rev = '0003'\n# more\n")[1])
        self.assertIsNone(self.write_call("backend/app/main.py", "x = 1\n")[1])


class CommandGuardTest(RepoCase):
    def test_force_push(self):
        self.assertTrue(denied(self.bash("git push --force origin main")))
        self.assertTrue(denied(self.bash("git push -f origin master")))
        self.assertTrue(denied(self.bash("git push origin +main")))
        self.assertTrue(denied(self.bash("git push --force-with-lease")))  # current branch is main
        self.assertTrue(denied(self.bash("cd sub && git push --force origin HEAD:main")))
        self.assertIsNone(self.bash("git push origin feature-x")[1])
        self.assertIsNone(self.bash("git push -f origin feature-x")[1])
        self.assertIsNone(self.bash("git push -u origin main")[1])

    def test_quoted_text_and_heredoc_do_not_trigger(self):
        self.assertIsNone(self.bash('git commit -m "docs: never use git push --force origin main"')[1])
        cmd = "git commit -m \"$(cat <<'EOF'\nWarn about git push --force origin main and cat .env\nEOF\n)\""
        self.assertIsNone(self.bash(cmd)[1])
        self.assertIsNone(self.bash("echo 'cat .env'")[1])

    def test_no_verify(self):
        self.assertTrue(denied(self.bash("git commit --no-verify -m x")))
        self.assertTrue(denied(self.bash("git commit -nm x")))
        self.assertTrue(denied(self.bash("git -c core.hooksPath=/dev/null commit -m x")))
        self.assertIsNone(self.bash('git commit -m "-n is a flag"')[1])

    def test_git_add_secret_files(self):
        self.assertTrue(denied(self.bash("git add backend/.env")))
        self.assertTrue(denied(self.bash("git add storage/secret.key")))
        self.assertIsNone(self.bash("git add .env.example")[1])
        self.write(".env", "A=1\n")
        self.assertTrue(denied(self.bash("git add -A")))
        self.assertTrue(denied(self.bash("git add .")))
        self.write(".gitignore", ".env\n")
        self.assertIsNone(self.bash("git add -A")[1])

    def test_print_secret_files(self):
        self.assertTrue(denied(self.bash("cat backend/.env")))
        self.assertTrue(denied(self.bash("head -n 3 storage/secret.key")))
        self.assertTrue(denied(self.bash('powershell -Command "Get-Content .env"')))
        self.assertTrue(denied(self.bash("bash -c 'type .env.production'")))
        self.assertTrue(denied(self.bash("ls && grep KEY backend/.env")))
        self.assertIsNone(self.bash("cat .env.example")[1])
        self.assertIsNone(self.bash("cat README.md")[1])


class GateTest(RepoCase):
    def test_no_config_does_nothing(self):
        r = self.bash("git commit -m x")
        self.assertEqual(r[0], 0)
        self.assertIsNone(r[1])

    def test_failing_gate_denies_commit_with_short_summary(self):
        ok, _ = self.counter_gate("lint", "lint", ["commit"])
        bad, _ = self.counter_gate("unit-tests", "unit", ["commit"], code=1, text="AssertionError: boom")
        self.config({"gates": [ok, bad]})
        r = self.bash("git commit -m x")
        self.assertTrue(denied(r))
        text = reason(r)
        self.assertIn("unit-tests (unit, exit 1", text)
        self.assertIn("AssertionError: boom", text)
        self.assertIn("Passed: lint", text)
        self.assertLess(len(text.splitlines()), 30)

    def test_long_output_is_tailed(self):
        prog = "print('\\n'.join('line%d' % i for i in range(500))); raise SystemExit(2)"
        self.config({"gates": [{"name": "noisy", "kind": "unit", "on": ["commit"], "cmd": '"%s" -c "%s"' % (PY, prog)}]})
        text = reason(self.bash("git commit -m x"))
        self.assertIn("line499", text)
        self.assertNotIn("line400\n", text)
        self.assertLessEqual(sum(1 for ln in text.splitlines() if ln.startswith("line")), 20)

    def test_passing_gates_one_line_and_session_cache(self):
        a, ca = self.counter_gate("backend-tests", "unit", ["commit"])
        b, cb = self.counter_gate("types", "types", ["commit"])
        self.config({"gates": [a, b]})
        r = self.bash("git commit -m x")
        ctx = r[1]["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", ctx)
        self.assertEqual(ctx["additionalContext"], "gates passed: backend-tests, types")
        r = self.bash("git commit -m x")
        self.assertEqual(r[1]["hookSpecificOutput"]["additionalContext"],
                         "gates passed: backend-tests (cached), types (cached)")
        self.assertEqual((self.runs(ca), self.runs(cb)), (1, 1))
        self.bash("git commit -m x", session="s2")  # another session reruns non-e2e gates
        self.assertEqual(self.runs(ca), 2)
        self.write("src.py", "x = 2\n")  # changed tree reruns
        self.bash("git commit -m x")
        self.assertEqual(self.runs(ca), 3)

    def test_failures_are_not_cached(self):
        bad, c = self.counter_gate("unit", "unit", ["commit"], code=1)
        self.config({"gates": [bad]})
        self.bash("git commit -m x")
        self.bash("git commit -m x")
        self.assertEqual(self.runs(c), 2)

    def test_e2e_stamp_skips_push_gate_until_tree_changes(self):
        e2e, c = self.counter_gate("e2e", "e2e", ["push"])
        self.config({"gates": [e2e]})
        code, out = manual(["stamp", "e2e"], self.repo)
        self.assertEqual(code, 0)
        self.assertIn("stamped e2e", out)
        r = self.bash("git push origin main", session="other")
        self.assertEqual(r[1]["hookSpecificOutput"]["additionalContext"], "gates passed: e2e (cached)")
        self.assertEqual(self.runs(c), 0)
        self.write("app.js", "console.log(1)\n")
        self.bash("git push origin main", session="other")
        self.assertEqual(self.runs(c), 1)

    def test_stamp_survives_commit_of_same_content(self):
        e2e, c = self.counter_gate("e2e", "e2e", ["push"])
        self.config({"gates": [e2e]})
        self.write("app.js", "console.log(1)\n")
        manual(["stamp", "e2e"], self.repo)
        self.git("add", "app.js")
        self.git("commit", "-q", "-m", "app")
        self.write(".sdlc/log.md", "## entry\n")  # .sdlc changes do not invalidate the stamp
        self.bash("git push origin main")
        self.assertEqual(self.runs(c), 0)

    def test_push_dry_run_and_commit_only_gates(self):
        e2e, c = self.counter_gate("e2e", "e2e", ["push"])
        self.config({"gates": [e2e]})
        self.assertIsNone(self.bash("git commit -m x")[1])
        self.assertIsNone(self.bash("git push --dry-run origin main")[1])
        self.assertEqual(self.runs(c), 0)

    def test_check_subcommand_prints_only_failures(self):
        bad, _ = self.counter_gate("unit", "unit", ["commit"], code=1, text="FAILED test_x")
        self.config({"gates": [bad]})
        code, out = manual(["check", "commit"], self.repo)
        self.assertEqual(code, 1)
        self.assertIn("FAILED test_x", out)


class StopGateTest(RepoCase):
    def stop(self, active=False):
        return hook("stop", {"hook_event_name": "Stop", "session_id": "s1", "cwd": self.repo,
                             "stop_hook_active": active})

    def start(self):
        return hook("session-start", {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": self.repo,
                                      "source": "startup"})

    def test_unchanged_session_runs_nothing(self):
        g, c = self.counter_gate("unit", "unit", ["stop"], code=1)
        self.config({"gates": [g]})
        self.start()
        self.assertIsNone(self.stop()[1])
        self.assertEqual(self.runs(c), 0)

    def test_failing_stop_gate_blocks_then_loop_guard_allows(self):
        g, c = self.counter_gate("unit", "unit", ["stop"], code=1, text="1 failed")
        self.config({"gates": [g]})
        self.start()
        self.write("src.py", "broken = True\n")
        r = self.stop()
        self.assertEqual(r[1]["decision"], "block")
        self.assertIn("1 failed", r[1]["reason"])
        self.assertEqual(self.stop(active=True)[1]["decision"], "block")
        self.assertIsNone(self.stop(active=True)[1])  # third time: let the agent stop
        self.assertEqual(self.runs(c), 2)

    def test_passing_stop_gate_not_rerun_on_same_tree(self):
        g, c = self.counter_gate("unit", "unit", ["stop"])
        self.config({"gates": [g]})
        self.start()
        self.write("src.py", "ok = True\n")
        self.assertIsNone(self.stop()[1])
        self.assertIsNone(self.stop()[1])
        self.assertEqual(self.runs(c), 1)


class SessionStartTest(RepoCase):
    def start(self):
        return hook("session-start", {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": self.repo,
                                      "source": "startup"})

    def test_empty_repo_prints_nothing(self):
        r = self.start()
        self.assertEqual(r[0], 0)
        self.assertIsNone(r[1])

    def test_log_and_gates_summarized_compactly(self):
        log = "# Log\n\n## 2026-01-01 10:00 old\n- Result: done\n\n## 2026-01-02 11:00 change-a\n" + "".join(
            "- line %d\n" % i for i in range(30))
        self.write(".sdlc/log.md", log)
        bad, _ = self.counter_gate("unit", "unit", ["commit"], code=1)
        self.config({"gates": [bad]})
        self.bash("git commit -m x")
        r = self.start()
        text = r[1]["hookSpecificOutput"]["additionalContext"]
        self.assertIn("2026-01-02 11:00 change-a", text)
        self.assertNotIn("old", text)
        self.assertIn("FAILED unit", text)
        self.assertLessEqual(len(text.splitlines()), 15)
        root_file = os.path.join(self.repo, ".sdlc", "state", "plugin_root")
        with open(root_file) as f:
            self.assertTrue(f.read().strip().endswith(os.path.basename(ROOT)))


class PostWriteTest(RepoCase):
    def test_formatter_runs_silently_on_matching_file(self):
        marker = os.path.join(self.outside, "formatted").replace("\\", "/")
        prog = "import sys; open(%r,'w').write(sys.argv[1])" % marker
        self.config({"format": [{"glob": "backend/**/*.py", "cmd": '"%s" -c "%s" {file}' % (PY, prog)}]})
        path = self.write("backend/app/x.py", "x=1\n")
        r = hook("post-write", {"tool_name": "Edit", "tool_input": {"file_path": path}, "cwd": self.repo})
        self.assertIsNone(r[1])
        self.assertEqual(r[2], "")
        with open(marker) as f:
            self.assertTrue(f.read().endswith("backend/app/x.py"))

    def test_non_matching_file_does_nothing(self):
        marker = os.path.join(self.outside, "formatted").replace("\\", "/")
        prog = "open(%r,'w').write('x')" % marker
        self.config({"format": [{"glob": "backend/**/*.py", "cmd": '"%s" -c "%s"' % (PY, prog)}]})
        path = self.write("frontend/a.ts", "x\n")
        hook("post-write", {"tool_name": "Write", "tool_input": {"file_path": path}, "cwd": self.repo})
        self.assertFalse(os.path.exists(marker))


class FailOpenTest(RepoCase):
    def test_off_switch(self):
        r = hook("pre-bash", {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"},
                              "cwd": self.repo}, env=clean_env(SDLC_HOOKS="off"))
        self.assertIsNone(r[1])

    def test_bad_json_fails_open_with_warning(self):
        r = hook("pre-write", None, cwd=self.repo, raw=b"not json")
        self.assertEqual(r[0], 0)
        self.assertIsNone(r[1])
        self.assertIn("skipped", r[2])
        r = hook("stop", None, cwd=self.repo, raw=b"not json")
        self.assertEqual((r[0], r[1], r[2]), (0, None, ""))

    @unittest.skipUnless(shutil.which("sh"), "needs sh")
    def test_shim_runs_and_honors_off(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"},
                              "cwd": self.repo}).encode()
        for env, expect in ((clean_env(), True), (clean_env(SDLC_HOOKS="off"), False)):
            p = subprocess.run(["sh", SHIM.replace("\\", "/"), "pre-bash"], input=payload, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env, timeout=60)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(b"deny" in p.stdout, expect, p.stderr)

    @unittest.skipUnless(shutil.which("sh"), "needs sh")
    def test_shim_fast_paths(self):
        def shim(sub, payload, **env):
            p = subprocess.run(["sh", SHIM.replace("\\", "/"), sub], input=json.dumps(payload).encode(),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=clean_env(**env), timeout=60)
            return p.returncode, p.stdout
        self.assertEqual(shim("pre-bash", {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}), (0, b""))
        code, out = shim("pre-bash", {"tool_name": "Bash", "tool_input": {"command": "cat .env"}, "cwd": self.repo})
        self.assertIn(b"deny", out)
        self.assertEqual(shim("stop", {"session_id": "s", "cwd": self.repo}, CLAUDE_PROJECT_DIR=self.repo), (0, b""))
        self.assertEqual(shim("post-write", {"tool_input": {"file_path": "x"}}, CLAUDE_PROJECT_DIR=self.repo), (0, b""))

    @unittest.skipUnless(shutil.which("sh"), "needs sh")
    def test_shim_without_python_fails_open(self):
        payload = b'{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}'
        env = clean_env(PATH=os.path.dirname(shutil.which("sh")))
        p = subprocess.run([shutil.which("sh"), SHIM.replace("\\", "/"), "pre-bash"], input=payload,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"")


class InitGatesTest(RepoCase):
    CLAUDE = """# CLAUDE.md

## Commands

| Purpose | Command | **Check?** |
|---|---|---|
| Start database | `docker compose up -d` | no |
| Backend tests | `cd backend && .venv/Scripts/python -m pytest` | yes |
| Backend lint | `cd backend && ruff check . && ruff format --check .` | yes |
| Backend types | `cd backend && mypy app` | yes |
| Frontend build + types | `cd frontend && npm run build` | yes |
| Grep check | `rg foo \\| wc -l` | yes |
| Frontend e2e (UI) | `cd frontend && npm run e2e` (Edge; own backend) | yes |

## UI
"""

    def test_generates_gates_from_checks_and_skips_existing(self):
        self.write("CLAUDE.md", self.CLAUDE)
        code, out = manual(["init-gates"], self.repo)
        self.assertEqual(code, 0, out)
        with open(os.path.join(self.repo, ".sdlc", "gates.json")) as f:
            cfg = json.load(f)
        got = {g["name"]: (g["kind"], g["on"], g["cmd"]) for g in cfg["gates"]}
        self.assertEqual(got["backend-tests"], ("unit", ["commit"], "cd backend && .venv/Scripts/python -m pytest"))
        self.assertEqual(got["backend-lint"][0], "lint")
        self.assertEqual(got["backend-types"][0], "types")
        self.assertEqual(got["frontend-build-types"][0], "build")
        self.assertEqual(got["frontend-e2e"], ("e2e", ["push"], "cd frontend && npm run e2e"))
        self.assertEqual(got["grep-check"][2], "rg foo | wc -l")
        self.assertNotIn("start-database", got)
        with open(os.path.join(self.repo, ".gitignore")) as f:
            self.assertIn(".sdlc/state/", f.read())
        code, out = manual(["init-gates"], self.repo)
        self.assertIn("skipped", out)


class HooksJsonTest(unittest.TestCase):
    def test_hooks_json_references_known_subcommands(self):
        with open(os.path.join(ROOT, "hooks", "hooks.json")) as f:
            cfg = json.load(f)
        subs = set()
        for event, groups in cfg["hooks"].items():
            for g in groups:
                for h in g["hooks"]:
                    self.assertEqual(h["type"], "command")
                    self.assertIn('"${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"', h["command"])
                    subs.add(h["command"].rsplit(" ", 1)[-1])
        self.assertEqual(subs, {"pre-write", "pre-bash", "post-write", "stop", "session-start"})
        self.assertEqual(set(cfg["hooks"]), {"SessionStart", "PreToolUse", "PostToolUse", "Stop"})


if __name__ == "__main__":
    unittest.main()
