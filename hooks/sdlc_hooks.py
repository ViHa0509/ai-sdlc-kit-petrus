#!/usr/bin/env python3
"""ai-sdlc-kit hooks: secret and command guards, quality gates, session context.

Python 3.8+ standard library only. Called by hooks/run.sh with one subcommand:

  pre-write      PreToolUse  Write|Edit|MultiEdit|NotebookEdit  secret guard, protected paths
  pre-bash       PreToolUse  Bash                               command guard, staged secrets, commit/push gates
  post-write     PostToolUse Write|Edit|MultiEdit               optional silent formatter
  stop           Stop                                           stop gates with a loop guard
  session-start  SessionStart                                   compact state summary
  stamp KIND     (manual)    record a pass for the current tree (qc-e2e: `stamp e2e`)
  check [STAGE]  (manual)    run the gates of a stage and print only failures
  init-gates     (manual)    write .sdlc/gates.json from the CLAUDE.md Commands table

Hooks fail open: any error allows the call. Output is JSON on stdout or nothing.
"""

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

CONFIG_REL = os.path.join(".sdlc", "gates.json")
STATE_REL = os.path.join(".sdlc", "state")
KINDS = ("unit", "integration", "e2e", "lint", "types", "build")
STAGES = ("commit", "push", "stop")
DEFAULT_GATE_TIMEOUT = 900
TAIL_LINES = 20
MAX_LINE = 200
MAX_STOP_BLOCKS = 2
CONTEXT_MAX_LINES = 15
SECRET_SUBCOMMANDS = ("pre-write", "pre-bash")


# --------------------------------------------------------------------------- utils


def out_json(obj):
    sys.stdout.write(json.dumps(obj))
    sys.stdout.write("\n")


def deny(reason):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def pre_context(text):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}}


def read_input():
    raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    data = json.loads(raw) if raw.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("hook input is not an object")
    return data


def run(args, cwd=None, env=None, timeout=60, input_bytes=None):
    """Run a command; return (code, stdout_text). Never raises for normal failures."""
    try:
        p = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=None if input_bytes is not None else subprocess.DEVNULL,
            timeout=timeout,
        )
        return p.returncode, p.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def git(root, *args, env=None, timeout=60):
    return run(["git"] + list(args), cwd=root, env=env, timeout=timeout)


def find_root(start):
    start = os.path.abspath(start or os.getcwd())
    d = start
    while True:
        if os.path.exists(os.path.join(d, ".git")) or os.path.isfile(os.path.join(d, CONFIG_REL)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return start
        d = parent


def load_config(root):
    path = os.path.join(root, CONFIG_REL)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        sys.stderr.write("ai-sdlc-kit: .sdlc/gates.json is not valid JSON; gates skipped\n")
        return {}


def hook_on(cfg, name):
    hooks = cfg.get("hooks") or {}
    return hooks.get(name, True) is not False


def state_dir(root, create=True):
    d = os.path.join(root, STATE_REL)
    if create and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
        try:
            with open(os.path.join(d, ".gitignore"), "w", encoding="utf-8") as f:
                f.write("*\n")
        except OSError:
            pass
    return d


def load_state(root, name, default):
    path = os.path.join(root, STATE_REL, name)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_state(root, name, value):
    d = state_dir(root)
    tmp = os.path.join(d, name + ".tmp%d" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=1)
    os.replace(tmp, os.path.join(d, name))


def rel_path(root, path):
    if not path:
        return None
    try:
        p = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))
        r = os.path.relpath(p, root)
    except ValueError:
        return None
    r = r.replace("\\", "/")
    if r.startswith("../") or r == "..":
        return None
    return r


_GLOB_CACHE = {}


def glob_match(pattern, path):
    """`*` matches within one folder, `**` across folders, `?` one char."""
    rx = _GLOB_CACHE.get(pattern)
    if rx is None:
        p = pattern.replace("\\", "/")
        out = []
        i = 0
        while i < len(p):
            if p.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif p.startswith("**", i):
                out.append(".*")
                i += 2
            elif p[i] == "*":
                out.append("[^/]*")
                i += 1
            elif p[i] == "?":
                out.append("[^/]")
                i += 1
            else:
                out.append(re.escape(p[i]))
                i += 1
        rx = re.compile("^" + "".join(out) + "$", re.I if os.name == "nt" else 0)
        _GLOB_CACHE[pattern] = rx
    return bool(rx.match(path))


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- secrets

PROVIDER_PATTERNS = [
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), 7),
    ("OpenAI API key", re.compile(r"\bsk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{20,}"), 3),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), 4),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"), 4),
    ("GitHub token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}"), 11),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"), 4),
    ("Slack token", re.compile(r"\bxox[abposre]-[A-Za-z0-9\-]{10,}"), 5),
]

GENERIC_PATTERN = re.compile(
    r"""(?ix)
    (?P<name>[A-Za-z0-9_.\-]*
      (?:api[_\-]?key|apikey|secret|token|passw(?:or)?d|pwd|private[_\-]?key|access[_\-]?key|auth[_\-]?key)
      [A-Za-z0-9_\-]*)
    ["']?\s*(?::=|=>|=|:)\s*
    (?P<q>["'`]?)(?P<val>[A-Za-z0-9_\-+/=.~!@\#%^&*]{16,})(?P=q)
    \s*(?:[,;)}\]\#]|$)
    """
)

