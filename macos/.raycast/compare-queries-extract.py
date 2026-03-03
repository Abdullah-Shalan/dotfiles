#!/usr/bin/env python3
"""
Compare two query files (plain text or TOML/YAML configs) by reducing each to a
canonical form and checking for any difference.

- For TOML/YAML: parses the file and extracts all query strings (from common keys
  like query, queries, body, filter, rule.query, etc.). All entries in a
  "queries" list are included so that removing a single entry is detected.
- For other extensions: treats the file as plain text.
- Canonicalization strips leading/trailing whitespace and collapses every run of
  whitespace (spaces, tabs, newlines) to a single space, so indentation and
  line breaks do not cause a mismatch.

Usage:
  compare-queries-extract.py <file1> <file2>

Exit codes:
  0  queries match (canonical forms identical)
  1  queries mismatch (canonical forms differ, even by one character)
  2  usage error / parse error / no queries found
"""

import os
import re
import sys


def _load_structured(path: str):
    """Load YAML or TOML into a Python structure, or return None for plain text."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore

            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            sys.stderr.write("Error: PyYAML required for YAML. pip install PyYAML\n")
            sys.exit(2)
        except Exception as e:  # pragma: no cover - defensive
            sys.stderr.write(f"Error parsing YAML: {e}\n")
            sys.exit(2)
    if ext == ".toml":
        try:
            if sys.version_info >= (3, 11):
                import tomllib  # type: ignore

                with open(path, "rb") as f:
                    return tomllib.load(f)
            else:
                import toml  # type: ignore

                with open(path, encoding="utf-8") as f:
                    return toml.load(f)
        except ImportError:
            sys.stderr.write(
                "Error: TOML requires Python 3.11+ (tomllib) or pip install toml\n"
            )
            sys.exit(2)
        except Exception as e:  # pragma: no cover - defensive
            sys.stderr.write(f"Error parsing TOML: {e}\n")
            sys.exit(2)
    # Non-config file: caller will treat as plain text.
    return None


def _get_queries_list(obj, keys):
    """Return a list of query strings (possibly one element)."""
    if obj is None:
        return []
    if isinstance(keys, str):
        keys = [keys]
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            v = obj[k]
            if isinstance(v, str):
                return [v]
            if isinstance(v, list):
                if v and isinstance(v[0], str):
                    return list(v)
                # list of dicts, e.g. rule: [{ query: "..." }]
                out = []
                for item in v:
                    if isinstance(item, dict):
                        qs = _get_queries_list(item, ["query", "queries", "body", "filter"])
                        out.extend(qs)
                if out:
                    return out
            if isinstance(v, dict):
                qs = _get_queries_list(v, ["query", "queries", "body", "filter"])
                if qs:
                    return qs
    return []


def _queries_from_rule_list(rule_list):
    """Get all query strings from rule when rule is a list."""
    if not isinstance(rule_list, list) or not rule_list:
        return []
    out = []
    for item in rule_list:
        if isinstance(item, dict):
            out.extend(_get_queries_list(item, ["query", "queries", "body", "filter"]))
    return out


def _find_all_queries(obj):
    if isinstance(obj, dict):
        if "query" in obj and isinstance(obj["query"], str):
            return [obj["query"]]
        if "queries" in obj and isinstance(obj["queries"], list):
            if obj["queries"] and isinstance(obj["queries"][0], str):
                return list(obj["queries"])
        for v in obj.values():
            r = _find_all_queries(v)
            if r:
                return r
    if isinstance(obj, list):
        for item in obj:
            r = _find_all_queries(item)
            if r:
                return r
    return []


def extract_query_text(path: str) -> str:
    """Return the raw query text to compare for a given file."""
    data = _load_structured(path)
    if data is None:
        # Plain text file: just read it as-is.
        with open(path, encoding="utf-8") as f:
            return f.read()

    queries = (
        _get_queries_list(data, "query")
        or _get_queries_list(data, "queries")
        or _get_queries_list(data, "body")
        or _get_queries_list(data, "filter")
        or _queries_from_rule_list(data.get("rule"))
        or _get_queries_list(data, ["rule", "query"])
        or _get_queries_list(data, ["rule", "queries"])
        or _get_queries_list(data, ["body", "query"])
        or _get_queries_list(data, ["search", "query"])
    )
    if not queries:
        queries = _find_all_queries(data)

    if not queries:
        sys.stderr.write(f"Error: No 'query' or 'queries' field found in {path}\n")
        sys.exit(2)

    # Join all queries with newlines; the canonicalizer will flatten whitespace.
    return "\n".join(queries) + "\n"


def to_canonical(text: str) -> str:
    """Strip leading/trailing whitespace and collapse every run of whitespace to a single space."""
    text = text.strip()
    return re.sub(r"\s+", " ", text)


def save_file(text: str, path: str):
    with open(path, "w") as f:
        f.write(text)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        sys.stderr.write("Usage: compare-queries-extract.py <file1> <file2>\n")
        sys.exit(2)

    file1, file2 = argv

    if not os.path.isfile(file1):
        sys.stderr.write(f"Error: not a file: {file1}\n")
        sys.exit(2)
    if not os.path.isfile(file2):
        sys.stderr.write(f"Error: not a file: {file2}\n")
        sys.exit(2)

    raw1 = extract_query_text(file1)
    raw2 = extract_query_text(file2)

    save_file(raw1, "data/1_raw.txt")
    save_file(raw2, "data/2_raw.txt")

    canon1 = to_canonical(raw1)
    canon2 = to_canonical(raw2)

    save_file(canon1, "data/1_canon.txt")
    save_file(canon2, "data/2_canon.txt")

    if canon1 == canon2:
        print("queries match")
        sys.exit(0)

    print("queries mismatch")
    sys.exit(1)

if __name__ == "__main__":
    main()
