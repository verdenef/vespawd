# Design tool sources

Record **where** UI lives outside the repo. Artifacts go in `screens/` and `exports/`.

| Tool | Link / project ID | Auth / MCP notes |
|------|-------------------|------------------|
| _e.g. Google Stitch_ | _project URL_ | _MCP in Cursor; setup via stitch.withgoogle.com — see docs/STITCH_CURSOR.md_ |
| | | |

**Habit:** Update this file when you connect Stitch (or Figma, v0, etc.) so future chats know your setup.

Examples:

- Figma: `https://www.figma.com/file/...`
- Google Stitch: project URL; MCP package name from Stitch’s Cursor instructions
- Penpot / v0: link + export folder used

**Do not put API keys in this file** — keys belong in `.cursor/mcp.json` (gitignored).
