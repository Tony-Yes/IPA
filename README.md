# MoviePilot release feed (LCSign compatibility test)

This is an unofficial AltStore-style plaintext JSON feed pointing at official
jxxghp/MoviePilot-App unsigned GitHub release assets. LCSign compatibility has
NOT been verified. Its screenshot confirms plaintext sources but not field schema.

## Publish

1. Create a PUBLIC GitHub repository named `moviepilot-source`, default branch `main`.
2. Upload `update.py`, `source.json`, README.md, and `.github/workflows/update.yml`.
   The hidden `.github` folder is required. If using GitHub's web UI, use Add file >
   Create new file and enter `.github/workflows/update.yml`, then paste its contents.
3. Open Actions > Update MoviePilot source > Run workflow.
4. Confirm the run succeeds and view source.json on the main branch.
5. Add this URL to LCSign (replace YOUR_USERNAME):
   https://raw.githubusercontent.com/YOUR_USERNAME/moviepilot-source/main/source.json
6. Confirm LCSign shows MoviePilot and can download the unsigned IPA. Signing still
   requires your own valid certificate. If import fails, retain the error text;
   the JSON schema may need adaptation to LCSign.

No GitHub Pages setup or personal access token is needed. The workflow uses the
repository's built-in GITHUB_TOKEN with contents:write. Repository policies or
branch protection may prohibit commits; inspect Actions logs if git push fails.

Every six hours, Actions queries the latest non-prerelease release, matches exactly
one MoviePilot-*-unsigned.ipa, downloads it temporarily, verifies SHA256SUMS and size,
reads the main Info.plist for actual version/bundle ID, then updates source.json.
No IPA is committed or mirrored. Only changed JSON is committed. Failed checks
leave the previous source.json intact. Scheduled jobs may be delayed by GitHub;
public-repository schedules can be disabled after 60 days of repository inactivity.

The upstream checksum guards download integrity, not independently the publisher's
identity. Code and workflows should be reviewed before enabling Actions.
