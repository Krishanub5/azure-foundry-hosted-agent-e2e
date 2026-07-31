"""Microsoft Foundry Hosted Agent entry point."""

from __future__ import annotations

from typing import Annotated

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from prompt import SYSTEM_PROMPT
from pydantic import Field
from rag import KnowledgeSearch
from settings import AgentSettings


def build_agent() -> Agent:
    """Build the in-process Agent Framework agent exposed by Foundry hosting."""
    settings = AgentSettings.from_environment()
    knowledge = KnowledgeSearch(settings)

    @tool(
        name="search_enterprise_knowledge",
        description=(
            "Search approved enterprise documents. Use this before answering factual "
            "questions about policies, procedures, systems, standards, or internal guidance."
        ),
        approval_mode="never_require",
    )
    def search_enterprise_knowledge(
        query: Annotated[
            str,
            Field(
                description=(
                    "A concise standalone search query containing the important entities "
                    "and constraints from the user's question."
                )
            ),
        ],
        top_k: Annotated[
            int,
            Field(description="Number of evidence passages to return, from 1 to 8", ge=1, le=8),
        ] = 5,
    ) -> str:
        """Return grounded passages and stable source labels from Azure AI Search."""
        return knowledge.search(query=query, top_k=top_k)

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    model_client = FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.model_deployment_name,
        credential=credential,
    )

    return Agent(
        client=model_client,
        name="EnterpriseKnowledgeAssistant",
        instructions=SYSTEM_PROMPT,
        tools=[search_enterprise_knowledge],
        # Foundry Agent Service owns session/history persistence for the hosted protocol.
        default_options={"store": False},
    )


def main() -> None:
    server = ResponsesHostServer(build_agent())
    server.run()


if __name__ == "__main__":
    main()
