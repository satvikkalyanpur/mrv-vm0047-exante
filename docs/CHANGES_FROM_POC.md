# Changes from the proof of concept

The proof of concept (`mrv-reference-pipeline`, doi:10.5281/zenodo.22026520) asked how much the credit figure for the existing garden moves when methodology choices change. This repository asks a different question: under VM0047's actual rules, how many credits would a new planting on that parcel earn?

Reading the methodology closely to answer that showed several places where the proof of concept, and the slides built on it, do not match VM0047. They are listed here with what was done about each.

## 1. An existing garden is not creditable

VM0047 credits activities that increase vegetative cover. For dense planting it then applies a performance benchmark: growth in the project is compared with growth in matched control plots, and only the difference counts (Appendix 1, Eq. A6). A mature garden grows like the gardens around it, so the benchmark is 1 and the credited share is zero.

The proof of concept reported 0.51 to 0.98 t CO₂e a year for the existing garden. That is the garden's growth after deductions. It is not an amount VM0047 would issue.

**Now:** the scenario is an explicit what-if for a new planting. The benchmark is in the credit equation and tested, including the existing-garden case.

## 2. The uncertainty rule was stated too simply

The proof of concept and slide 6 say "minimum 10 % uncertainty deduction (90 % CI)". VM0047 has two rules:

- **Ex ante** (estimates made before measurement): a deduction of at least 10 % (Section 8.6).
- **Ex post** (at verification): UNC = max(0, U − 10 %), where U is the 90 % confidence half-width as a share of the estimate (Eqs. 27, 28). The first ten points are free, so a well-measured project deducts nothing.

**Now:** both rules are implemented. This repository is ex ante, so the 10 % floor applies.

## 3. A 10 % buffer is below the floor

The proof of concept varied the buffer over 10 %, 20 % and 40 %. The AFOLU Non-Permanence Risk Tool v4.2 sets a minimum rating of 12 (Section 2.5.2), so 10 % is not available. The top of the published range (0.98) used it; with a 12 % buffer that case gives about 0.96.

**Now:** the engine will not go below 12 and refuses a rating above 60.

## 4. Leakage was missing

VM0047's area-based approach requires leakage to be assessed with VMD0054. The proof of concept had no leakage term in its final version.

**Now:** VMD0054's displaced-production steps are implemented. The scenario plants on fallow land, where leakage is zero, and reports what would happen on working cropland.

## 5. The biomass equation changed, and this is the largest change

The proof of concept used Prayogo et al. (2018), fitted in Indonesia. VM0047 asks for species equations from the same region first. Das et al. (2021) fitted equations to 40 areca palms cut and weighed in Assam, including roots.

| Equation | Fitted in | 10-year credits | Notes |
|---|---|---|---|
| Prayogo 2018 (H × D^1.2) | Indonesia | 24.1 | Used in the proof of concept |
| **Das 2021, height model** | India | **43.1** | All 8 cultivars within the calibration range |
| Das 2021, D²H model | India | 96.2 | Authors' preferred model, but 3 of 8 cultivars have diameters above its range |

**Now:** the height model is the default. It is from India, it covers every input, and it is the lower of the two Indian models. The other two remain as options and appear in the sensitivity chart. The choice is one line in the scenario file.

This is a judgement, and a verifier may see it differently. The spread between equations (24 to 96) is larger than every deduction combined, which is a result worth reporting in its own right.

## 6. Root share is now a measured species value

The proof of concept compared 0.15 and 0.24. Das et al. measured 80 % of biomass above ground and 20 % below on excavated areca palms, a root-to-shoot ratio of 0.25.

## 7. Tree sizes are now cited

The proof of concept assumed a 12 cm stem and a height of 10.0 m rising to 10.4 m. This repository uses measured height and diameter of 10-year-old palms of eight cultivars at Thirthahalli, roughly 65 km from the parcel in the same Malnad zone, planted at 2.7 m × 2.7 m (Bhoomika et al. 2023). The scenario adopts that spacing. They are still not measurements of this parcel.

## 8. No Earth Engine needed

The what-if is a calculation from published measurements, so the notebook runs without any login. The satellite check from the proof of concept is kept as an optional last cell.

## Unchanged

Carbon fraction 0.47, the 44/12 conversion, soil carbon excluded, the parcel boundary, and the SHA-256 hash chain.

---

## What to update in the slides

| Slide | Says | Should say |
|---|---|---|
| 6, Credit engine | "≥10 % uncertainty deduction (90 % CI), permanence buffer and leakage" | "Performance benchmark, uncertainty (≥10 % ex ante; ex post only the excess over 10 %), leakage, buffer ≥12 %" |
| 16, Carbon MRV | "Planned: full uncertainty, buffer and leakage coverage" | These are now built |
| 16, Methodology rules | "Planned: deeper rule coverage" | Built: benchmark, uncertainty, leakage and buffer rules, with tests |
| 18, Credit estimate | "(AGB + BGB) − uncertainty deduction − permanence buffer" | Add the performance benchmark and leakage |
| 18, Experiment | Buffer "10/20/40 %" | 10 % is below the 12 % floor; rerun with 12/20/40 |
| 18, Result | "0.51 – 0.98 t CO₂e/yr" presented as credits | Growth after deductions on an existing garden; VM0047 would not issue it |