PEM_PATTERN = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")
PEM_BODY = re.compile(r"[A-Za-z0-9+/=]{40,}")

PLACEHOLDER_WORDS = (
    "xxxx", "your", "example", "changeme", "change-me", "change_me", "placeholder", "dummy",
    "redacted", "sample", "fake", "replace", "insert", "...", "****", "<", ">", "{{", "0000000000",
    "1234567890", "abcdef",
)
ALLOW_MARKERS = ("sdlc:allow-secret", "pragma: allowlist secret")


def is_placeholder(value, prefix_len=0):
    v = value.strip().strip("\"'`")
    if not v:
        return True
    low = v.lower()
    if any(w in low for w in PLACEHOLDER_WORDS):
        return True
    body = low[prefix_len:] if prefix_len < len(low) else low
    if len(set(body)) < 6:
        return True
    return False


def entropy(value):
    counts = {}
    for c in value:
        counts[c] = counts.get(c, 0) + 1
    n = float(len(value))
    return -sum(k / n * math.log(k / n, 2) for k in counts.values())


def generic_is_secret(value):
    if value.startswith("$") or is_placeholder(value):
        return False
    if not (re.search(r"[A-Za-z]", value) and re.search(r"[0-9]", value)):
        return False
    return entropy(value) >= 3.3


def scan_text(text, allow=()):
    """Return [(type, line_number)] for likely secrets in text. Never returns secret text."""
    findings = []
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if any(m in low for m in ALLOW_MARKERS):
            continue
        if any(rx.search(line) for rx in allow):
            continue
        hit = None
        for name, rx, plen in PROVIDER_PATTERNS:
            for m in rx.finditer(line):
                val = m.group(0)
                if is_placeholder(val, plen):
                    continue
                if name == "OpenAI API key" and not (re.search(r"[0-9]", val[3:]) and re.search(r"[A-Za-z]", val[3:])):
                    continue
                hit = name
                break
            if hit:
                break
        if not hit:
            for m in GENERIC_PATTERN.finditer(line):
                if generic_is_secret(m.group("val")):
                    hit = "secret value assigned to " + ("a password" if re.search(r"(?i)passw|pwd", m.group("name")) else "a key/token name")
                    break
        if hit:
            findings.append((hit, i))
    for m in PEM_PATTERN.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        line = lines[line_no - 1] if line_no - 1 < len(lines) else ""
        if any(mk in line.lower() for mk in ALLOW_MARKERS) or any(rx.search(line) for rx in allow):
            continue
        if PEM_BODY.search(text[m.end(): m.end() + 400]):
            findings.append(("private key block", line_no))
    findings.sort(key=lambda f: f[1])
    return findings


def secret_settings(cfg):
    s = cfg.get("secrets") or {}
    allow = []
    for p in s.get("allow") or []:
        try:
            allow.append(re.compile(p))
        except re.error:
            pass
    return allow, list(s.get("ignore_paths") or [])


def format_findings(findings, limit=5):
    parts = ["%s at line %d" % (t, n) for t, n in findings[:limit]]
    more = len(findings) - limit
    if more > 0:
        parts.append("%d more" % more)
    return "; ".join(parts)


# --------------------------------------------------------------------------- pre-write


def new_contents(tool, ti, path):
    """Yield (text, line_offset) for the new content of a write-like tool call."""
    if tool == "Write":
        yield ti.get("content") or "", 0
    elif tool == "Edit":
        yield ti.get("new_string") or "", edit_offset(path, ti.get("old_string"))
    elif tool == "MultiEdit":
        for e in ti.get("edits") or []:
            if isinstance(e, dict):
                yield e.get("new_string") or "", edit_offset(path, e.get("old_string"))
    elif tool == "NotebookEdit":
        yield ti.get("new_source") or "", 0
    else:
        for key in ("content", "new_string", "new_source"):
            if isinstance(ti.get(key), str):
                yield ti[key], 0


def edit_offset(path, old):
    if not path or not old:
        return 0
    try:
        if os.path.getsize(path) > 5_000_000:
            return 0
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        idx = content.find(old)
        return content.count("\n", 0, idx) if idx > 0 else 0
    except OSError:
        return 0


def is_committed(root, rel):
    """True when rel is in HEAD; outside a git repo (or without commits) every existing file counts."""
    code, _ = git(root, "rev-parse", "--verify", "-q", "HEAD", timeout=10)
    if code != 0:
        return True
    code, _ = git(root, "cat-file", "-e", "HEAD:" + rel, timeout=10)
    return code == 0


