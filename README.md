# Volley

**A step counter for conversations with your child.**

The Bee on a parent's wrist already hears the day. Volley counts the
back-and-forth exchanges between the parent and the child, keeps the
counts, throws the words away on the parent's own machine, and says one
thing to try tomorrow. The number it counts is the most validated one in
early childhood; the only instrument that measures it has never been
sold to a parent.

Status: planned, not built. The plan is in `docs/`, written before the
first line of code so that the build is judged against it.

| Document | What it answers |
|---|---|
| [docs/PLAN.md](docs/PLAN.md) | What gets built, in what order, with what gates and dates |
| [docs/DESIGN.md](docs/DESIGN.md) | The technical design: packages, the turn rule, privacy by construction, API, MCP, AWS, tests as claims |
| [docs/SITE.md](docs/SITE.md) | The landing page and product surface: every section, its copy outline, the i-buttons, light and dark, mobile and desktop, the first-time-visitor path |
| [docs/EVIDENCE.md](docs/EVIDENCE.md) | The science, what each number is and is not, and how the site is allowed to say it |
| [docs/PRIOR_ART.md](docs/PRIOR_ART.md) | Who has done what, named before a judge has to find it |
| [docs/HONESTY.md](docs/HONESTY.md) | Privacy, consent, what it never does, the limits, and the kill criteria |
| [docs/RULES_MAP.md](docs/RULES_MAP.md) | Every line of the rules and every judging criterion, and where it is met |
| [docs/WINNER_PATTERNS.md](docs/WINNER_PATTERNS.md) | The twelve patterns from top-placed projects, where Volley passes, and what closing each miss costs |

Track: Bee (primary), Alexa+ (an Agent Skill backed by an MCP server).
Mini challenges: AWS Builder, Open Source (`serve-return` on PyPI, MIT).

Sibling projects in this hackathon, each with its own repository and
docs: Earshot (Fire TV, hearing in noise), Bellwether (Bee, speech as a
vital sign), EveryWord (Fire TV), Nightlight (Ring). Volley reuses
Bellwether's Bee client, server, stack and video pipeline; it shares no
claim with it.
