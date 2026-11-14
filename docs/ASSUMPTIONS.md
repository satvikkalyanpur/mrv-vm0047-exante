# Assumptions

Everything the result depends on that is not a methodology rule or a published measurement, and which way each one pushes the answer.

| Assumption | Value | Effect on credits | What would replace it |
|---|---|---|---|
| The parcel is fallow, with no woody cover, at the start | 0 % woody cover | Makes the scenario possible at all. The real parcel is an established garden. | A real candidate site, with a 10-year satellite record |
| Nothing is grown on the land before planting | No displaced production | Raises credits: leakage is zero. On working cropland credits would fall to zero. | Three years of production records for the site |
| Project start | 1 June 2025 | Only moves the calendar | The actual planting date |
| Palms on this parcel grow like the Thirthahalli trial palms | Height 7.06 to 9.02 m at age 10 | Probably raises credits: research-station palms are well managed | Field measurement of the stand |
| Seedling height at planting is ignored | Height starts at 0 | Lowers early credits slightly; CPCRI seedlings are 12 to 18 months old at planting | Measured seedling heights |
| Height grows linearly from zero | Straight line to age 10 | Lowers early-year credits; no effect on the year-10 total | Repeated height measurements |
| Every palm survives | 100 % | Raises credits. At 80 % survival credits fall by 20 %. | A mortality count at each monitoring visit |
| Biomass follows the Das height model | 1.074 × exp(−0.496 + 1.616 ln H) | Central of three published options (24, 43, 96 credits) | A local equation, or destructive sampling |
| The equation holds for short palms | Used below its 6.66 m lower limit until about year 9 | Affects timing only; year-10 heights are within range | Measurements of young palms |
| Performance benchmark | 0 | Raises credits: an upper bound. At 0.30 credits fall by 30 %. | Matched control plots from satellite data |
| Uncertainty | 10 % (floor); estimated 9.2 % from cultivar spread | Lowest allowed | Plot sampling error at verification |
| Buffer rating | 12 (floor) | Lowest allowed. At 30 credits fall by about 20 %. | The full Non-Permanence Risk Tool |
| Project emissions | 0 | Raises credits slightly | Fertiliser and burning records |
| Soil carbon and other pools | Excluded | Lowers credits | Soil sampling |

## Closest available values

Where no value exists for this plot, the nearest published one is used:

| Needed | Used instead | Distance from the ideal |
|---|---|---|
| Palm sizes on this plot at age 10 | Eight cultivars measured at Thirthahalli | Same Malnad zone, roughly 65 km away, research station |
| A Karnataka biomass equation for areca | Das et al. 2021, Assam | Same species and country, different region |
| Root share for areca in Karnataka | Das et al. 2021, measured by excavation | Same as above |
| Stand-level check for Malnad | Das et al. 2021 stands of 10 to 35 years | Different region and planting density |
| Rainfall at the plot | NASA POWER grid cell (about 50 km) | Regional, not a rain gauge |
| Greenness of the plot since March 2025 | MODIS 250 m pixel | Covers about five times the parcel |

## Notes on the sources

- **Diameter height.** Bhoomika et al. measured stem diameter 1.0 m above the collar; Das et al. measured at 1.37 m. Palm stems are close to cylindrical, and the default equation uses height only, so this does not affect the reference result.
- **Log-bias correction.** Das et al. report a correction factor of 1.074 for their models without describing how it is applied. The engine multiplies the back-transformed prediction by it, which is the standard use. Without it the result would be 7 % lower.
- **Root share.** Das et al. state that 80 % of biomass was above ground and 20 % below, from palms excavated to 1 m³ of soil around the base.
- **Methodology text.** Rules were read from the VM0047 v1.0 text and Verra's published summary of v1.1 changes; the v1.1 PDF could not be machine-read when this was written.