def pre_write(data):
    ti = data.get("tool_input") or {}
    tool = data.get("tool_name") or ""
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    cwd = data.get("cwd") or os.getcwd()
    root = find_root(cwd)
    cfg = load_config(root)
    rel = rel_path(root, path)
    shown = rel or os.path.basename(path) or "file"

    if hook_on(cfg, "protected") and rel and cfg.get("protected"):
        abs_path = path if os.path.isabs(path) else os.path.join(root, path)
        pats = [p for p in cfg.get("protected") or [] if glob_match(p, rel)]
        if pats and os.path.exists(abs_path) and is_committed(root, rel):
            return deny(
                "Protected path: %s matches '%s' in .sdlc/gates.json and is already committed, so it must not "
                "be changed. Create a new file instead (for example a new migration)." % (rel, pats[0])
            )

    if hook_on(cfg, "secrets"):
        allow, ignore = secret_settings(cfg)
        if rel and any(glob_match(p, rel) for p in ignore):
            return None
        findings = []
        for text, offset in new_contents(tool, ti, path):
            findings += [(t, n + offset) for t, n in scan_text(text, allow)]
        if findings:
            return deny(
                "Secret guard: the new content of %s looks like it contains a secret (%s). Do not write keys "
                "into files: read them from the environment or the app's secret store. If this is a false "
                "positive, ask the user to add a secrets.allow pattern in .sdlc/gates.json."
                % (shown, format_findings(findings))
            )
    return None


# --------------------------------------------------------------------------- shell parsing

HEREDOC = re.compile(r"(<<-?[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2)([^\n]*)\n.*?\n[ \t]*\3[ \t]*(?=\n|$)", re.S)
WRAPPERS = ("sudo", "env", "command", "exec", "time", "nohup", "builtin", "xargs")
SHELLS = {"bash": "-c", "sh": "-c", "zsh": "-c", "dash": "-c", "powershell": "-command", "pwsh": "-command",
          "cmd": "/c"}


def strip_heredocs(cmd):
    prev = None
    while prev != cmd:
        prev = cmd
        cmd = HEREDOC.sub(lambda m: m.group(1) + m.group(4), cmd, count=1)
    return cmd


def split_commands(cmd):
    """Quote-aware split into simple commands (lists of words)."""
    cmds, words, cur = [], [], []
    has = False
    quote = None
    i, n = 0, len(cmd)

    def flush_word():
        nonlocal cur, has
        if has:
            words.append("".join(cur))
        cur, has = [], False

    def flush_cmd():
        nonlocal words
        flush_word()
        if words:
            cmds.append(words)
        words = []

    while i < n:
        c = cmd[i]
        if quote == "'":
            if c == "'":
                quote = None
            else:
                cur.append(c)
            i += 1
            continue
        if quote == '"':
            if c == "\\" and i + 1 < n and cmd[i + 1] in '"\\$`':
                cur.append(cmd[i + 1])
                i += 2
                continue
            if c == '"':
                quote = None
            else:
                cur.append(c)
            i += 1
            continue
        if c in "'\"":
            quote = c
            has = True
        elif c == "\\" and i + 1 < n:
            if cmd[i + 1] != "\n":
                cur.append(cmd[i + 1])
                has = True
            i += 2
            continue
        elif c in " \t\r":
            flush_word()
        elif c in ";&|\n()`":
            flush_cmd()
        elif c == "#" and not has:
            while i < n and cmd[i] != "\n":
                i += 1
            continue
        else:
            cur.append(c)
            has = True
        i += 1
    flush_cmd()
    return cmds


def base_cmd(word):
    w = word.replace("\\", "/").rsplit("/", 1)[-1].lower()
    for ext in (".exe", ".cmd", ".bat"):
        if w.endswith(ext):
            w = w[: -len(ext)]
    return w


def simple_commands(cmd, depth=0):
    """Yield word lists, unwrapping env assignments, sudo-like wrappers and `bash -c '...'`."""
    for words in split_commands(strip_heredocs(cmd)):
        while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or base_cmd(words[0]) in WRAPPERS):
            words = words[1:]
        if not words:
            continue
        b = base_cmd(words[0])
        flag = SHELLS.get(b)
        if flag and depth < 3:
            for j, w in enumerate(words[1:], 1):
                if w.lower() == flag and j + 1 < len(words):
                    for inner in simple_commands(words[j + 1], depth + 1):
                        yield inner
                    break
            else:
                yield words
            continue
        yield words


def git_parts(words):
    """For a git command return (global_opts, subcommand, args) or None."""
    if not words or base_cmd(words[0]) != "git":
        return None
    opts = []
    i = 1
    while i < len(words):
        w = words[i]
        if w in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            opts.append((w, words[i + 1] if i + 1 < len(words) else ""))
            i += 2
            continue
        if w.startswith("-"):
            opts.append((w, ""))
            i += 1
            continue
        return opts, w, words[i + 1:]
    return opts, None, []


SAFE_ENV_SUFFIXES = ("example", "sample", "template", "dist", "defaults")
READERS = {"cat", "type", "more", "less", "head", "tail", "get-content", "gc", "bat", "nl", "xxd", "od",
           "base64", "strings", "grep", "egrep", "rg", "awk", "sed", "findstr", "select-string", "sls"}


