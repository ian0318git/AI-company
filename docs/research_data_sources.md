# Research Data Sources: AI's Impact on Australian Embedded/Firmware Engineer Job Market

> Compiled: 2026-07-08
> Purpose: Systematic identification of data sources for studying how AI is reshaping embedded/firmware engineering roles in Australia.

---

## 1. Academic Databases

### 1.1 IEEE Xplore
- **URL:** https://ieeexplore.ieee.org
- **Search Strategy:** `(("artificial intelligence" OR "machine learning" OR "LLM" OR "code generation") AND ("embedded systems" OR "firmware" OR "microcontroller") AND ("labour market" OR "workforce" OR "employment" OR "job displacement"))`
- **Why it matters:** IEEE is the primary publisher for embedded systems, firmware, and hardware-adjacent computing research. Key conferences (ICSE, ASE, DAC, EMSOFT) and journals (IEEE Software, IEEE Micro) publish on both embedded engineering and AI displacing/redefining software roles.
- **Supplementary search:** `"software engineer" AND ("productivity" OR "automation") AND ("impact" OR "employment")` filtered by publication year >= 2022.

### 1.2 ACM Digital Library
- **URL:** https://dl.acm.org
- **Search Strategy:** Full-text search for `("large language model" OR "code completion" OR "AI-assisted") AND ("embedded" OR "firmware" OR "real-time") AND ("labour" OR "occupation" OR "skill" OR "hiring")` with filters for conference proceedings (ICSE, ESEC/FSE, CHI) and journals (ACM Computing Surveys, TOSEM).
- **Why it matters:** ACM venues increasingly publish empirical studies on AI-assisted programming (e.g., Copilot evaluations) and workforce effects. CHI proceedings also cover human-computer interaction aspects of AI tools in engineering workplaces.

### 1.3 Scopus
- **URL:** https://www.scopus.com
- **Search Strategy:** `TITLE-ABS-KEY(("embedded engineer" OR "firmware engineer" OR "software engineer") AND ("artificial intelligence" OR "generative AI" OR "large language model") AND ("job" OR "occupation" OR "labour" OR "wages" OR "demand"))` limited to Computer Science and Economics subject areas, 2020 onward.
- **Why it matters:** Scopus provides broader cross-disciplinary coverage than IEEE/ACM alone. Useful for tracking grey literature, preprints, and cross-domain studies (CS + economics + education).

### 1.4 Google Scholar
- **URL:** https://scholar.google.com
- **Search Strategy:** Multiple query strings:
  - `"AI impact" "embedded systems" "job market"`
  - `"generative AI" "firmware engineer" "demand"`
  - `"AI-assisted coding" productivity embedded`
  - `"large language model" "occupation" "australia"`
- **Why it matters:** Google Scholar indexes preprints (arXiv, SSRN), working papers, and theses that may not appear in subscription databases. Set alerts (`AI impact embedded engineer Australia`) for ongoing monitoring.

### 1.5 arXiv (cs.SE, cs.AI, econ.GN)
- **URL:** https://arxiv.org
- **Search Strategy:** Browse categories `cs.SE` (Software Engineering), `cs.AI` (Artificial Intelligence), and `econ.GN` (General Economics). Search for `"code generation" AND productivity`, `"large language model" AND occupation`, `"firmware" AND automation`.
- **Why it matters:** Rapid publication of preprints on LLM evaluation, Copilot/GitHub studies, and labour economics of AI. Search at least monthly for new submissions.

### 1.6 Web of Science
- **URL:** https://www.webofscience.com
- **Search Strategy:** `TS=((artificial OR AI OR LLM OR "generative") AND (embedded OR firmware OR microcontroller) AND (employment OR occupation OR wage OR "skill demand"))` restricted to 2020 onward.
- **Why it matters:** High-quality citation indexing. Useful for identifying highly cited papers (impact indicators) and tracking how AI-and-jobs research has evolved over time.

---

## 2. Industry Reports

### 2.1 McKinsey Global Institute
- **URL:** https://www.mckinsey.com/mgi
- **Search Strategy:** Site search for `"generative AI" AND ("workforce" OR "automation" OR "software development")` and specifically the 2023 reports *Generative AI and the Future of Work in Australia* and *The Economic Potential of Generative AI*.
- **Why it matters:** McKinsey's quantified estimates of automation potential by occupation and industry are frequently cited by policymakers. Their occupational taxonomy allows cross-walking to embedded engineer categories.

### 2.2 Deloitte — "Tech Trends" & "Human Capital Trends"
- **URL:** https://www.deloitte.com/au/en/issues/technology.html
- **Search Strategy:** Filter by country (Australia), tag "Technology" and "Workforce". Look for annual *Tech Trends* report (engineering chapters) and *Global Human Capital Trends* relating to AI-augmented work.
- **Why it matters:** Deloitte's Australian practice provides region-specific analysis. Their *Tech Trends* report often includes case studies relevant to engineering workforce shifts.

