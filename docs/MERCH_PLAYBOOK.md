# Merch Playbook

Merchandise is more than revenue—it’s a tangible extension of Papito’s gratitude ministry. This guide outlines how to curate, release, and restock offerings.

## Catalog Structure
- Stored in `content/fans/merch_catalog.json`
- Each item: `sku`, `name`, `description`, `price`, `currency`, `url`, optional `inventory`
- Update via CLI: `papito merch add`

## Drop Cadence
1. **Announcement** – Tease new items 1 week prior with testimonials or behind-the-scenes footage.
2. **Launch Day** – Sync blog post, social carousel, and email blast. Include a gratitude shout-out per item.
3. **Sustain** – Highlight a “Fan Fit Friday” look each week, rotating top supporters.
4. **Restock** – When inventory drops below threshold, prompt manufacturing partners and notify VIP fans first.

## Ethical Merch Principles
- Source materials from ethical supplier networks (documented in Value Adders supply chain).
- Embed affirmations inside packaging (gratitude cards, QR codes linking to Papito meditations).
- Allocate a percentage of profits to community uplift projects (scholarships, studio grants).

## Operational Checklist
- [ ] Add items via CLI and regenerate catalog
- [ ] Sync catalog with hosted API so storefronts stay in sync
- [ ] Ensure shipping and tax details are reflected on the external storefront
- [ ] Update `docs/FANBASE_STRATEGY.md` if new supporter tiers receive exclusive items
