SHELL := /usr/bin/env bash

PYTHON ?= python3
ENV ?= development
TAG ?= local
SOURCE ?= sample-data
AUDIT_CACHE ?= .cache/pip-audit
TF_DIR := infra/terraform
TFVARS := environments/$(ENV).tfvars

.PHONY: help setup-dev lint test coverage audit validate-local validate-all docker-build init fmt validate plan apply images deploy-agent agent-rbac deploy-ui ingest smoke destroy-plan

help:
	@echo "Quality: setup-dev lint test coverage audit validate-local validate-all docker-build"
	@echo "Deploy: init fmt validate plan apply images deploy-agent agent-rbac deploy-ui ingest smoke destroy-plan"
	@echo "Examples: make validate-local | make apply ENV=development | make ingest ENV=development SOURCE=sample-data"

setup-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install --requirement requirements-dev.txt

lint:
	$(PYTHON) -m ruff check apps scripts tests
	$(PYTHON) -m ruff format --check apps scripts tests

test:
	$(PYTHON) -m compileall -q apps scripts
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

coverage:
	$(PYTHON) -m coverage erase
	$(PYTHON) -m coverage run -m unittest discover -s tests -p 'test_*.py'
	$(PYTHON) -m coverage report

audit:
	$(PYTHON) -m pip_audit --cache-dir "$(AUDIT_CACHE)" --progress-spinner off

validate-local:
	./scripts/validate-local.sh

validate-all:
	./scripts/validate-local.sh --all

docker-build:
	docker build --tag enterprise-knowledge-agent:local apps/agent
	docker build --tag enterprise-knowledge-web:local apps/web
	docker build --tag enterprise-knowledge-ingestion:local apps/ingestion

init:
	terraform -chdir=$(TF_DIR) init

fmt:
	terraform -chdir=$(TF_DIR) fmt -recursive

validate:
	terraform -chdir=$(TF_DIR) validate

plan:
	terraform -chdir=$(TF_DIR) plan -var-file=$(TFVARS) -out=.build-$(ENV).tfplan

apply:
	terraform -chdir=$(TF_DIR) apply .build-$(ENV).tfplan

images:
	./scripts/build-and-push.sh $(ENV) $(TAG)

deploy-agent:
	./scripts/deploy-agent.sh $(ENV) $(TAG)

agent-rbac:
	./scripts/post-deploy-rbac.sh $(ENV)

deploy-ui:
	./scripts/deploy-ui.sh $(ENV) $(TAG)

ingest:
	./scripts/ingest.sh $(ENV) "$(SOURCE)"

smoke:
	./scripts/smoke-test.sh $(ENV)

destroy-plan:
	terraform -chdir=$(TF_DIR) plan -destroy -var-file=$(TFVARS)
