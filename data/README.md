# Data files

## `parcel.geojson`
The study parcel, unchanged from the proof of concept (`mrv-reference-pipeline`
v1.0.0, doi:10.5281/zenodo.22026520). WGS84, GeoJSON `[lng, lat]`.

## `growth_anchor_bhoomika2023.csv`
Palm height (m) and stem diameter (cm, measured 1.0 m above the collar) for
eight arecanut cultivars at **age 10 years**, planted at 2.7 m x 2.7 m, at the
Agricultural and Horticultural Research Station, Thirthahalli, Shivamogga,
Karnataka (Malnad). Pooled means of the 2019-20 and 2020-21 seasons.

Source: Bhoomika, H.R., Hegde, M.R. and Maheswarappa, H.P. (2023).
Productivity and carbon sequestration potential of arecanut cultivars.
*Indian Journal of Horticulture* 80(4): 372-376. doi:10.58993/ijh/2023.80.4.11.
Values are from Table 1 of the paper.

Two things to know about this source:

- The paper's running text gives different stem diameters for SAS-1 (18.07 cm)
  and Mangala (13.14 cm) than its Table 1 (17.38 and 11.78 cm). The text
  figures match the internodal-distance column, so this file uses Table 1.
- These are research-station palms. Smallholder stands may grow more slowly
  and lose more palms; the scenario exposes a survival fraction for that.

## `reference_stands.csv`
Carbon stocks of arecanut stands that were measured, used to check the model.

- Das et al. (2021): stands of 10, 15, 25 and 35 years in Karimganj, Assam,
  with palm density and total (above + below ground) carbon per hectare.
  doi:10.1016/j.indic.2021.100115.
- Bhoomika et al. (2023): the mean of the eight Thirthahalli cultivars at
  age 10, as the authors estimated it (above ground only, Prayogo equation,
  carbon fraction 0.5): 11.51 t biomass/ha x 0.5 = 5.76 t C/ha.

## `observed/`
What has actually been observed at the plot.

| File | What it is | Status |
|---|---|---|
| `poc_sentinel2_ndvi.csv` | Mean NDVI of the parcel, Sentinel-2 at 10 m, Nov 2024 to Mar 2025 | Measured in the proof of concept |
| `weather_nasa_power.csv` | Monthly rainfall and mean temperature, NASA POWER (about 50 km grid) | Created by `python collect_observations.py` |
| `ndvi_modis_250m.csv` | NDVI every 16 days for the 250 m MODIS pixel containing the plot | Created by `python collect_observations.py` |
| `ndvi_sentinel2_10m.csv` | Monthly NDVI of the parcel itself | Created by the notebook's optional Earth Engine cell |

The MODIS pixel covers about 6 ha, five times the parcel, so it describes the
plot and its neighbours together.
