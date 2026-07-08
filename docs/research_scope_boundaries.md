# Research Scope: AI's Impact on the Australian Embedded/Firmware Engineer Job Market

> **Version**: 1.0  
> **Date**: 2026-07-08  
> **Status**: Draft for review

---

## 1. Research Questions

### Primary Question
**RQ1:** How has the availability and nature of embedded/firmware engineering roles in Australia changed between 2022 and 2026, and what measurable role has AI adoption played in those changes?

### Secondary Questions

**RQ2:** Which specific embedded/firmware tasks or sub-domains (e.g., driver development, RTOS configuration, PCB-level debugging, CI for firmware) are most susceptible to automation or augmentation by current-generation AI tools, and which remain resilient?

**RQ3:** What skills, tools, and credentials are Australian employers prioritising in embedded/firmware job postings as AI-assisted development becomes more common (e.g., requirement for AI tool proficiency, increased emphasis on system-level thinking, demand for verification/testing skills)?

**RQ4:** How do salaries, contract rates, and required experience levels for embedded/firmware roles in Australia compare before and after the widespread availability of LLM-based coding assistants (i.e., pre-2023 vs 2024-2026)?

**RQ5:** What gaps exist between (a) the AI-related competencies expected by employers and (b) the current curricula of Australian tertiary engineering/CS programs for embedded systems?

---

## 2. Scope Boundaries

### Included

| Dimension | Included |
|-----------|----------|
| **Geography** | Australia only (national aggregate, plus state-level breakdowns for NSW, VIC, QLD, WA) |
| **Timeframe** | January 2022 to July 2026 |
| **Job roles** | Embedded Software Engineer, Firmware Engineer, Embedded Systems Engineer, IoT Firmware Engineer, Principal Embedded Engineer, Hardware/Firmware co-design roles |
| **Industry sectors** | Consumer electronics, industrial automation, medical devices, automotive, aerospace/defence, agtech, energy/utilities |
| **AI tools** | LLM-based coding assistants (GitHub Copilot, Claude Code, Cursor, Amazon Q Developer), automated testing/fuzzing tools, AI-assisted PCB design tools |
| **Data types** | Job board postings, salary surveys, industry reports, academic literature, employer skill surveys |

### Excluded

| Dimension | Excluded | Rationale |
|-----------|----------|-----------|
| **Geography** | New Zealand, SE Asia, global averages | Keeps sample homogeneous for policy/education recommendations |
| **Timeframe** | Pre-2020 data | Labour market and AI capabilities pre-2020 are too dissimilar to inform current decisions |
| **Job roles** | Pure software engineering (web, mobile, data science), IT support, hardware-only roles (no firmware component) | Scope must remain tractable and focused on the intersection of hardware and software |
| **AI tools** | General AI/ML frameworks (PyTorch, TensorFlow), AI for chip design (EDA) | These constitute a different labour category (ML engineer, digital design engineer) |
| **Education** | International university comparisons, primary/secondary school curricula | Australian tertiary education only; scope excludes pre-tertiary |
| **Policy** | Immigration/visa policy analysis, government R&D tax incentive impact | Policy factors are acknowledged as confounders but not analysed in depth |

---

## 3. Methodology Outline

### Phase 1: Data Collection (Weeks 1-3)

1. **Job board scraping / querying**
   - Programmatically query Seek, LinkedIn, Indeed (via their APIs or structured search) for embedded/firmware roles in Australia.
   - Collect structured fields: title, location, salary range, required skills, experience level, posting date.
   - Target minimum N = 500 unique postings across the 2022-2026 window.

2. **Salary and industry surveys**
   - Source annual reports from ACS (Australian Computer Society), Engineers Australia, and Hays Technology.
   - Extract embedded/firmware-specific salary bands and hiring sentiment.

3. **Academic literature search**
   - Database: IEEE Xplore, ACM Digital Library, Scopus.
   - Search terms: ("AI-assisted development" OR "LLM" OR "code generation") AND ("embedded systems" OR "firmware" OR "IoT").

4. **Employer / recruiter perspectives**
   - Semi-structured interviews or structured surveys with 5-10 Australian engineering managers / recruiters specialising in embedded roles.

### Phase 2: Analysis (Weeks 4-6)

1. **Trend analysis** (RQ1, RQ4)
   - Time-series decomposition of job posting volume, salary bands, and seniority requirements.
   - Statistical tests (e.g., Mann-Kendall trend test, change-point detection) for structural breaks around late 2023 / early 2024.

2. **Skill frequency analysis** (RQ3)
   - NLP pipeline: tokenise job descriptions, extract skill bigrams/trigrams, compute TF-IDF-weighted frequency shifts pre- vs post-2024.
   - Identify skills whose relative frequency changes by >20% between periods.

3. **Task susceptibility mapping** (RQ2)
   - Develop a rubric (Automation Augmentation Resilience potential) based on: task repetitiveness, safety-criticality, availability of ground-truth test oracles, need for hardware-in-the-loop context.
   - Survey practitioners or use expert elicitation (N = 5) to score common embedded tasks against the rubric.

