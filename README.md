# IRPF SINACOR (BTG) Monorepo Skeleton

Local-first monorepo skeleton with FastAPI backend + Vue frontend for SINACOR (BTG) workflow.


## Local validation

Use the Makefile to run the same checks expected in CI:

```bash
make setup
make ci
```

Or run individual checks:

```bash
make lint
make type-check
make test
```