def is_secret_file(path):
    name = path.strip("\"'").replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()
    if name == ".env":
        return True
    if name.startswith(".env."):
        return name[5:] not in SAFE_ENV_SUFFIXES
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return name in ("id_rsa", "id_ed25519", "id_ecdsa", "id_dsa")


def current_branch(cwd):
    code, out = git(cwd, "rev-parse", "--abbrev-ref", "HEAD", timeout=10)
    return out.strip() if code == 0 else ""


def check_push(args, cwd):
    force = False
    positional = []
    whole = False
    for a in args:
        if a in ("--force", "-f", "--force-with-lease", "--force-if-includes", "--mirror") or a.startswith(
            "--force-with-lease="
        ):
            force = True
            whole = whole or a == "--mirror"
        elif a in ("--all", "--branches"):
            whole = True
        elif re.match(r"^-[A-Za-z]+$", a) and "f" in a[1:]:
            force = True
        elif a.startswith("-"):
            continue
        else:
            positional.append(a)
    refspecs = positional[1:]
    if any(r.startswith("+") for r in refspecs):
        force = True
    if not force:
        return None
    protected = ("main", "master")
    hit = whole
    for r in refspecs:
        dst = r.lstrip("+").split(":")[-1]
        if dst.startswith("refs/heads/"):
            dst = dst[len("refs/heads/"):]
        if dst == "HEAD" or dst == "":
            dst = current_branch(cwd)
        if dst in protected:
            hit = True
    if not refspecs and current_branch(cwd) in protected:
        hit = True
    if hit:
        return ("Command guard: force-pushing to main/master is not allowed (it rewrites shared history). "
                "Push a new commit instead, or push the work to another branch.")
    return None


def commit_skips_hooks(opts, args):
    for k, v in opts:
        if k == "-c" and v.lower().replace(" ", "").startswith("core.hookspath"):
            return True
    for a in args:
        if a == "--no-verify":
            return True
        if re.match(r"^-[A-Za-z]+$", a) and "n" in a[1:]:
            before = a[1: a.index("n")]
            if not any(ch in "mFCct" for ch in before):
                return True
    return False


def changed_secret_files(cwd, paths):
    code, out = git(cwd, "ls-files", "-z", "--others", "--modified", "--exclude-standard", "--", *paths, timeout=30)
    if code != 0:
        return []
    return [p for p in out.split("\0") if p and is_secret_file(p)]


def check_add(args, cwd):
    bulk = False
    targets = []
    for a in args:
        if a in ("-A", "--all", "--no-ignore-removal"):
            bulk = True
        elif a.startswith("-"):
            continue
        else:
            targets.append(a)
    named = [t for t in targets if is_secret_file(t)]
    if named:
        return "Command guard: do not stage secret files (%s). Keep them git-ignored." % ", ".join(
            os.path.basename(t) for t in named[:3])
    dirs = [t for t in targets if t in (".", ":/", "*") or os.path.isdir(os.path.join(cwd, t))]
    if bulk or dirs:
        found = changed_secret_files(cwd, [] if bulk else dirs)
        if found:
            return ("Command guard: this add would stage secret files that are not git-ignored (%s). "
                    "Add them to .gitignore, or stage files by name." % ", ".join(found[:3]))
    return None


def check_print(words):
    if base_cmd(words[0]) not in READERS:
        return None
    for a in words[1:]:
        if a.startswith("-") and not is_secret_file(a):
            continue
        if is_secret_file(a.split("=", 1)[-1]):
            return ("Command guard: do not print secret files (%s); their values would enter the conversation "
                    "and logs. Ask the user to check the file, or read only the variable names they need." %
                    os.path.basename(a.strip("\"'").replace("\\", "/")))
    return None


# --------------------------------------------------------------------------- diff scanning


def scan_diff(diff, allow, ignore):
    findings = []
    path = None
    lineno = 0
    added = []

    def flush():
        if path and added and not any(glob_match(p, path) for p in ignore):
            text = "\n".join(t for _, t in added)
            for kind, idx in scan_text(text, allow):
                findings.append((path, added[idx - 1][0], kind))

    for line in diff.split("\n"):
        if line.startswith("+++ "):
            flush()
            added = []
            p = line[4:].strip()
            path = p[2:] if p.startswith("b/") else (None if p == "/dev/null" else p)
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++"):
            added.append((lineno, line[1:]))
            lineno += 1
    flush()
    return findings


def untracked_findings(root, allow, ignore):
    code, out = git(root, "ls-files", "-z", "--others", "--exclude-standard", timeout=30)
    findings = []
    if code != 0:
        return findings
    for p in out.split("\0"):
        if not p or any(glob_match(g, p) for g in ignore):
            continue
        full = os.path.join(root, p)
        try:
            if os.path.getsize(full) > 1_000_000:
                continue
            with open(full, "rb") as f:
                raw = f.read()
        except OSError:
            continue
        if b"\0" in raw:
            continue
        for kind, n in scan_text(raw.decode("utf-8", "replace"), allow):
            findings.append((p, n, kind))
    return findings


