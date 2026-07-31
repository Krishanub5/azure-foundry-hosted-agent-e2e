from __future__ import annotations

import argparse
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import deploy_agent  # noqa: E402


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class DeployAgentTests(unittest.TestCase):
    def test_parse_key_value_preserves_equals_in_value(self) -> None:
        self.assertEqual(deploy_agent.parse_key_value("KEY=a=b"), ("KEY", "a=b"))

    def test_parse_key_value_rejects_invalid_input(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            deploy_agent.parse_key_value("INVALID")

    def test_deploy_creates_immutable_version_and_routes_endpoint(self) -> None:
        deployer = object.__new__(deploy_agent.FoundryHostedAgentDeployer)
        deployer.get_agent = lambda _name: {"name": "assistant"}
        calls: list[tuple[str, str, dict[str, object]]] = []

        def request(method: str, path: str, **kwargs):
            calls.append((method, path, kwargs))
            if method == "POST":
                return _Response({"version": "7"})
            if path.endswith("/versions/7"):
                return _Response({"status": "active"})
            if method == "PATCH":
                return _Response({})
            return _Response(
                {"instance_identity": {"principal_id": "00000000-0000-0000-0000-000000000007"}}
            )

        deployer.request = request
        with redirect_stdout(io.StringIO()):
            result = deployer.deploy(
                name="assistant",
                image="registry.invalid/agent:sha",
                cpu="1",
                memory="2Gi",
                protocol_version="2.0.0",
                environment={"MODEL": "deployment"},
                timeout_seconds=10,
            )

        create_call = calls[0]
        self.assertEqual(create_call[:2], ("POST", "/agents/assistant/versions"))
        definition = create_call[2]["json"]["definition"]
        self.assertEqual(
            definition["container_configuration"]["image"], "registry.invalid/agent:sha"
        )
        self.assertEqual(
            definition["protocol_versions"],
            [{"protocol": "responses", "version": "2.0.0"}],
        )
        patch_call = next(call for call in calls if call[0] == "PATCH")
        rule = patch_call[2]["json"]["agent_endpoint"]["version_selector"][
            "version_selection_rules"
        ][0]
        self.assertEqual(rule["agent_version"], "7")
        self.assertEqual(rule["traffic_percentage"], 100)
        self.assertEqual(
            result["instance_identity_principal_id"], "00000000-0000-0000-0000-000000000007"
        )


if __name__ == "__main__":
    unittest.main()
