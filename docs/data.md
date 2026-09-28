# Data

Patient Zero will use patient records, community data, and clinical reference data to practice ingestion, transformation, and normalization.


## Patient Data

| Source | What it provides | Access |
| --- | --- | --- |
| [CMS Blue Button Sandbox](https://bluebutton.cms.gov/api-documentation/) | Synthetic Medicare patients, insurance coverage, medical claims, and prescription claims | FHIR API; requires a sandbox account, application registration, and OAuth authorization |
| [Synthea](https://synthetichealth.github.io/downloads.html) | Synthetic patient histories, including encounters, conditions, medications, and observations | Download CSV or FHIR files, or generate a population locally |
| [MIMIC-IV](https://physionet.org/content/mimiciv/3.1/) | Deidentified hospital records, including admissions, diagnoses, medications, labs, and ICU measurements | Full data requires credentialing, training, and a data-use agreement; an [open demo](https://physionet.org/content/mimic-iv-demo/2.2/) is available |
| [CMS DE-SynPUF](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files) | Synthetic Medicare beneficiary records and claims from 2008–2010 | Bulk CSV downloads |
| [AHRQ MEPS](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files.jsp) | Survey records covering conditions, healthcare visits, prescriptions, insurance, costs, and household information | Public downloads, including two-year longitudinal panels |
| [AHRQ SyH-DR](https://www.ahrq.gov/data/innovations/syh-dr.html) | Medicare, Medicaid, and commercial insurance records for 2016 | Requires an approved application and data-use agreement; claims contain synthetic elements, while person-level information is masked or aggregated |


## CMS Blue Button Sandbox

[CMS Blue Button](https://bluebutton.cms.gov/api-documentation/) provides synthetic Medicare beneficiary, coverage, medical claim, and prescription claim records through a FHIR API.


## MIMIC-IV

[MIMIC-IV](https://physionet.org/content/mimiciv/3.1/) contains deidentified hospital and ICU records, including admissions, diagnoses, medications, laboratory results, and clinical measurements.


## CMS DE-SynPUF

[DE-SynPUF](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files) contains synthetic Medicare beneficiary and claims records covering 2008-2010.


## AHRQ MEPS

[MEPS](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files.jsp) contains survey data on health conditions, healthcare use, prescriptions, costs, insurance, and household characteristics.


## AHRQ SyH-DR

[SyH-DR](https://www.ahrq.gov/data/innovations/syh-dr.html) contains 2016 Medicare, Medicaid, and commercial insurance data, with synthetic claims elements and masked or aggregated person-level information.


## Synthea

[Synthea](https://github.com/synthetichealth/synthea) is MITRE's open-source simulator for fictional patients and their longitudinal medical histories. Its data covers demographics, encounters, diagnoses, medications, allergies, immunizations, labs, procedures, care plans, insurance, and claims. Exports include CSV, FHIR, and C-CDA; specialized collections add images, genomics, physiological signals, and clinical notes. Published datasets are available from the [downloads page](https://synthetichealth.github.io/downloads.html), with CSV fields described in the [data dictionary](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary).

### Data Locations

Raw downloads are stored locally under `data/raw/synthea/`, outside Git. [`etl_synthea_patients.py`](../etls/etl_synthea_patients.py) loads raw data into `patient_zero.synthea_data`. CSV records use all-text `<dataset>_<entity>_raw` tables.

| Dataset | Description | Format / approximate download size | Table pattern in `synthea_data` |
| --- | --- | --- | --- |
| [SyntheticMass v2](https://mitre.box.com/shared/static/3bo45m48ocpzp8fc0tp005vax7l93xji.gz) | Massachusetts population advertised as one million synthetic patient records with longitudinal healthcare histories. Released May 24, 2017. | FHIR 3.0.1, CSV, C-CDA / 21 GB | `syntheticmass_v2_<entity>_raw` |
| [SyntheticMass v1](https://mitre.box.com/shared/static/s9m4itxxzbw7q9gy68wf84foev3x1t6y.gz) | Earlier Massachusetts population release, advertised as one million synthetic patient records. Released February 27, 2017. | FHIR 1.8.0, CSV, C-CDA / 28 GB | `syntheticmass_v1_<entity>_raw` |
| [Current CSV sample](https://synthetichealth.github.io/synthea-sample-data/downloads/latest/synthea_sample_data_csv_latest.zip) | General patient histories, advertised as a 100-patient sample. The downloaded snapshot contains 108 patient rows. | CSV / 7 MB | `sample_latest_<entity>_raw` |
| [April 2020 CSV sample](https://synthetichealth.github.io/synthea-sample-data/downloads/synthea_sample_data_csv_apr2020.zip) | General patient histories for a nominal 1,000-patient population. | CSV / 9 MB | `sample_1k_2020_<entity>_raw` |
| [COVID-19 10K](https://synthetichealth.github.io/synthea-sample-data/downloads/10k_synthea_covid19_csv.zip) | COVID-19-focused medical histories for a nominal 10,000-patient population. | CSV / 54 MB | `covid19_10k_<entity>_raw` |
| [COVID-19 100K](https://mitre.box.com/shared/static/wk3560f962ozlg7sd2oj1zxk73ayqvm0.zip) | Larger COVID-19-focused population, advertised as 100,000 patients. | CSV / 512 MB | `covid19_100k_<entity>_raw` |
| [Synthetic Denver](https://mitre.box.com/shared/static/ydmcj2kpwzoyt6zndx4yfz163hfvyhd0.zip) | Records for 6,357 simulated children in Colorado, developed for the Childhood Obesity Data Initiative. Includes split records for identity-matching studies. | FHIR / 295 MB | `denver_<entity>_raw` |
| [Breast cancer / mCODE](https://confluence.hl7.org/display/COD/mCODE+Test+Data) | Synthetic breast cancer records using minimal Common Oncology Data Elements (mCODE) profiles. | FHIR / varies by collection | `mcode_breast_cancer_<entity>_raw` |
| [Canadian sample](https://mitre.box.com/shared/static/f359fe69kkgzuy1predq822si96qghtl.zip) | Synthetic patient records spanning Canadian provinces. | FHIR / 124 MB | `canada_<entity>_raw` |
| [Coherent](https://synthea-open-data.s3.amazonaws.com/coherent/coherent-11-07-2022.zip) | Linked clinical records, DICOM images, genomic data, physiological signals such as ECGs, and clinical notes. | FHIR and associated files / 9 GB | `coherent_2022_<entity>_raw` |

## Community Data





| Source | What it provides | Access |
| --- | --- | --- |
| [Census ACS](https://www.census.gov/programs-surveys/acs/data/data-via-api.html) | Population, income, poverty, education, employment, housing, and insurance estimates | API and downloads; five-year estimates include census tracts |
| [CDC PLACES](https://www.cdc.gov/places/tools/explore-places-data-portal.html) | Local estimates of health outcomes, health behaviors, and preventive care | API and downloads at several geographic levels |
| [AHRQ Community-Level Health](https://www.ahrq.gov/data/innovations/clh-data.html) | Combined demographic, economic, education, infrastructure, and health measures | Annual Excel downloads by county, ZIP Code, census tract, and census block group |
| [CDC Social Vulnerability Index](https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html) | Community vulnerability measures and rankings | CSV and geographic downloads by census tract and county |


### Census ACS

[ACS](https://www.census.gov/programs-surveys/acs/data/data-via-api.html) provides geographic estimates of population, income, education, employment, housing, poverty, and insurance coverage.


### CDC PLACES

[PLACES](https://www.cdc.gov/places/tools/explore-places-data-portal.html) provides modeled local estimates of health outcomes, health behaviors, and preventive care.


### AHRQ Community-Level Health

[Community-Level Health](https://www.ahrq.gov/data/innovations/clh-data.html) combines demographic, economic, education, infrastructure, and health measures at several geographic levels.


### CDC Social Vulnerability Index

[SVI](https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html) provides community vulnerability measures and rankings by county and census tract.


## Reference Data






| Source | What it provides | Access |
| --- | --- | --- |
| [ICD-10-CM and ICD-10-PCS](https://www.cms.gov/medicare/coding-billing/ICD-10-codes) | Diagnosis codes and inpatient procedure codes, respectively | Official downloadable releases |
| [RxNorm](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html) | Standard medication names and relationships between ingredients, strengths, and forms | RxNav API; [bulk releases](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html) have separate access terms |
| [FDA NDC Directory](https://open.fda.gov/apis/drug/ndc/) | Drug product and package codes, names, ingredients, and packaging | openFDA API and downloadable data |
| [CMS HCPCS Level II](https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update) | Codes for supplies, equipment, and certain services and drugs | Public quarterly files |


### ICD-10-CM and ICD-10-PCS

[CMS ICD-10 releases](https://www.cms.gov/medicare/coding-billing/ICD-10-codes) contain diagnosis codes (ICD-10-CM) and inpatient procedure codes (ICD-10-PCS).


### RxNorm

[RxNorm](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html) provides standardized medication names and relationships among ingredients, strengths, and dosage forms.


### FDA NDC Directory

[The NDC Directory](https://open.fda.gov/apis/drug/ndc/) contains drug product and package identifiers, names, ingredients, and packaging information.


### CMS HCPCS Level II

[HCPCS Level II](https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update) contains codes for supplies, equipment, and selected services and drugs.