### 2.3 World Economic Forum — "Future of Jobs Report"
- **URL:** https://www.weforum.org/reports/the-future-of-jobs-report-2025/
- **Search Strategy:** Search for "embedded systems" or "software developer" within the report data. Download the full dataset (Excel/CSV) for custom analysis — it includes job family scores for automation risk, augmentation, and skill demand.
- **Why it matters:** WEF provides the most structured cross-country data on job displacement and creation by technology, disaggregated by occupation. The raw dataset allows filtering for Australian-specific responses.

### 2.4 CSIRO — Responsible AI & Future of Work
- **URL:** https://www.csiro.au/en/research/technology-space/ai
- **Search Strategy:** Search `"responsible AI" workforce engineering`, `"digital skills" Australia report`, and browse CSIRO's *Data61* publications on AI and decision-making.
- **Why it matters:** CSIRO is Australia's national science agency. Their *Australia's AI Ecosystem* reports are the authoritative domestic source on AI adoption across sectors, including engineering.

### 2.5 ACS Australia — "Australia's Digital Pulse" & "ACS Digital Skills Gap"
- **URL:** https://www.acs.org.au/policy-advocacy.html
- **Search Strategy:** Find annual *Australia's Digital Pulse* report and any ACS surveys on AI hiring trends. Look for *ICT Workforce Report* — section on embedded/industrial engineering. Use the ACS Jobs Index (monthly) for near-real-time trends.
- **Why it matters:** ACS (Australian Computer Society) produces the most granular Australian ICT labour data. Their reports segment by occupation and geography, and their policy submissions directly reference AI's impact on tech roles.

### 2.6 AlphaBeta / Access Economics (now part of Deloitte)
- **URL:** https://www.alphabeta.com (redirects to Deloitte)
- **Search Strategy:** Search Deloitte Australia's site for "AlphaBeta" reports on automation, with filter "Technology" and "Future of Work".
- **Why it matters:** AlphaBeta produced foundational AI-economy work for the Australian government (e.g., *The Net Benefit of AI in Australia*) that includes per-occupation estimates.

### 2.7 Robert Half / Hays / Michael Page — Salary & Hiring Guides
- **URLs:**
  - https://www.roberthalf.com/au/en/salary-guide
  - https://www.hays.com.au/salary-guide
  - https://www.michaelpage.com.au/salary-guide
- **Search Strategy:** Search for `"embedded engineer" salary Australia`, `"firmware engineer" hiring trend`. Download the annual guide PDFs and extract the "Engineering" or "Technology" sections.
- **Why it matters:** Recruitment agencies publish forward-looking demand signals and salary benchmarks. Year-over-year comparisons can show if employer demand for embedded skills is rising or falling relative to other software roles.

