# Security Policy

## Supported versions

Security fixes are applied to the `main` branch and included in the next tagged release.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting:

1. Open the **Security** tab of this repository.
2. Select **Advisories** and then **Report a vulnerability**.

Do not open a public issue for an unfixed vulnerability.

## Known dependency advisories

`chromadb 1.5.9` is installed as a transitive dependency of `crewai[tools]`. Four open advisories affect it:

- GHSA-36p7-vc44-83pf (critical)
- GHSA-f4j7-r4q5-qw2c (critical)
- GHSA-2wm9-hf6c-p5cr (high)
- GHSA-xph7-9rjv-w5fr (high)

No patched release exists as of 2026-11-21. This project does not enable CrewAI memory and does not run a Chroma server, so the vulnerable authorization and server paths are not used. The package remains a supply-chain risk. Remove or upgrade it as soon as upstream publishes a fixed release.

Other direct and transitive dependencies are kept on patched versions. `pyproject.toml` requires Python 3.11.5+ and constrains `soupsieve>=4.0.0` because earlier releases have open advisories. The lockfile resolves `soupsieve 4.1.3`.
