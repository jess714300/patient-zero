# Data

Patient Zero will use patient records, community data, and clinical reference data to practice ingestion, transformation, and normalization.

The initial scope includes 14 sources. These are selected sources, not completed integrations. We will build one ingestion flow at a time and use the actual data to guide decisions about shared code and storage.

## Patient Data

| Source | What it provides | Access |
| --- | --- | --- |
| [CMS Blue Button Sandbox](https://bluebutton.cms.gov/api-documentation/) | Synthetic Medicare patients, insurance coverage, medical claims, and prescription claims | FHIR API; requires a sandbox account, application registration, and OAuth authorization |
| [Synthea](https://synthetichealth.github.io/downloads.html) | Synthetic patient histories, including encounters, conditions, medications, and observations | Download CSV or FHIR files, or generate a population locally |
| [MIMIC-IV](https://physionet.org/content/mimiciv/3.1/) | Deidentified hospital records, including admissions, diagnoses, medications, labs, and ICU measurements | Full data requires credentialing, training, and a data-use agreement; an [open demo](https://physionet.org/content/mimic-iv-demo/2.2/) is available |
| [CMS DE-SynPUF](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files) | Synthetic Medicare beneficiary records and claims from 2008–2010 | Bulk CSV downloads |
| [AHRQ MEPS](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files.jsp) | Survey records covering conditions, healthcare visits, prescriptions, insurance, costs, and household information | Public downloads, including two-year longitudinal panels |
| [AHRQ SyH-DR](https://www.ahrq.gov/data/innovations/syh-dr.html) | Medicare, Medicaid, and commercial insurance records for 2016 | Requires an approved application and data-use agreement; claims contain synthetic elements, while person-level information is masked or aggregated |

Blue Button provides API practice, while DE-SynPUF provides bulk claims data. Blue Button authorization is tied to a beneficiary; it is not an unrestricted download of the entire sandbox population.

These sources generally represent different people. We will work toward a common record structure while keeping each source's patient identifiers separate.

## Community Data

| Source | What it provides | Access |
| --- | --- | --- |
| [Census ACS](https://www.census.gov/programs-surveys/acs/data/data-via-api.html) | Population, income, poverty, education, employment, housing, and insurance estimates | API and downloads; five-year estimates include census tracts |
| [CDC PLACES](https://www.cdc.gov/places/tools/explore-places-data-portal.html) | Local estimates of health outcomes, health behaviors, and preventive care | API and downloads at several geographic levels |
| [AHRQ Community-Level Health](https://www.ahrq.gov/data/innovations/clh-data.html) | Combined demographic, economic, education, infrastructure, and health measures | Annual Excel downloads by county, ZIP Code, census tract, and census block group |
| [CDC Social Vulnerability Index](https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html) | Community vulnerability measures and rankings | CSV and geographic downloads by census tract and county |

Community data can be connected to patient records where usable geography is available. Geographic boundaries and data years need to match. A community measure, such as a neighborhood poverty rate, does not describe an individual patient's income.

Some sources overlap. The Social Vulnerability Index uses ACS data, and AHRQ combines information from multiple sources. CDC PLACES values are modeled community estimates, not individual patient measurements. The Community-Level Health database replaces AHRQ's earlier SDOH database.

## Reference Data

| Source | What it provides | Access |
| --- | --- | --- |
| [ICD-10-CM and ICD-10-PCS](https://www.cms.gov/medicare/coding-billing/ICD-10-codes) | Diagnosis codes and inpatient procedure codes, respectively | Official downloadable releases |
| [RxNorm](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html) | Standard medication names and relationships between ingredients, strengths, and forms | RxNav API; [bulk releases](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html) have separate access terms |
| [FDA NDC Directory](https://open.fda.gov/apis/drug/ndc/) | Drug product and package codes, names, ingredients, and packaging | openFDA API and downloadable data |
| [CMS HCPCS Level II](https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system/quarterly-update) | Codes for supplies, equipment, and certain services and drugs | Public quarterly files |

Reference releases have effective dates. We will need the versions that apply to the records being processed, rather than assuming the latest release covers everything.

DE-SynPUF also needs legacy ICD-9-CM support. [Synthea uses SNOMED CT and LOINC](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary) as well; we can preserve those codes without adding their full reference datasets to this first pass. HCPCS Level II does not include the separately licensed CPT code set.