### 2.8 OECD — Employment Outlook & Skills for Jobs
- **URL:** https://www.oecd.org/en/topics/employment.html
- **Search Strategy:** Search for "ICT employment" and "automation risk" by country (Australia). Use the OECD *Skills for Jobs* database (https://www.oecdskillsforjobsdatabase.org) for skill shortage indicators.
- **Why it matters:** OECD provides internationally comparable data on skill shortages, automation risk scores per occupation, and wage trends — enabling benchmarking of Australia against other economies.

---

## 3. Australian Job Boards & Labour Market Data

### 3.1 SEEK — Talent Insights & Employment Data
- **URL:** https://www.seek.com.au
- **Search Strategy:**
  - Manual search: `"embedded engineer"`, `"firmware engineer"`, `"embedded software engineer"` — record job count, salary range, posted date.
  - SEEK Talent Insights: https://insights.seek.com.au — use "Advertised Salary Trends" tool filtered by "Engineering" and "Information & Communication Technology" categories.
  - Track keyword frequency in job ads: "AI", "machine learning", "Python" (vs bare-metal C).
- **Why it matters:** SEEK is Australia's dominant online job board (~60% market share). The combination of job ad counts (volume), salary range, and skill keywords provides the richest longitudinal data set. Ad descriptions include required technologies (C, C++, FreeRTOS, ESP-IDF, etc.), revealing how AI skills interact with traditional embedded requirements.

### 3.2 Indeed Australia
- **URL:** https://au.indeed.com
- **Search Strategy:** `"embedded firmware"` OR `"embedded systems engineer"` OR `"firmware engineer"`. Use Indeed's "Trending Searches" page and Indeed Hiring Lab (https://www.hiringlab.org/au) for wage and demand trend reports.
- **Why it matters:** Indeed complements SEEK with different listings (including smaller firms and contract roles). Indeed Hiring Lab publishes data-driven research on Australian labour market tightness by occupation.

### 3.3 LinkedIn — Talent Insights & Job Trends
- **URL:** https://www.linkedin.com
- **Search Strategy:**
  - Talent Insights tool: search occupation = "Embedded Software Engineer" (or "Firmware Engineer") in Australia. Track hiring rate, skills distribution, and talent flow (where people move).
  - Job search: `"embedded" + "firmware" + Australia`, filter by "Past month", note total openings.
  - Skills page: look at "Embedded C" skill — note how many members list it vs "C++" vs "Python" vs "AI/ML".
- **Why it matters:** LinkedIn provides the best view of the talent pool size (members listing these roles), skill adjacency (what other skills people with Embedded C have), and hiring rate (proportion of members changing roles in the last 90 days). Their *Workforce Report* data (when available) specifically tracks ICT occupations.

### 3.4 Hays Salary Guide (Australia-specific edition)
- **URL:** https://www.hays.com.au/salary-guide
- **Search Strategy:** Download the annual *Hays Salary Guide* PDF. Look for "Embedded Software Engineer", "Firmware Engineer", "IoT Engineer" in the Technology section. Note year-over-year salary changes and commentary on hiring difficulty (i.e., "skills in shortage" markers).
- **Why it matters:** Hays is the most widely referenced salary guide for Australian engineering employers. Includes a "Skills in Shortage" indicator that signals whether embedded roles are becoming harder (or easier) to fill — a proxy for demand pressure.

### 3.5 Adzuna Australia (via Labour Market Insights portal)
- **URL:** https://www.adzuna.com.au (aggregated by Australian Government)
- **Search Strategy:** Visit https://labourmarketinsights.gov.au and use the "Occupation" filter to look at ICT or Engineering Technologist categories. Adzuna powers the government's job advertisement aggregation.
- **Why it matters:** Adzuna underpins the Australian Government's official job advertisement data, providing a near-census view of online job ads. Can cross-reference SEEK/Indeed numbers.

---

## 4. Government & Official Sources

### 4.1 Australian Bureau of Statistics (ABS) — Labour Force Survey
- **URL:** https://www.abs.gov.au/statistics/labour
- **Key Datasets:**
  - **Labour Force, Australia (cat. 6202.0):** Monthly employment/unemployment by occupation (ANZSCO groups).
  - **Employment and Earnings, Public Sector (cat. 6248.0.55.003):** Wage data by occupation.
  - **Characteristics of Employment (cat. 6333.0):** Contract type, hours, multiple job-holding — relevant for embedded contractors.
  - **Job Vacancies (cat. 6354.0):** Quarterly vacancy counts by industry (look for "Professional, Scientific and Technical Services").
- **Search Strategy:** Use ABS TableBuilder or microdata (DataLab) to extract occupation-level data for "Software and Applications Programmers" (ANZSCO 2613) and "ICT Support and Test Engineers" (ANZSCO 2632). The key challenge: embedded/firmware is not a separate ANZSCO code — it is nested within broader categories.
- **Why it matters:** ABS is the definitive source for official employment counts, unemployment rates, hours worked, and wage trends. However, the ANZSCO classification does not have a dedicated "embedded engineer" code, so extraction requires careful proxy matching.

### 4.2 Jobs and Skills Australia (formerly Department of Employment)
- **URL:** https://www.jobsandskills.gov.au
- **Key Products:**
  - **National Skills Commission — Occupation Profiles:** Search "Telecommunications Engineering Professionals" (ANZSCO 2633) or "Software and Applications Programmers" (ANZSCO 2613).
  - **Skills Priority List (annual):** Shows occupations in national shortage.
  - **Labour Market Updates:** Monthly/quarterly reports with state-level analysis.
  - **Internet Vacancy Index (IVI):** Time series of online job ads by occupation (derived from Adzuna data).
- **Search Strategy:** Download the IVI time series. Filter for ANZSCO minor groups 2613 (Software and Applications Programmers) and 2633 (Telecommunications Engineering Professionals). Check the *Skills Priority List* for any embedded/firmware-related occupations reported as in shortage.
- **Why it matters:** Jobs and Skills Australia produces the most comprehensive domestic data on occupation-level shortages, skill demand, and future workforce projections. Their *Internet Vacancy Index* is the primary indicator of short-run demand changes.

### 4.3 Department of Home Affairs — Skilled Migration Data
- **URL:** https://www.homeaffairs.gov.au/research-and-statistics/statistics/visa-statistics
- **Key Datasets:**
  - **Skilled Migration Program outcomes:** Number of sponsored visas by occupation and industry.
  - **Temporary Skill Shortage (TSS) / Subclass 482 visas:** Approved nominations by occupation (ANZSCO).
  - **Employer Nomination Scheme (ENS):** Permanent sponsored positions.
- **Search Strategy:** Filter visa grants by ANZSCO code. The most likely codes for embedded roles are:
  - 233411 — Electronics Engineer
  - 263311 — Telecommunications Engineer
  - 261312 — Developer Programmer (broadest, likely includes many firmware roles)
  - 261399 — Software and Applications Programmers (nec)
- **Why it matters:** Skilled visa data reveals if employers are turning to overseas recruitment to fill embedded roles — a strong signal of domestic shortage. A decline in visa sponsorship for these codes (while AI tooling improves) would be a noteworthy trend.

### 4.4 Department of Industry, Science and Resources
- **URL:** https://www.industry.gov.au
- **Key Reports:**
  - **The State of AI in Australia:** Periodic report on AI adoption across industries.
  - **Critical Technologies List:** Identifies technologies (including AI and advanced manufacturing) that the government prioritises.
  - **Technology and Skills reports** examining the defence/manufacturing workforce (major embedded systems employers).
- **Search Strategy:** Search for "artificial intelligence adoption engineering", "cyber-physical skills", "defence industry workforce". Cross-reference the Critical Technologies List with engineering occupation projections.
- **Why it matters:** Australian Government-funded reports on AI adoption provide official adoption rates by sector, including manufacturing and engineering services — key embedded employer verticals.

### 4.5 CSIRO Data61 — AI Adoption & Workforce Data
- **URL:** https://data61.csiro.au
- **Search Strategy:** Browse "AI enabled workforce" publications and any longitudinal surveys of Australian firms on AI adoption. Search for "AI risk perception" surveys that include engineering occupations.
- **Why it matters:** Data61's survey-based research on Australian firms' AI adoption provides the most reliable domestic adoption statistics, segmented by industry. This directly feeds into demand-side analysis.

---

## 5. International Benchmarks & Supplementary Sources

| Source | URL | Why It Matters |
|--------|-----|----------------|
| US Bureau of Labor Statistics (BLS) | https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm | Comparable US occupation projections for "Software Developers" and "Electrical Engineers" — benchmark against Australia |
| European Commission — Digital Economy & Society Index (DESI) | https://digital-strategy.ec.europa.eu/en/policies/desi | ICT employment share and digital skills by EU country — context for how Australia compares |
| Stack Overflow Developer Survey | https://survey.stackoverflow.co/2025/ | Embedded developer segment size, salaries, tools used, AI tool adoption rates (yearly) |
| GitHub Octoverse / Copilot Reports | https://github.blog/news-insights/octoverse/ | Geography-specific data on AI-assisted coding adoption; language popularity trends (C vs C++ vs Rust in embedded) |
| ITU (International Telecommunication Union) | https://www.itu.int/en/ITU-D/Statistics/Pages/stat/default.aspx | ICT development and skills benchmarks across countries |
| Pew Research Center | https://www.pewresearch.org/internet/ | Surveys on AI sentiment and workplace technology adoption by occupation |

---

## 6. Data Quality & Limitations

1. **ANZSCO classification gap:** Australian occupational codes do not have a dedicated "embedded/firmware engineer" category. Most embedded roles fall under "Software and Applications Programmers" (2613), "Electronics Engineer" (2334), or "ICT Support and Test Engineers" (2632). **Mitigation**: use multiple proxy codes and document the classification uncertainty in analysis.
2. **Job board duplications:** SEEK, Indeed, and LinkedIn often carry duplicate listings. **Mitigation**: cross-reference unique employer counts, not just raw job ad counts.
3. **Pub date filtering:** The AI job-market literature shifted significantly after ChatGPT (Nov 2022). Filter searches to 2020–present, with sub-analysis for pre-2023 vs 2023 onward.
4. **Paywalled data:** Scopus, Web of Science, and some McKinsey/Deloitte reports sit behind paywalls. Use institutional access (university library). ABS microdata requires registration via DataLab.

---

## 7. Monitoring Plan

| Frequency | Data Source | Action |
|-----------|-------------|--------|
| **Weekly** | SEEK job search (API or manual scrape) | Record job count for embedded/firmware searches; note AI keyword frequency |
| **Monthly** | LinkedIn Talent Insights, arXiv | Check hiring rate changes; review new preprints on AI x engineering |
| **Quarterly** | ABS Labour Force, IVI, Jobs & Skills Australia updates | Update employment and vacancy trends |
| **Annually** | WEF Future of Jobs, ACS Digital Pulse, Hays Salary Guide, Stack Overflow Survey | Integrate into year-on-year comparison dataset |
