# Papito Core

`papito_core` contains the autonomous creative toolkit that powers Papito Mamito AI.  
Install it in editable mode to experiment with workflows that generate music concepts, daily blogs, and release plans.

```bash
pip install -e apps/papito_core[dev]
```

## Modules
- `papito_core.prompts` - Persona-aware prompt builders for blogs and music.
- `papito_core.workflows` - High-level orchestration around text generation engines.
- `papito_core.engines` - Interfaces and stubs for plugging in your preferred LLM provider.
- `papito_core.storage` - Release catalog persistence.

Replace the stub generator with an actual LLM client to unleash Papito's full creative range.
