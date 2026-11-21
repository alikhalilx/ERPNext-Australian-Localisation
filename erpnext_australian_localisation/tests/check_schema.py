"""Compare the fork's schema declarations to the reviewed version-16 baseline."""

import ast
import json
import subprocess
from pathlib import Path

BASE = "922dfd861fe48d03af19293ceea5277f68d7cb03"
ROOT = Path(__file__).resolve().parents[2]
APP = "erpnext_australian_localisation"
CUSTOM_FIELDS = APP + "/setup/custom_fields.py"


def upstream(*args):
	return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def declarations(source):
	return {
		node.targets[0].id: ast.literal_eval(node.value)
		for node in ast.parse(source).body
		if isinstance(node, ast.Assign)
	}


def schema(source):
	doc = json.loads(source)
	return (
		doc["name"],
		doc.get("issingle", 0),
		doc.get("istable", 0),
		[(f["fieldname"], f["fieldtype"], f.get("options")) for f in doc["fields"]],
	)


def check():
	expected = declarations(upstream("show", BASE + ":" + CUSTOM_FIELDS))
	actual = declarations((ROOT / CUSTOM_FIELDS).read_text())
	(switch,) = actual["CUSTOM_FIELDS"].pop("Company")
	assert (switch["fieldname"], switch["fieldtype"], switch["default"]) == (
		"enable_australian_localisation",
		"Check",
		"0",
	)
	assert actual == expected, "Unreviewed change to custom field declarations"
	pattern = "**/doctype/*/*.json"
	baseline = {
		p: schema(upstream("show", BASE + ":" + p))
		for p in upstream("ls-tree", "-r", "--name-only", BASE, APP).splitlines()
		if Path(p).match(pattern) and Path(p).stem == Path(p).parent.name
	}
	current = {
		p.relative_to(ROOT).as_posix(): schema(p.read_text())
		for p in (ROOT / APP).glob(pattern)
		if p.stem == p.parent.name
	}
	assert current == baseline, "Unreviewed change to app DocTypes"
	print(f"Verified {len(current)} upstream DocTypes and one additional Company field.")


if __name__ == "__main__":
	check()
