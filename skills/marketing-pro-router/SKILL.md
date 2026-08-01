---
name: marketing-pro-router
version: 1.0.0
description: Route ANY marketing or content-production request (YouTube creatives, ad creative, campaign plans, SEO/AEO audits, brand setup, content engine, social posts, email, competitor analysis, analytics reports) to the digital-marketing-pro plugin's 158 skills. Load this first, pick the right skill from the catalog, then load it with skill_view.
---

# Digital Marketing Pro — skill router

The `digital-marketing-pro` plugin provides 158 marketing skills, but plugin skills
are NOT in the ambient skills index — they must be loaded explicitly:

    skill_view("digital-marketing-pro:<skill-name>")

Pick the best match from the catalog below, load it, and follow it.
For YouTube creative/script/thumbnail work, ALSO consider the youtube-insights plugin skills
(`youtube-insights:youtube-content-creator`, `youtube-insights:generate-image`,
`youtube-insights:image-style-guide`, `youtube-insights:youtube-gap-finder`) which carry
the channel's own style system and competitive-intelligence workspace.

## Catalog

- `ab-test-plan` — "Design A/B and multivariate tests. Use when: sample size calculation, testing hypothesis, CRO experimentation."
- `ad-creative` — "Generate platform-specific ad copy. Use when: Google RSA, Meta, LinkedIn, TikTok ad variations with quality scoring."
- `add-integration` — "Add MCP server integrations. Use when: connecting a custom tool, API, or service to the plugin via .mcp.json."
- `aeo-audit` — "Audit AI search visibility. Use when: checking brand presence in ChatGPT, Perplexity, AI Overviews, Gemini."
- `aeo-geo` — "Optimize AI engine visibility. Use when: AEO/GEO strategy, citation optimization, entity consistency across AI platforms."
- `agency-dashboard` — "Portfolio-level agency dashboard aggregating health metrics across all client brands — campaign status, budget pacing, KPI attainment, team utilization. Use wh
- `analytics-insights` — "Analyze marketing performance. Use when: KPI frameworks, attribution modeling, anomaly investigation, measurement strategy."
- `anomaly-scan` — "Detect marketing anomalies. Use when: traffic drops, cost spikes, conversion changes, deliverability issues, budget overruns."
- `attribution-model` — "Set up attribution models. Use when: multi-touch attribution, credit distribution rules, GA4 config, channel contribution."
- `attribution-report` — "Run multi-touch attribution analysis. Use when: first/last-touch, linear, time-decay, position-based revenue allocation."
- `audience-intelligence` — "Research target audiences. Use when: buyer personas, segmentation, Jobs-to-Be-Done, psychographic profiling, audience deep-dive."
- `audience-profile` — "Build detailed buyer personas. Use when: demographics, psychographics, behaviors, JTBD, content preferences."
- `autopilot-status` — "Check campaign autopilot status. Use when: health scores, auto-corrections, guardrail review, campaigns needing attention."
- `backlink-gap` — "Find referring domains that link to your competitors but not to you, ranked by an opinionated outreach-priority score with DR / link-overlap / traffic / topica
- `brand-setup` — "Set up or update a brand profile. Use when: new brand onboarding, client setup, brand switching, context update."
- `budget-optimizer` — "Optimize budget allocation. Use when: channel spend reallocation, data-driven budget planning, ROI-based justification."
- `budget-tracker` — "Track budget pacing in real time. Use when: cross-platform spend tracking, overspend alerts, reallocation recommendations."
- `c2pa-metadata` — "Embed C2PA (Content Authenticity Initiative) provenance manifests in AI-generated marketing assets (image/video/audio/PDF). Use when: preparing AI-generated ad
- `campaign-audit` — "Audit a brand's existing live campaigns across every active channel — paid, organic, email, social, content, SEO. Produce a current-state inventory, quick-wins
- `campaign-orchestrator` — "Orchestrate full campaign lifecycle. Use when: planning, launching, managing, UTM setup, media plan, post-mortem."
- `campaign-plan` — "Build multi-channel campaign plans. Use when: objectives, audience targeting, channel mix, budget, timeline, KPIs."
- `campaign-status` — "Check active campaign status. Use when: cross-platform execution history, performance metrics, pending approvals."
- `case-study-plan` — "Create case studies and success stories. Use when: client results showcase, portfolio piece, testimonial-based proof points."
- `check` — "Run the unified pre-publish quality gate on marketing content — hallucination detection, claim verification, brand voice scoring, structure validation. Use bef
- `churn-risk` — "Assess customer churn risk. Use when: churn scoring, at-risk segment identification, intervention playbook generation."
- `client-onboarding` — "Plan client onboarding. Use when: kickoff agenda, discovery questionnaire, account setup checklist, 30-60-90 day plan."
- `client-proposal` — "Draft agency proposals. Use when: pitch deck, scope of work, SLA, capabilities presentation for prospects or clients."
- `client-report` — "Generate client-facing reports. Use when: white-labeled performance report with KPIs, trends, strategic recommendations."
- `client-validation-document` — "Produce the Part 5 Client Validation Document — the one true stop where unbiased v1 findings meet the client. Each finding gets ACCEPT/REJECT/EDIT/DEFER decisi
- `cohort-analysis` — "Analyze customer cohorts. Use when: acquisition cohorts, retention curves, LTV by cohort, behavioral segmentation."
- `competitor-alerts` — "Configure competitor alerts. Use when: tracking content changes, pricing shifts, ad launches, SERP changes, social spikes."
- `competitor-analysis` — "Run competitive analysis. Use when: content, SEO, paid ads, social, AI visibility, pricing, positioning comparison."
- `competitor-monitor` — "Set up ongoing competitor monitoring. Use when: defining tracked competitors, scan frequency, change detection alerts."
- `competitor-pages` — "Create competitor comparison pages. Use when: \"X vs Y\" layouts, alternatives pages, feature matrices, roundup pages."
- `connect` — "Set up an MCP connector. Use when: connecting Google Ads, Salesforce, Mailchimp, or any service to the plugin."
- `content-brief` — "Create detailed content briefs. Use when: keyword targets, outline, structure, voice guidelines, SEO requirements."
- `content-calendar` — "Plan content calendars. Use when: monthly or quarterly scheduling, platform assignments, content pillars, repurposing."
- `content-decay-scan` — "Scan content library for decay signals: declining traffic, falling rankings, outdated stats, dropped AI citations. Prioritizes refresh opportunities by busines
- `content-engine` — "Create or optimize marketing content. Use when: blog posts, ad copy, emails, social posts, landing pages, voice guidelines."
- `content-repurpose` — "Repurpose content across channels. Use when: blog-to-social, webinar-to-article, pillar derivatives, format adaptation."
- `context-engine` — "Load brand context for marketing tasks. Use when: setting up brands, switching context, or needing industry benchmarks."
- `continuous-improvement-loop` — "Run Part 12 — the continuous improvement loop. Aggregates market + operating signals into product/offering recommendations. Runs alongside live operations, not
- `counter-narrative` — "Build counter-narrative playbooks. Use when: competitor rebrand, new category claim, aggressive campaign, price change response."
- `cowork-setup` — "One-shot setup that wires Digital Marketing Pro for team usage in Anthropic Cowork. Verifies the Cowork sandbox, checks for a Google Drive integration, creates
- `creative-health` — "Assess ad creative fatigue. Use when: ads underperform, need refresh timing, or creative lifecycle review."
- `creative-testing-framework` — "Design structured ad creative tests with A/B test plans, multivariate creative strategies, sample size calculations, and iteration cadences. Use when planning 
- `credential-switch` — "Switch brand credentials. Use when: activating the correct API keys for MCP servers in multi-client workflows."
- `crisis-response` — "Manage PR crises. Use when: reputational threat emerges, need stakeholder messaging, or communication timeline."
- `crm-sync` — "Sync data to CRM platforms. Use when: pushing contacts, deals, or campaigns to Salesforce, HubSpot, Zoho, or Pipedrive."
- `cro` — "Optimize conversion rates. Use when: auditing landing pages, testing forms, or improving checkout flow."
- `dark-funnel` — "Map invisible buyer journeys. Use when: tracking unattributed discovery, Reddit, AI chatbots, or word-of-mouth."
- `data-export` — "Export marketing data. Use when: sending data to BigQuery, Google Sheets, or Supabase for analysis or reporting."
- `data-import` — "Import data from external sources. Use when: loading CRM contacts, email lists, or campaign data from CSV, JSON, or Sheets."
- `digital-pr` — "Plan digital PR campaigns. Use when: pitching journalists, journalist-request responses, thought leadership, or E-E-A-T building."
- `email-sequence` — "Design email sequences. Use when: building subject lines, body copy, timing, segmentation logic, and deliverability plans."
- `emerging-channels` — "Explore emerging marketing channels. Use when: evaluating voice search, social commerce, or new platforms."
- `engagement-workflow` — "Run a full marketing engagement using the 12-Part methodology. Use when starting a new engagement, advancing parts, applying the Decision Matrix, or showing en
- `entity-audit` — "Audit brand entity consistency. Use when: checking Wikidata, Knowledge Panel, or directory discrepancies."
- `eval-config` — "Configure content eval settings. Use when: adjusting score thresholds, dimension weights, or auto-reject rules."
- `eval-content` — "Evaluate content quality. Use when: scoring drafts, checking hallucinations, or assessing brand voice compliance."
- `eval-suite` — "Batch evaluate multiple content pieces. Use when: scoring a content library, campaign assets, or deliverable set."
- `exec-summary` — "Generate C-suite executive summaries. Use when: preparing board reports, portfolio ROI, or strategic reviews."
- `executive-dashboard` — "Design executive marketing dashboards. Use when: building CMO reports, board metrics, or leadership views."
- `focus-group` — "Run synthetic focus groups. Use when: testing messaging, pricing, or positioning before live research spend."
- `four-core-documents` — "Produce the Four Core Documents at strategic depth (61 total steps): Business & SBU Analysis, Segmentation Framework, Brand Positioning, DMFlow. Use when runni
- `funnel-architect` — "Design marketing funnels. Use when: mapping customer journeys, attribution modeling, or conversion paths."
- `funnel-audit` — "Audit funnel performance. Use when: finding drop-off points, conversion gaps, or stage bottlenecks."
- `geo-monitor` — "Monitor brand AI visibility. Use when: tracking mentions in ChatGPT, Perplexity, Gemini, or AI Overviews."
- `growth-engineering` — "Engineer growth loops. Use when: building referral programs, viral loops, or product-led growth strategy."
- `growth-plan` — "Produce the 11-section Growth Plan — the flagship Part 8 client-facing deliverable that synthesises the entire engagement into a single executable strategy."
- `gsc-ai-performance` — "Query and interpret the new Google Search Console AI Performance Report (AI Overviews + AI Mode impressions/pages/countries/devices/dates). Use when: baselinin
- `help` — "Show the getting started guide, available commands, examples, and help for Digital Marketing Pro"
- `hreflang-check` — "Audit hreflang tags. Use when: checking missing tags, incorrect language codes, or x-default configuration."
- `image-seo-audit` — "Audit image SEO. Use when: checking alt text, file sizes, WebP/AVIF formats, lazy loading, or responsive images."
- `import-guidelines` — "Import brand guidelines. Use when: adding voice guides, style restrictions, or messaging frameworks."
- `import-sop` — "Import agency SOPs. Use when: adding workflow definitions, approval processes, or launch checklists."
- `import-template` — "Import deliverable templates. Use when: adding proposal formats, report structures, or brief templates."
- `influencer-brief` — "Create influencer campaign briefs. Use when: setting creator criteria, FTC compliance, or measurement plans."
- `influencer-creator` — "Plan influencer and creator partnerships. Use when: discovering creators, UGC campaigns, or FTC compliance."
- `integrations` — "Show MCP integration status. Use when: checking active connectors, available integrations, or skill unlocks."
- `intelligence-report` — "Generate marketing intelligence briefings from compound intelligence across agents — surfaces learnings, cross-agent patterns, confidence distribution, and pla
- `journey-design` — "Design cross-channel customer journeys. Use when: mapping touchpoints, branching logic, or stage transitions."
- `keyword-cluster` — "Build a content cluster plan from seed keywords — pillar+spokes architecture with internal-link map, intent grouping, and quality scorecard. Use when: planning
- `keyword-research` — "Research keyword expansion, intent, and gaps. Use when: mapping search intent, finding content gaps, or long-tail discovery."
- `landing-page-audit` — "Audit landing pages. Use when: scoring above-fold clarity, trust signals, form friction, message match, or mobile UX."
- `language-audit` — "Audit multilingual content consistency. Use when: checking language parity, regional compliance, or translation quality."
- `language-config` — "Configure language settings. Use when: setting primary languages, do-not-translate terms, or locale formatting."
- `launch-ad-campaign` — "Launch paid ad campaigns. Use when: deploying ads on Google, Meta, LinkedIn, or TikTok with targeting and safeguards."
- `launch-campaign` — "Orchestrate the full multi-channel launch of an approved campaign plan — pre-launch checklist, asset readiness gate, channel-by-channel activation, CRM campaig
- `launch-plan` — "Build product launch playbooks. Use when: planning pre-launch, launch day, or post-launch phases."
- `lead-import` — "Import leads into CRM. Use when: loading leads from forms, CSV, or manual entry with deduplication and scoring."
- `learn` — "Save a marketing learning or insight. Use when: capturing knowledge, recording campaign results, building compound intelligence."
- `live-dashboard` — "Create live Looker Studio dashboards. Use when: connecting marketing data sources with auto-configured visualizations."
- `local-seo` — "Build local SEO strategy. Use when: optimizing Google Business Profile, fixing NAP consistency, improving local pack rankings."
- `local-seo-audit` — "Audit local SEO health. Use when: reviewing GBP optimization, NAP consistency, local citations, or local pack rankings."
- `localize-campaign` — "Localize campaigns for multiple markets. Use when: translating assets, adapting references, adjusting compliance."
- `loop-detect` — "Identify and model growth loops. Use when: detecting viral, content, or paid loops, modeling effectiveness, proposing new loops."
- `market-weather` — "Assess current market conditions. Use when: checking economic indicators, cultural moments, or competitive activity."
- `marketing-automation` — "Design marketing automation workflows. Use when: building lead scoring, nurture sequences, drip campaigns, or behavioral triggers."
- `martech-audit` — "Audit the martech stack. Use when: evaluating marketing tools, recommending consolidation, or choosing between platforms."
- `media-plan` — "Create a paid media plan. Use when: building media buy schedules, cross-channel budget allocation, or creative rotation calendars."
- `message-test` — "Test message variants on synthetic audiences. Use when: predicting response rates, sentiment, or objections before live tests."
- `multilingual-score` — "Score localized content quality. Use when: checking translation accuracy, cultural adaptation, or voice preservation."
- `narrative-landscape` — "Map the competitive narrative landscape. Use when: analyzing positioning territories, gaps, competitor claims, differentiation."
- `narrative-tracker` — "Track AI engine brand narratives. Use when: detecting narrative drift, misrepresentation, or competitor narrative gains over time."
- `page-seo-analysis` — "Analyze SEO for a single page. Use when: auditing on-page signals, schema, content quality, E-E-A-T, or AI search readiness."
- `paid-advertising` — "Plan paid advertising campaigns. Use when: managing Google Ads, Meta Ads, LinkedIn Ads, bid strategy, or budget optimization."
- `pdf-report` — "Generate branded PDF reports. Use when: creating executive summaries, campaign reports, or client deliverables."
- `performance-check` — "Pull live marketing metrics for a performance snapshot: KPIs vs targets, trend comparison, and cross-platform overview. Use when checking current marketing per
- `performance-report` — "Generate performance reports. Use when: tracking KPIs, trend analysis, anomaly detection, and actionable recommendations."
- `pipeline-update` — "Update CRM pipeline. Use when: changing deal stages, values, notes, tracking velocity, or managing deal progression."
- `pr-pitch` — "Create media pitch packages. Use when: building pitch templates, media lists, outreach strategy, or journalist-request-platform responses (Qwoted, Featured, So
- `pricing-test` — "Test pricing strategies with synthetic data. Use when: simulating willingness to pay, price sensitivity, or optimal price points."
- `programmatic-seo` — "Plan programmatic SEO pages. Use when: building template engines, URL patterns, thin content safeguards, or quality gates."
- `prompt-test` — "A/B test content variations. Use when: comparing quality scores across prompt approaches, headline styles, or content versions."
- `publish-blog` — "Publish blog posts. Use when: deploying to WordPress or Webflow with SEO optimization, categories, and scheduling."
- `qbr-plan` — "Prepare a Quarterly Business Review. Use when: building QBR presentations, client performance reviews, or strategy updates."
- `quality-report` — "Generate quality trends report. Use when: reviewing eval scores over time, content type performance, or regression alerts."
- `rank-monitor` — "Monitor keyword rankings and SERP features. Use when: tracking keyword positions, detecting ranking drops, alerting on position changes, or tracking SERP-featu
- `recall` — "Recall marketing learnings. Use when: querying what we know about a channel, audience, objective, or past campaign."
- `redirect-manager` — "Manage URL redirects. Use when: creating 301/302 redirects, auditing chains, fixing loops, or deploying via CMS MCP."
- `region-config` — "Configure regional settings. Use when: setting timezone, language, compliance rules, currency, or local preferences."
- `reputation-management` — "Manage brand reputation. Use when: handling reviews, crisis comms, negative press, sentiment, or recovery plans."
- `retargeting-strategy` — "Design retargeting strategy. Use when: planning cross-platform remarketing, audience segmentation, or ad sequencing."
- `review-response` — "Respond to online reviews. Use when: drafting replies for Google, Yelp, G2, or building review response templates."
- `roi-calculator` — "Calculate marketing ROI. Use when: measuring campaign ROAS, CAC, CPL, LTV, or multi-channel attribution returns."
- `save-knowledge` — "Save brand knowledge to memory. Use when: persisting campaign learnings, guidelines, or competitive intel for retrieval."
- `schedule-social` — "Schedule social media posts. Use when: publishing to Twitter/X, Instagram, LinkedIn, TikTok, YouTube, or Pinterest."
- `search-knowledge` — "Search stored brand knowledge. Use when: recalling past learnings, voice guidelines, or competitor insights via semantic search."
- `segment-audience` — "Create audience segments. Use when: building or updating CRM or email platform segments for campaign targeting."
- `send-email-campaign` — "Send email campaigns. Use when: deploying via SendGrid, Klaviyo, Customer.io, Brevo, or Mailchimp with A/B testing."
- `send-notification` — "Send team notifications. Use when: pushing campaign updates, alerts, or approval requests via Slack or Intercom."
- `send-report` — "Deliver performance reports. Use when: sending KPI summaries via Slack, email, or Google Sheets with analysis."
- `send-sms` — "Send SMS or WhatsApp messages. Use when: deploying marketing messages via Twilio or Brevo with compliance checks."
- `seo-audit` — "Run comprehensive SEO audit. Use when: checking technical health, on-page, content quality, E-E-A-T, or link profile."
- `seo-drift` — "Compare two SEO snapshots (GSC, GSC AI Performance, rank tracker, AEO probe) and surface biggest movers per metric — impressions, clicks, position, AI citation
- `seo-implement` — "Execute SEO changes. Use when: updating meta tags, schema markup, canonicals, redirects, or indexing via CMS MCP."
- `seo-plan` — "Build SEO strategy and roadmap. Use when: planning site architecture, content strategy, or phased implementation."
- `serp-tracker` — "Deprecated — merged into rank-monitor. Use /digital-marketing-pro:rank-monitor --features for SERP-feature tracking (AI Overviews, snippets, PAA, local pack)."
- `share-of-voice` — "Measure share of voice. Use when: comparing keyword visibility, SERP presence, ad share, or AI citations vs competitors."
- `simulate` — "Simulate revenue impact via Monte Carlo. Use when: testing channel mix changes, budget shifts, or new channel launches."
- `sitemap-manager` — "Manage XML sitemaps. Use when: auditing sitemap health, generating sitemaps, or planning sitemap architecture."
- `social-strategy` — "Build social media strategy. Use when: defining content pillars, posting cadence, engagement tactics, or growth plans."
- `sop-library` — "Manage agency SOPs. Use when: creating, assigning, versioning, or auditing standard operating procedures."
- `status` — "Show a unified status snapshot of the active brand: profile, active engagements with current part, recent insights, recent compliance violations, Python depend
- `switch-brand` — "Switch active brand profile. Use when: changing brand context in multi-client or agency workflows."
- `sync-memory` — "Batch sync session learnings to memory. Use when: persisting campaign insights and performance history across sessions."
- `team-assign` — "Assign tasks to team members. Use when: distributing work by role, expertise, and capacity, or managing workloads."
- `tech-seo-audit` — "Run technical SEO audit. Use when: checking Core Web Vitals, crawlability, indexation, speed, or structured data."
- `technical-seo` — "Deep technical SEO analysis. Use when: optimizing crawlability, Core Web Vitals, rendering, redirects, or sitemaps."
- `translate-content` — "Translate marketing content. Use when: localizing with brand voice preservation, quality scoring, or transcreation."
- `validate-output` — "Validate content structure. Use when: checking schema compliance, required sections, word count, or placeholders."
- `validate-profile` — "Validate a brand profile end-to-end — required fields, voice/audience completeness, connector reachability, credentials health, and compliance prerequisites — 
- `verify-claims` — "Verify marketing claims. Use when: cross-checking statistics, awards, certifications, or performance claims with sources."
- `video-script` — "Write video scripts. Use when: creating YouTube, TikTok, Reels, LinkedIn, demo, or explainer video content."
- `webinar-plan` — "Plan webinars and virtual events. Use when: designing promotion, content, registration, and post-event follow-up."
- `what-if` — "Compare budget scenarios side-by-side. Use when: testing 2-4 allocation variants with projected outcomes."
- `yearly-planner` — "Produce the 12-month operational Yearly Planner — the calendar companion to the Growth Plan in Part 8. Translates strategy into month-by-month execution."
