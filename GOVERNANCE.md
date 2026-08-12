# GULA Platform Governance

## Project Overview

GULA Platform is an open-source healthcare platform governed by the principles
outlined in PROGRAM-CONSTITUTION-001. This document describes the governance
model for the project.

## Governance Model

The project follows a **benevolent dictator** governance model with a single
lead maintainer and contributor community.

### Roles

#### Lead Maintainer
- Final decision authority on project direction
- Appoints and removes maintainers
- Manages the project roadmap
- Represents the project in external communications
- Ensures Platform Constitution compliance

#### Maintainers
See [MAINTAINERS.md](MAINTAINERS.md) for current maintainers and their
responsibilities.

#### Contributors
- Anyone who submits a pull request, files an issue, or participates in
  discussions
- Expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md)
- Expected to comply with the [Contributing Guide](CONTRIBUTING.md)

### Decision Making

| Decision Type | Process |
|---------------|---------|
| Bug fixes | PR review by maintainer |
| Feature additions | PR review + maintainer approval |
| Breaking changes | Maintainer consensus + issue discussion |
| Governance changes | Lead maintainer decision + community notice |
| Constitution changes | Lead maintainer decision (permanent rules) |

### Voting

When consensus cannot be reached, the lead maintainer makes the final decision.
Major decisions should be communicated via GitHub Discussions.

## Platform Constitution

This project is permanently governed by **PROGRAM-CONSTITUTION-001**:

1. **Free First** — Always implement with free solutions before considering paid
2. **Open Source First** — Prefer open-source dependencies
3. **Self-Hosted First** — Self-host before using SaaS
4. **No Vendor Lock-In** — All components must be replaceable
5. **Reuse Before Build** — Search existing code before implementing new features
6. **Zero Paid Dependency** — Paid software requires documented exception
7. **Local AI First** — Self-hosted AI inference before commercial APIs
8. **Free Security First** — Use open-source security tools

Full policy: `docs/constitution/COST_GOVERNANCE.md`

## Code of Conduct

All community participants must follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Contributing

See the [Contributing Guide](CONTRIBUTING.md) for details on how to contribute.

## Versioning

This project follows [Semantic Versioning](https://semver.org/). See
[CHANGELOG.md](CHANGELOG.md) for release history.

## License

This project is licensed under the Apache License, Version 2.0.
See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.
