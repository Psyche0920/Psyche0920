# Profile design and evidence

This profile uses original repository-owned SVGs, CSS-only animation, and ordinary GitHub Markdown. It does not depend on third-party stats widgets, browser JavaScript, custom HTML scripts, tracking pixels, or additional account tokens.

## Design reference

The visual hierarchy draws inspiration from [DenverCoder1's profile](https://github.com/DenverCoder1): a strong graphic introduction, contact buttons, grouped projects, and visible statistics. The SVG artwork and renderer here were created for Weijia Han, rather than copied from that profile. Additional references: [Awesome GitHub Profile README](https://github.com/abhisheknaiidu/awesome-github-profile-readme).

## Data boundaries

- Profile and public repository statistics come from unauthenticated GitHub REST endpoints.
- The skyline renders GitHub's published daily intensity levels, not a fabricated count of commits.
- All numbers are dated snapshots. They do not automatically update in this version.
- The radar counts explicitly mapped projects. One project can demonstrate more than one focus area. It is not a claim about skill proficiency, percentile, employment seniority, or certification.
- The language donut counts public repositories by primary detected language, rather than lines of code. Repositories without a detected language are omitted; the profile repository is excluded.
- The achievement showcase uses only badges actually observed on the account. The badges link to GitHub's original achievement records. GitHub Pro is a subscription highlight, not an earned achievement.
- Existing private project descriptions were retained from the approved portfolio. Their repositories remain private. They are not included in public API counts.
- Project milestones such as LEVEL3 and the hackathon finalist role are professional/project context, not GitHub achievements.
- User email links use `mailto:hanweijia.ann@outlook.com`, which opens a configured email application. A plain email address is also visible for copying.

## Reproduce and refresh

Requires Python 3.11 or newer; standard library only.

```bash
python scripts/render_profile.py            # reproduce assets from saved snapshot
python scripts/render_profile.py --refresh  # fetch current public data and regenerate
```

Review and commit regenerated assets and data after a refresh. No scheduled workflow or account secret is installed. A failed source request raises `ProfileDataError` before replacing the previous assets. CSS animation respects reduced-motion preferences and retains a readable static state.

Generated image filenames include a content hash, and the renderer updates README image references. This avoids GitHub showing a cached old chart after new statistics are published. The renderer removes only obsolete files matching its own generated image names.

See [data/evidence.json](data/evidence.json) for source URLs and radar mappings, and [data/snapshot.json](data/snapshot.json) for the public snapshot used by the renderer.

## Achievement visibility

GitHub's account preference controls whether anonymized private activity counts toward the native graph and achievements. Public badge availability and tiers remain determined by GitHub. Some achievements require genuine collaboration, community recognition, or actions by other users; a README cannot award them.

References: [GitHub profile reference](https://docs.github.com/en/account-and-profile/reference/profile-reference) and [achievement visibility settings](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/manage-visibility-settings-for-private-contributions-and-achievements).