def staged_secrets(root, cfg, wide):
    allow, ignore = secret_settings(cfg)
    findings = []
    code, diff = git(root, "diff", "--cached", "-U0", "--no-color", "--no-ext-diff", timeout=60)
    if code == 0:
        findings += scan_diff(diff, allow, ignore)
    if wide:
        code, diff = git(root, "diff", "-U0", "--no-color", "--no-ext-diff", timeout=60)
        if code == 0:
            findings += scan_diff(diff, allow, ignore)
        findings += untracked_findings(root, allow, ignore)
    seen, uniq = set(), []
    for f in findings:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


# --------------------------------------------------------------------------- gates


def tree_hash(root):
    """Content hash of the working tree (git-ignored files and .sdlc/ excluded), or None."""
    code, idx = git(root, "rev-parse", "--git-path", "index", timeout=10)
    if code != 0:
        return None
    idx = idx.strip()
    if not os.path.isabs(idx):
        idx = os.path.join(root, idx)
    tmp = os.path.join(state_dir(root), "index-%d.tmp" % os.getpid())
    try:
        if os.path.isfile(idx):
            shutil.copyfile(idx, tmp)
        env = dict(os.environ, GIT_INDEX_FILE=tmp)
        code, _ = git(root, "add", "-A", "--", ".", ":(exclude).sdlc", env=env, timeout=120)
        if code != 0:
            return None
        git(root, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", ".sdlc", env=env, timeout=60)
        code, out = git(root, "write-tree", env=env, timeout=60)
        return out.strip() if code == 0 and out.strip() else None
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def find_shell():
    for name in ("sh", "bash"):
        p = shutil.which(name)
        if p and not re.search(r"(?i)[\\/](system32|windowsapps)[\\/]", p):
            return p
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), r"C:\Program Files (x86)"):
            p = os.path.join(base, "Git", "bin", "bash.exe")
            if os.path.isfile(p):
                return p
    return None


def gates_for(cfg, stage):
    out = []
    for g in cfg.get("gates") or []:
        if not isinstance(g, dict) or not g.get("cmd"):
            continue
        on = g.get("on") or ["commit"]
        if isinstance(on, str):
            on = [on]
        if stage in on:
            g = dict(g)
            g.setdefault("name", g["cmd"][:30])
            g.setdefault("kind", "unit")
            out.append(g)
    return out


def run_gate(root, gate):
    shell = find_shell()
    timeout = gate.get("timeout") or DEFAULT_GATE_TIMEOUT
    start = time.time()
    try:
        args = [shell, "-c", gate["cmd"]] if shell else gate["cmd"]
        p = subprocess.run(args, shell=not shell, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, timeout=timeout)
        code, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        code, out = 124, (e.stdout or b"") + (b"\n[timed out after %ds]" % int(timeout))
    except OSError as e:
        code, out = 127, str(e).encode()
    return code, strip_ansi(out.decode("utf-8", "replace")), time.time() - start


def is_cached(cache, gate, tree, session):
    if not tree:
        return False
    csha = sha(gate["cmd"])
    for e in cache:
        if e.get("tree") != tree:
            continue
        if gate.get("kind") == "e2e":
            if e.get("cmd") == csha or (e.get("cmd") is None and e.get("kind") == "e2e"):
                return True
        elif e.get("cmd") == csha and e.get("session") == session:
            return True
    return False


def record_pass(root, cache, gate_name, kind, cmd, tree, session):
    cache.append({"gate": gate_name, "kind": kind, "cmd": sha(cmd) if cmd else None, "tree": tree,
                  "session": session, "time": int(time.time())})
    del cache[:-100]
    save_state(root, "cache.json", cache)


def run_gates(root, cfg, stage, session):
    gates = gates_for(cfg, stage)
    if not gates:
        return None
    tree = tree_hash(root)
    cache = load_state(root, "cache.json", [])
    if not isinstance(cache, list):
        cache = []
    results = []
    for g in gates:
        if is_cached(cache, g, tree, session):
            results.append({"name": g["name"], "kind": g["kind"], "status": "cached"})
            continue
        code, out, secs = run_gate(root, g)
        if code == 0:
            results.append({"name": g["name"], "kind": g["kind"], "status": "pass", "secs": round(secs)})
            if tree:
                record_pass(root, cache, g["name"], g["kind"], g["cmd"], tree, session)
        else:
            tail = [ln[:MAX_LINE] for ln in out.rstrip().split("\n")[-TAIL_LINES:]]
            results.append({"name": g["name"], "kind": g["kind"], "status": "fail", "code": code,
                            "secs": round(secs), "tail": tail})
    save_state(root, "last-gates.json", {
        "stage": stage, "time": int(time.time()), "tree": tree,
        "results": [{k: v for k, v in r.items() if k != "tail"} for r in results],
    })
    return results


def passed_line(results):
    ok = [r["name"] + (" (cached)" if r["status"] == "cached" else "") for r in results if r["status"] != "fail"]
    return "gates passed: " + ", ".join(ok)


