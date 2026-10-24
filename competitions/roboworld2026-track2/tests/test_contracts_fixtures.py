import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "contracts"

try:  # full validation when jsonschema is installed; structural checks otherwise
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


def _structural_check(schema, instance, path="$"):
    if "const" in schema:
        assert instance == schema["const"], f"{path}: const mismatch"
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        assert isinstance(instance, dict), f"{path}: expected object"
        for key in schema.get("required", []):
            assert key in instance, f"{path}: missing required {key}"
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(instance) - set(props)
            assert not extra, f"{path}: unexpected keys {sorted(extra)}"
        for key, sub in props.items():
            if key in instance and "$ref" not in sub and "anyOf" not in sub:
                _structural_check(sub, instance[key], f"{path}.{key}")
    elif t == "array":
        assert isinstance(instance, list), f"{path}: expected array"
    elif t == "string":
        assert isinstance(instance, str), f"{path}: expected string"
    elif t == "integer":
        assert isinstance(instance, int) and not isinstance(instance, bool), f"{path}: expected integer"
    elif t == "number":
        assert isinstance(instance, (int, float)) and not isinstance(instance, bool), f"{path}: expected number"
    elif t == "boolean":
        assert isinstance(instance, bool), f"{path}: expected boolean"
    if "enum" in schema:
        assert instance in schema["enum"], f"{path}: not in enum"


class ContractFixtureTests(unittest.TestCase):
    def test_every_schema_has_a_valid_fixture(self):
        schemas = sorted(ROOT.glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 14)
        for sp in schemas:
            schema = json.loads(sp.read_text())
            fx = ROOT / "fixtures" / sp.name.replace(".schema.json", ".json")
            self.assertTrue(fx.exists(), f"missing fixture for {sp.name}")
            instance = json.loads(fx.read_text())
            if jsonschema is not None:
                jsonschema.validate(instance, schema)
            else:
                _structural_check(schema, instance)

    def test_fixture_rejects_missing_required_key(self):
        sp = ROOT / "EpisodeInput_v1.schema.json"
        schema = json.loads(sp.read_text())
        instance = json.loads((ROOT / "fixtures" / "EpisodeInput_v1.json").read_text())
        required = schema.get("required", [])
        self.assertTrue(required)
        broken = {k: v for k, v in instance.items() if k != required[-1]}
        if jsonschema is not None:
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(broken, schema)
        else:
            with self.assertRaises(AssertionError):
                _structural_check(schema, broken)


if __name__ == "__main__":
    unittest.main()
