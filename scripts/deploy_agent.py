"""Create a new Hosted Agent version through the current Foundry v1 REST API."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx
from azure.identity import DefaultAzureCredential


def parse_key_value(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Environment values must use KEY=VALUE")
    key, item = value.split("=", 1)
    if not key:
        raise argparse.ArgumentTypeError("Environment key cannot be empty")
    return key, item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-endpoint", required=True)
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--cpu", default="1")
    parser.add_argument("--memory", default="2Gi")
    parser.add_argument("--protocol-version", default="2.0.0")
    parser.add_argument("--env", action="append", default=[], type=parse_key_value)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser.parse_args()


class FoundryHostedAgentDeployer:
    def __init__(self, project_endpoint: str):
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        token = credential.get_token("https://ai.azure.com/.default").token
        credential.close()
        self.base_url = project_endpoint.rstrip("/")
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={"api-version": "v1"},
            timeout=httpx.Timeout(120, connect=20),
        )

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = self.client.request(method, f"{self.base_url}{path}", **kwargs)
        if response.status_code >= 400:
            detail = response.text[:2000]
            raise RuntimeError(
                f"Foundry API {method} {path} failed with {response.status_code}: {detail}"
            )
        return response

    def get_agent(self, name: str) -> dict[str, Any] | None:
        response = self.client.get(f"{self.base_url}/agents/{name}")
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise RuntimeError(
                f"Unable to inspect Hosted Agent: {response.status_code} {response.text[:1000]}"
            )
        return response.json()

    def deploy(
        self,
        name: str,
        image: str,
        cpu: str,
        memory: str,
        protocol_version: str,
        environment: dict[str, str],
        timeout_seconds: int,
    ) -> dict[str, Any]:
        definition = {
            "kind": "hosted",
            "container_configuration": {"image": image},
            "cpu": cpu,
            "memory": memory,
            "protocol_versions": [{"protocol": "responses", "version": protocol_version}],
            "environment_variables": environment,
        }
        existing = self.get_agent(name)
        if existing is None:
            created = self.request(
                "POST",
                "/agents",
                json={"name": name, "definition": definition},
            ).json()
            version = str(
                created.get("version")
                or created.get("versions", {}).get("latest", {}).get("version")
                or "1"
            )
        else:
            created = self.request(
                "POST",
                f"/agents/{name}/versions",
                json={"definition": definition},
            ).json()
            version = str(created.get("version") or "")
            if not version:
                raise RuntimeError("Foundry did not return the new agent version")

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            version_info = self.request(
                "GET",
                f"/agents/{name}/versions/{version}",
            ).json()
            status = str(version_info.get("status", "unknown"))
            print(f"Hosted Agent version {version}: {status}", flush=True)
            if status == "active":
                break
            if status == "failed":
                raise RuntimeError(
                    f"Hosted Agent provisioning failed: {json.dumps(version_info.get('error'))}"
                )
            time.sleep(10)
        else:
            raise TimeoutError(f"Hosted Agent version {version} did not become active")

        self.request(
            "PATCH",
            f"/agents/{name}",
            headers={"Content-Type": "application/merge-patch+json"},
            json={
                "agent_endpoint": {
                    "version_selector": {
                        "version_selection_rules": [
                            {
                                "agent_version": version,
                                "traffic_percentage": 100,
                                "type": "FixedRatio",
                            }
                        ]
                    },
                    "protocol_configuration": {"responses": {}},
                }
            },
        )
        agent = self.request("GET", f"/agents/{name}").json()
        principal_id = agent.get("instance_identity", {}).get("principal_id") or agent.get(
            "instanceIdentity", {}
        ).get("principalId")
        return {
            "agent_name": name,
            "version": version,
            "status": "active",
            "instance_identity_principal_id": principal_id,
            "image": image,
        }

    def close(self) -> None:
        self.client.close()


def main() -> None:
    args = parse_args()
    deployer = FoundryHostedAgentDeployer(args.project_endpoint)
    try:
        result = deployer.deploy(
            name=args.agent_name,
            image=args.image,
            cpu=args.cpu,
            memory=args.memory,
            protocol_version=args.protocol_version,
            environment=dict(args.env),
            timeout_seconds=args.timeout_seconds,
        )
    finally:
        deployer.close()

    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