def failure_summary(stage, results):
    failed = [r for r in results if r["status"] == "fail"]
    head = "%s blocked: %s failed (.sdlc/gates.json)." % (
        stage.capitalize(), ", ".join("%s (%s, exit %s, %ss)" % (r["name"], r["kind"], r["code"], r["secs"])
                                      for r in failed))
    parts = [head]
    for r in failed:
        parts.append("--- %s: last %d lines ---" % (r["name"], len(r["tail"])))
        parts.extend(r["tail"])
    ok = [r["name"] for r in results if r["status"] != "fail"]
    if ok:
        parts.append("Passed: " + ", ".join(ok) + ".")
    parts.append("Fix the failures, then retry. Do not bypass or weaken the gates or the tests.")
    return "\n".join(parts)


# --------------------------------------------------------------------------- pre-bash


def pre_bash(data):
    ti = data.get("tool_input") or {}
    command = ti.get("command") or ""
    if not command.strip():
        return None
    cwd = data.get("cwd") or os.getcwd()
    root = find_root(cwd)
    cfg = load_config(root)
    session = data.get("session_id") or ""

    cmds = list(simple_commands(command))
    commit, push, adds_files = None, None, False
    for words in cmds:
        if hook_on(cfg, "commands"):
            reason = check_print(words)
            if reason:
                return deny(reason)
        parts = git_parts(words)
        if not parts or not parts[1]:
            continue
        opts, sub, args = parts
        gcwd = cwd
        for k, v in opts:
            if k == "-C" and v:
                gcwd = v if os.path.isabs(v) else os.path.join(gcwd, v)
        if sub == "push":
            push = args
            if hook_on(cfg, "commands"):
                reason = check_push(args, gcwd)
                if reason:
                    return deny(reason)
        elif sub == "commit":
            commit = args
            if hook_on(cfg, "commands") and commit_skips_hooks(opts, args):
                return deny("Command guard: skipping git hooks (--no-verify, -n, core.hooksPath) is not allowed. "
                            "Let the checks run and fix what they report.")
        elif sub == "add":
            adds_files = True
            if hook_on(cfg, "commands"):
                reason = check_add(args, gcwd)
                if reason:
                    return deny(reason)
        elif sub == "stage":
            adds_files = True

    if commit is not None and hook_on(cfg, "secrets"):
        wide = adds_files or any(a in ("-a", "--all") or re.match(r"^-[A-Za-z]*a[A-Za-z]*$", a) for a in commit)
        findings = staged_secrets(root, cfg, wide)
        if findings:
            listed = "; ".join("%s line %d: %s" % f for f in findings[:5])
            return deny("Secret guard: the commit would add likely secrets (%s). Remove them and read the values "
                        "from the environment or the app's secret store. If this is a false positive, ask the "
                        "user to add a secrets.allow pattern in .sdlc/gates.json." % listed)

    if not hook_on(cfg, "gates") or not cfg.get("gates"):
        return None
    stages = []
    if commit is not None:
        stages.append("commit")
    if push is not None and "--dry-run" not in push and "-n" not in push:
        stages.append("push")
    lines = []
    for stage in stages:
        results = run_gates(root, cfg, stage, session)
        if not results:
            continue
        if any(r["status"] == "fail" for r in results):
            return deny(failure_summary(stage, results))
        lines.append(passed_line(results))
    if lines:
        return pre_context("; ".join(lines))
    return None


# --------------------------------------------------------------------------- post-write


def shell_quote(path):
    return "'" + path.replace("\\", "/").replace("'", "'\"'\"'") + "'"


def post_write(data):
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ""
    root = find_root(data.get("cwd") or os.getcwd())
    cfg = load_config(root)
    entries = cfg.get("format") or []
    if not entries or not hook_on(cfg, "format"):
        return None
    rel = rel_path(root, path)
    if not rel:
        return None
    abs_path = path if os.path.isabs(path) else os.path.join(root, path)
    shell = find_shell()
    for e in entries:
        if isinstance(e, dict) and e.get("cmd") and glob_match(e.get("glob") or "**", rel):
            cmd = e["cmd"].replace("{file}", shell_quote(abs_path))
            args = [shell, "-c", cmd] if shell else cmd
            try:
                subprocess.run(args, shell=not shell, cwd=root, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, timeout=50)
            except (OSError, subprocess.SubprocessError):
                pass
            break
    return None


# --------------------------------------------------------------------------- stop


def stop(data):
    root = find_root(data.get("cwd") or os.getcwd())
    cfg = load_config(root)
    if not hook_on(cfg, "stop") or not hook_on(cfg, "gates") or not gates_for(cfg, "stop"):
        return None
    session = data.get("session_id") or ""
    tree = tree_hash(root)
    if not tree:
        return None
    st = load_state(root, "stop.json", {})
    if not isinstance(st, dict):
        st = {}
    s = st.get(session) or {}
    if not s.get("baseline"):
        s["baseline"] = tree
        st[session] = s
        save_stop_state(root, st)
        return None
    if tree in (s.get("baseline"), s.get("passed")):
        return None
    if not data.get("stop_hook_active"):
        s["blocks"] = 0
    elif s.get("blocks", 0) >= MAX_STOP_BLOCKS:
        s["blocks"] = 0
        st[session] = s
        save_stop_state(root, st)
        return None
    results = run_gates(root, cfg, "stop", session) or []
    if any(r["status"] == "fail" for r in results):
        s["blocks"] = s.get("blocks", 0) + 1
        st[session] = s
        save_stop_state(root, st)
        return {"decision": "block", "reason": failure_summary("stop", results)}
    s["passed"] = tree
    s["blocks"] = 0
    st[session] = s
    save_stop_state(root, st)
    return None


