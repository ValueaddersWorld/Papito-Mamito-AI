# Daily Blog Playbook

Papito's blog series offers a transparent window into his creative evolution, building trust and intimacy with the fanbase.

## Objectives
- Reinforce Papito Mamito's mission, values, and gratitude-first philosophy.
- Document musical experiments, release progress, and community highlights.
- Provide actionable inspiration for aspiring artists and knowledge workers.

## Format
1. **Opening blessing:** Short gratitude prayer or affirmation.
2. **Today's groove:** Behind-the-scenes on current song or rehearsal.
3. **Value drop:** Insight, framework, or empowerment lesson.
4. **Fan spotlight:** Celebrate the community, cite comments or collaborations.
5. **Call to unity:** Invitation to listen, share, or meditate on abundance.

## Automation Workflow
1. Load canonical prompts from `papito_core.prompts.blog`.
2. Feed daily context (for example: song in progress, gratitude focus) via JSON.
3. Generate a draft using Papito's voice profile.
4. Run tone-alignment checks for gratitude, empowerment, authenticity, unity, and spirituality.
5. Save the markdown entry under `content/blogs/YYYY/MM/DD.md`.
6. Publish a summary to social surfaces (Instagram, X, Discord) via connectors.