4. **Curriculum gap analysis** (RQ5)
   - Map top-20 demanded skills from Phase 2 against unit offerings in 5-8 Australian universities' engineering/CS programs (public course handbooks, 2025-2026).
   - Quantify coverage gaps.

### Phase 3: Synthesis & Reporting (Week 7)

- Triangulate findings across data sources.
- Produce the deliverables listed in Section 6.
- Peer review by one industry practitioner and one academic.

### Limitations & Mitigations

| Limitation | Mitigation |
|------------|------------|
| Job board data may not reflect unadvertised roles | Supplement with recruiter interviews and LinkedIn talent pool estimates |
| Salary data is self-reported or banded | Use multiple survey sources and report ranges, not point estimates |
| AI tool adoption metrics are sparse | Proxy via job description mentions, vendor market reports, and practitioner surveys |
| Attribution problem (AI vs macroeconomics) | Acknowledge confounders (e.g., interest rates, CHIPS Act tail-effects) and use qualitative evidence to bound claims |

---

## 4. Key Data Sources

### Job Boards & Labour Market Data

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| Seek (au.seek.com) | Job listings | Public web / API (RapidAPI) | Largest AU job board; structured salary data often available |
| LinkedIn Jobs | Job listings | Public web / API | Good for skills extraction and company-level aggregation |
| Indeed Australia | Job listings | Public web / API (Indeed Publisher) | Broad coverage; salary estimates less reliable |
| Labour Market Information Portal (LMIP) | Government statistics | Public (data.gov.au) | Occupation-level trends (ANZSCO codes for ICT Professionals) |
| Burning Glass Technologies / Lightcast | Labour market analytics | Licensed (university access possible) | Granular skill taxonomy; widely used in education gap analyses |

### Industry & Salary Reports

| Source | Type | Frequency |
|--------|------|-----------|
| Hays Technology Salary Guide | Salary survey | Annual |
| ACS Australia's Digital Pulse | Industry workforce report | Annual |
| Engineers Australia Professional Engineer Remuneration Report | Salary survey | Biennial |
| Robert Half Technology Salary Guide | Salary survey | Annual |
| TECHD (Technology, Engineering & Cybersecurity Hiring Digest) | Market report | Quarterly |

### Academic Databases

| Database | Coverage | Access |
|----------|----------|--------|
| IEEE Xplore | Engineering, electronics, embedded systems | Institutional |
| ACM Digital Library | Software engineering, HCI | Institutional |
| Scopus | Multidisciplinary | Institutional |
| arXiv (cs.SE, cs.AI) | Preprints | Open |

### AI Tool Adoption Data

| Source | Type | Notes |
|--------|------|-------|
| GitHub Octoverse / Copilot reports | Vendor data | Adoption rates, language breakdowns by region |
| Stack Overflow Developer Survey | Self-report survey | Questions on AI tool usage from 2023 onward |
| JetBrains Developer Ecosystem Survey | Self-report survey | Annual, with AI-specific sections since 2023 |
| McKinsey / BCG reports on generative AI in engineering | Consulting reports | Strategic context; limited AU-specific data |

---

## 5. Expected Outcomes & Deliverables

### Primary Deliverable

- **Research Report** (PDF / Markdown): A structured document answering RQ1-RQ5, including executive summary (2 pages), full analysis (~20-30 pages), and technical appendices.

### Supporting Deliverables

| # | Deliverable | Format | Description |
|---|-------------|--------|-------------|
| D1 | Job market trend dashboard | Interactive HTML (plotly/d3) | Time-series of role counts, salary bands, and top skills by quarter, filterable by state and industry |
| D2 | Skills shift matrix | Table (CSV + visual heatmap) | Pre/post AI-era frequency comparison for 50+ embedded/firmware skills |
| D3 | Task susceptibility rubric | PDF / Markdown | Rubric scores for 20-30 common embedded engineering tasks, with rationale |
| D4 | Curriculum gap analysis | Table (Markdown) | Mapping of employer-demanded skills to university unit offerings with gap classification (covered / partial / absent) |
| D5 | Practitioner interview synthesis | Markdown | Thematic summary of 5-10 interviews with engineering managers and recruiters |
| D6 | Raw dataset (anonymised) | CSV | Job postings, salary survey extracts, interview notes (where consent allows) |

### Potential Impact

- **For engineering managers**: Evidence-based hiring strategy and team upskilling roadmap.
- **For educators**: Identified gaps to feed curriculum renewal cycles.
- **For engineers**: Data-driven career planning — which skills to deepen vs broaden.
- **For policymakers**: Baseline for workforce development and migration skill lists.

---

## References (Initial)

1. ACS. (2025). *Australia's Digital Pulse 2025*. Australian Computer Society.
2. Engineers Australia. (2024). *Professional Engineer Remuneration Report 2024*.
3. Hays. (2025). *Hays Technology Salary Guide FY2025/26*.
4. GitHub. (2025). *Octoverse 2025: The State of Open Source and AI Adoption*.
5. Stack Overflow. (2025). *2025 Developer Survey Results*.
6. JetBrains. (2025). *Developer Ecosystem Survey 2025*.
7. Lightcast. (2025). *Australian Labour Market Data* [Dataset].
8. Australian Government. (2025). *Labour Market Information Portal – Occupation Summaries*.