def save_stop_state(root, st):
    if len(st) > 20:
        for k in list(st.keys())[:-20]:
            del st[k]
    save_state(root, "stop.json", st)


# --------------------------------------------------------------------------- session start


def openspec_lines(root):
    if not os.path.isdir(os.path.join(root, "openspec", "changes")):
        return []
    exe = shutil.which("openspec")
    if not exe:
        return []
    code, out = run([exe, "list", "--json"], cwd=root, timeout=15)
    if code != 0:
        return []
    try:
        changes = json.loads(out[out.index("{"):]).get("changes") or []
    except (ValueError, AttributeError):
        return []
    lines = []
    for c in changes[:4]:
        lines.append("- change %s: %s/%s tasks (%s)" % (
            c.get("name"), c.get("completedTasks", "?"), c.get("totalTasks", "?"), c.get("status", "?")))
    return lines


def log_lines(root):
    path = os.path.join(root, ".sdlc", "log.md")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return []
    idx = text.rfind("\n## ")
    if idx < 0:
        idx = 0 if text.startswith("## ") else -1
    if idx < 0:
        return []
    entry = [ln for ln in text[idx:].strip().split("\n") if ln.strip()][:5]
    return ["- last log: " + entry[0].lstrip("# ").strip()] + ["  " + ln.strip()[:160] for ln in entry[1:]]


def gate_lines(root):
    last = load_state(root, "last-gates.json", None)
    if not isinstance(last, dict) or not last.get("results"):
        return []
    res = last["results"]
    failed = [r["name"] for r in res if r.get("status") == "fail"]
    ok = [r["name"] for r in res if r.get("status") != "fail"]
    age = int((time.time() - last.get("time", time.time())) / 60)
    when = "%d min ago" % age if age < 120 else "%d h ago" % (age // 60)
    line = "- last gates (%s, %s): " % (last.get("stage"), when)
    line += ("FAILED " + ", ".join(failed) + "; " if failed else "") + ("passed " + ", ".join(ok) if ok else "")
    return [line.rstrip("; ")]


def session_start(data):
    root = find_root(data.get("cwd") or os.getcwd())
    cfg = load_config(root)
    if os.path.isdir(os.path.join(root, ".sdlc")):
        try:
            here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(state_dir(root), "plugin_root"), "w", encoding="utf-8") as f:
                f.write(here.replace("\\", "/") + "\n")
        except OSError:
            pass
        if hook_on(cfg, "stop") and gates_for(cfg, "stop") and data.get("session_id"):
            tree = tree_hash(root)
            if tree:
                st = load_state(root, "stop.json", {})
                if not isinstance(st, dict):
                    st = {}
                s = st.get(data["session_id"]) or {}
                s.setdefault("baseline", tree)
                st[data["session_id"]] = s
                save_stop_state(root, st)
    if not hook_on(cfg, "context"):
        return None
    lines = openspec_lines(root) + log_lines(root) + gate_lines(root)
    if not lines:
        return None
    text = "\n".join(["ai-sdlc-kit state (from hooks; no need to rediscover):"] + lines[:CONTEXT_MAX_LINES - 1])
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}


# --------------------------------------------------------------------------- manual subcommands


def cmd_stamp(args):
    if not args:
        sys.stderr.write("usage: run.sh stamp <kind|gate-name>\n")
        return 2
    target = args[0]
    root = find_root(os.getcwd())
    cfg = load_config(root)
    tree = tree_hash(root)
    if not tree:
        sys.stdout.write("stamp skipped: not a git repository\n")
        return 0
    cache = load_state(root, "cache.json", [])
    if not isinstance(cache, list):
        cache = []
    matched = [g for g in cfg.get("gates") or [] if isinstance(g, dict) and target in (g.get("name"), g.get("kind"))]
    if matched:
        for g in matched:
            record_pass(root, cache, g.get("name"), g.get("kind"), g.get("cmd"), tree, "stamp")
    else:
        record_pass(root, cache, target, target, None, tree, "stamp")
    sys.stdout.write("stamped %s at tree %s\n" % (target, tree[:10]))
    return 0


def cmd_check(args):
    stage = args[0] if args else "commit"
    root = find_root(os.getcwd())
    cfg = load_config(root)
    results = run_gates(root, cfg, stage, os.environ.get("SDLC_SESSION", "manual"))
    if not results:
        sys.stdout.write("no %s gates configured\n" % stage)
        return 0
    if any(r["status"] == "fail" for r in results):
        sys.stdout.write(failure_summary(stage, results) + "\n")
        return 1
    sys.stdout.write(passed_line(results) + "\n")
    return 0


