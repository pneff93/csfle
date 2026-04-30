# csfle-gen

Interactive CLI for generating CSFLE (Client-Side Field Level Encryption) client projects.

The generator asks a series of questions about the target Confluent deployment, KMS provider, and client language, then writes a ready-to-run client project under `../generated/<project-name>/`.

## Quickstart

```shell
uv run csfle-gen new
```

That's it. `uv` handles the virtualenv and dependencies; no manual setup needed.

<video width="100%" controls muted autoplay loop>
  <source src="./assets/demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## What gets generated

A self-contained project. Common to both languages:

- Avro schema with the `birthday` field tagged as PII
- A config module that loads `.env`, validates env vars, and exposes config getters
- Producer + consumer that produce/consume encrypted records
- `bootstrap.sh` — creates the Kafka topic and registers the schema + encryption rule
- `.env`, `.env.example`, `README.md`

Python adds `requirements.txt`; Java adds `pom.xml`, `BootstrapTopic.java`, and `src/main/resources/logback.xml`.

## Supported combinations

| Target | KMS providers | Languages |
|---|---|---|
| Confluent Cloud | AWS, Azure, GCP, HashiCorp Vault | Python, Java |
| Confluent Platform | AWS, Azure, GCP, HashiCorp Vault | Python, Java |

Other languages will be added as sibling template trees in future versions.

## Development

```shell
# Run tests
uv run pytest

# Update snapshots after intentional template changes
uv run pytest --snapshot-update
```
