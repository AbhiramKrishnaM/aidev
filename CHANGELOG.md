# Changelog

## 2026-08-11 10:54
- Removed the Ollama-only implementation (model class, `--local/--api` flags, dead config/deps)
- Provider registry (`MODEL_CLASSES`) is now empty, ready for the Anthropic/OpenAI pivot
- Rewrote README, dev docs, and marketing site copy to drop Ollama references
- Wrote ADRs and architecture docs for the cloud-provider pivot in `docs/adr/` and `docs/architecture.md`