def split_row(line):
    cells, cur, tick = [], [], False
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if c == "`":
            tick = not tick
        if c == "|" and not tick:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if "".join(cur).strip():
        cells.append("".join(cur).strip())
    return cells


def infer_kind(purpose, cmd):
    text = (purpose + " " + cmd).lower()
    p = purpose.lower()
    if re.search(r"\be2e\b|end[- ]to[- ]end|playwright|cypress", text):
        return "e2e"
    if "integration" in text:
        return "integration"
    if re.search(r"lint|format|ruff check|eslint", p) or (re.search(r"\blint\b", text) and "test" not in p):
        return "lint"
    if "build" in p:
        return "build"
    if re.search(r"\btypes?\b|type[- ]?check|mypy|tsc|pyright", text):
        return "types"
    if "test" in text:
        return "unit"
    return "build" if "build" in text else "unit"


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "gate"


def parse_commands_table(claude_md):
    lines = claude_md.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^##\s+Commands\b", ln.strip(), re.I):
            start = i + 1
            break
    if start is None:
        return []
    header = None
    rows = []
    for ln in lines[start:]:
        if ln.startswith("## "):
            break
        if not ln.strip().startswith("|"):
            if header and rows:
                break
            continue
        cells = split_row(ln)
        if header is None:
            header = [c.lower().strip("* ") for c in cells]
            continue
        if all(re.match(r"^:?-+:?$", c) for c in cells if c):
            continue
        rows.append(cells)
    if not header:
        return []

    def col(name):
        for j, h in enumerate(header):
            if h.startswith(name):
                return j
        return None

    ip, ic, ik = col("purpose"), col("command"), col("check")
    if ic is None or ik is None:
        return []
    gates = []
    used = set()
    for r in rows:
        if ik >= len(r) or not r[ik].lower().strip("* `").startswith("yes"):
            continue
        purpose = r[ip] if ip is not None and ip < len(r) else ""
        cell = r[ic] if ic < len(r) else ""
        m = re.search(r"`([^`]+)`", cell)
        cmd = (m.group(1) if m else cell).strip()
        if not cmd or "<!--" in cmd:
            continue
        kind = infer_kind(purpose, cmd)
        name = slug(re.sub(r"\(.*?\)", "", purpose)) or kind
        base, k = name, 2
        while name in used:
            name = "%s-%d" % (base, k)
            k += 1
        used.add(name)
        gates.append({"name": name, "kind": kind, "on": ["push"] if kind == "e2e" else ["commit"], "cmd": cmd})
    return gates


def cmd_init_gates(args):
    root = find_root(os.getcwd())
    target = os.path.join(root, CONFIG_REL)
    if os.path.exists(target):
        sys.stdout.write(".sdlc/gates.json: skipped (already exists)\n")
        return 0
    try:
        with open(os.path.join(root, "CLAUDE.md"), encoding="utf-8") as f:
            gates = parse_commands_table(f.read())
    except OSError:
        sys.stdout.write(".sdlc/gates.json: not created (no CLAUDE.md at %s)\n" % root.replace("\\", "/"))
        return 1
    if not gates:
        sys.stdout.write(".sdlc/gates.json: not created (no Commands rows marked yes in Check?)\n")
        return 1
    cfg = {"gates": gates, "protected": [], "secrets": {"allow": [], "ignore_paths": []}}
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    sys.stdout.write(".sdlc/gates.json: created with %d gates\n" % len(gates))
    for g in gates:
        sys.stdout.write("- %s (%s, on %s): %s\n" % (g["name"], g["kind"], "/".join(g["on"]), g["cmd"]))
    if "--no-gitignore" not in args:
        gi = os.path.join(root, ".gitignore")
        try:
            with open(gi, encoding="utf-8") as f:
                existing = f.read()
        except OSError:
            existing = ""
        if not re.search(r"(?m)^/?\.sdlc/(state/?)?\s*$", existing):
            with open(gi, "a", encoding="utf-8", newline="\n") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(".sdlc/state/\n")
            sys.stdout.write(".gitignore: added .sdlc/state/\n")
    return 0


# --------------------------------------------------------------------------- main

HOOKS = {
    "pre-write": pre_write,
    "pre-bash": pre_bash,
    "post-write": post_write,
    "stop": stop,
    "session-start": session_start,
}
MANUAL = {"stamp": cmd_stamp, "check": cmd_check, "init-gates": cmd_init_gates}


def main(argv):
    if sys.version_info < (3, 8):
        return 0
    if os.environ.get("SDLC_HOOKS", "").strip().lower() in ("off", "0", "false", "no"):
        return 0
    sub = argv[1] if len(argv) > 1 else ""
    if sub in MANUAL:
        return MANUAL[sub](argv[2:])
    fn = HOOKS.get(sub)
    if not fn:
        return 0
    try:
        result = fn(read_input())
        if result:
            out_json(result)
    except Exception as e:  # fail open
        if sub in SECRET_SUBCOMMANDS:
            sys.stderr.write("ai-sdlc-kit: %s check skipped after an error (%s)\n" % (sub, type(e).__name__))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
