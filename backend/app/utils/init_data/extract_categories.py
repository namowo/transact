"""Regenerates app/utils/init_data/data/*.json from the source xlsx files.

Run with `uv run python app/utils/init_data/extract_categories.py` (from
backend/). Only needs re-running if Categories.xlsx or the Definitionen
file change - the JSON output is what categories.py actually loads at
app startup, not these spreadsheets.

Each sheet/column is mapped by hand onto the DB model it actually
belongs to, since several Excel names differ from their model:
- 05bb_ItemPartMaterialCategori -> SurfaceMaterialCategory (not a
  "condition" table despite living next to ItemPartsCategory)
- Items/Condition rows in the Definitionen "Enums with Descriptions"
  sheet -> ConditionOfItemPartCategory
- Individuals/DNAsheddingPropensity enum rows -> DNASheddingPropensityCategory
- 07aa_TypeOfSwabCategories.SupplierCategoryID is a 1-based row index
  into 07aaa_SupplierCategories, resolved here to a supplier name and
  resolved again to an id at import time in categories.py
- 07aa_TypeOfSwabCategories.CatalogueNumberOfSupplier/FullNameAsBySupplier
  are dropped: those columns belong to the Supplier model, and this
  sheet only carries one such value per swab type, which isn't reliable
  enough to overwrite the shared Supplier row
- ItemCategory/ItemPartsCategory/ItemSubcategory have no FK between them
  in the schema, so their cross-reference columns in the sheets are
  dropped and only the flat name lists are imported
"""

import json
from pathlib import Path

import openpyxl

INIT_DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = INIT_DATA_DIR / "data"
OUT_DIR.mkdir(exist_ok=True)

CATEGORIES_XLSX = INIT_DATA_DIR / "Categories.xlsx"
DEFINITIONS_XLSX = INIT_DATA_DIR / "Definitionen_Auswahlmöglichkeiten_Repositorx.xlsx"


def clean(v):
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def rows(ws):
    """Yield non-empty rows as dicts keyed by the header row, values cleaned."""
    it = ws.iter_rows(values_only=True)
    header = [clean(h) for h in next(it)]
    for r in it:
        r = [clean(v) for v in r]
        if all(v is None for v in r):
            continue
        yield dict(zip(header, r))


def dump(name, records):
    path = OUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(records)} records -> {path}")


def main():
    wb = openpyxl.load_workbook(CATEGORIES_XLSX, data_only=True)

    # --- simple name-only / name+description sheets -> flat lookup tables ---
    simple_sheet_to_table = {
        "02a_ScenarioCategories": "scenario_category",
        "02d_DisturbanceCategories": "disturbance_category",
        "03a_ActivityCategories": "activity_category",
        "04s_SourceOfDNACategories": "source_of_dna_category",
        "05aa_LocationOfBodyCategories": "location_of_body_category",
        "05ab_BodyPartConditionCategorie": "body_part_condition_category",
        "06ba_ItemCategories": "item_category",
        "07aaa_SupplierCategories": "supplier",  # single-column subset, see below
    }
    for sheet, table in simple_sheet_to_table.items():
        ws = wb[sheet]
        records = []
        for row in rows(ws):
            header_key = next(iter(row))
            name = row[header_key]
            if name is None:
                continue
            rec = {"name": name}
            if "Description" in row and row["Description"] is not None:
                rec["description"] = row["Description"]
            records.append(rec)
        dump(table, records)

    # --- sheets with an explicit Description column already handled above ---
    for sheet, table in {
        "02e_GeographicLocationCategorie": "geographic_location_category",
        "07ab_SwabbingTechniqueCategorie": "swabbing_technique_category",
        "08a_PrincipleOfExtractionMethod": "principle_of_extraction_method_category",
    }.items():
        ws = wb[sheet]
        records = []
        for row in rows(ws):
            header_key = next(iter(row))
            name = row.get(header_key)
            if name is None:
                continue
            records.append({"name": name, "description": row.get("Description")})
        dump(table, records)

    # --- 05bb_ItemPartMaterialCategori -> surface_material_category ---
    ws = wb["05bb_ItemPartMaterialCategori"]
    records = [{"name": row["ItemPartMaterialCategory"]} for row in rows(ws)]
    dump("surface_material_category", records)

    # --- 05ba_ItemPartsCategories -> item_parts_category (name only; no FK in schema) ---
    ws = wb["05ba_ItemPartsCategories"]
    seen = []
    for row in rows(ws):
        name = row["ItemPartsCategory"]
        if name not in seen:
            seen.append(name)
    dump("item_parts_category", [{"name": n} for n in seen])

    # --- 06bab_ItemSubcategories -> item_subcategory (name only; no FK in schema) ---
    ws = wb["06bab_ItemSubcategories"]
    records = [{"name": row["ItemSubcategory"]} for row in rows(ws)]
    dump("item_subcategory", records)

    # --- 06aa_SkinDiseaseCategories -> skin_disease_category ---
    ws = wb["06aa_SkinDiseaseCategories"]
    bool_map = {"increase": True, "decrease": False, "none": False}
    records = []
    for row in rows(ws):
        name = row["SkinDiseaseCategory"]
        if name is None:
            continue
        influence_raw = (row.get("InfluenceOnSheddingPropensity") or "").strip().lower() if row.get("InfluenceOnSheddingPropensity") else None
        records.append(
            {
                "name": name,
                "influence_on_shedding_propensity": bool_map.get(influence_raw),
                "literature": row.get("Literature"),
            }
        )
    dump("skin_disease_category", records)

    # --- 06ab_DeterminationOfSheddingPro -> determination_of_shedding_propensity_category ---
    ws = wb["06ab_DeterminationOfSheddingPro"]
    key_map = {
        "Authors": "authors",
        "Title": "title",
        "doi": "doi",
        "RestrictionsPriorToSampling": "restrictions_prior_to_sampling",
        "MonitoredTransferFactors": "monitored_transfer_factors",
        "NumberOfParticipants": "number_of_participants",
        "Replicates": "replicates",
        "ShedderTest": "shedder_test",
        "ClassificationCriteria": "classification_criteria",
        "ClassificationScheme": "classification_scheme",
        "ClassificationOutcome": "classification_outcome",
    }
    records = []
    for row in rows(ws):
        if row.get("Authors") is None:
            continue
        records.append({key_map[k]: v for k, v in row.items() if k in key_map})
    dump("determination_of_shedding_propensity_category", records)

    # --- 09a_PrincipleOfQuantMethodCateg -> principle_of_quant_method_category ---
    ws = wb["09a_PrincipleOfQuantMethodCateg"]
    records = [
        {"name": row["PrincipleOfQuantificationMethodCategory"]} for row in rows(ws)
    ]
    dump("principle_of_quant_method_category", records)

    # --- 07aaa_SupplierCategories -> supplier (name only) ---
    ws = wb["07aaa_SupplierCategories"]
    supplier_names = [row["SupplierCategory"] for row in rows(ws)]
    dump("supplier", [{"name": n} for n in supplier_names])

    # --- 07aa_TypeOfSwabCategories -> type_of_swab_category ---
    # Note: CatalogueNumberOfSupplier / FullNameAsBySupplier columns are dropped
    # here on purpose - they belong to the Supplier model, not TypeOfSwabCategory,
    # and the sheet only provides one such value per swab type (not reliable
    # enough to safely overwrite the referenced Supplier row).
    ws = wb["07aa_TypeOfSwabCategories"]
    records = []
    for row in rows(ws):
        name = row.get("TypeOfSwabCategory")
        if name is None:
            continue
        supplier_id = row.get("SupplierCategoryID")
        supplier_name = (
            supplier_names[int(supplier_id) - 1]
            if supplier_id and 0 < int(supplier_id) <= len(supplier_names)
            else None
        )
        records.append(
            {
                "name": name,
                "description": row.get("Description"),
                "supplier_name": supplier_name,  # resolved to supplier_id at import time
            }
        )
    dump("type_of_swab_category", records)

    # --- Definitionen file: Enums with Descriptions -> a few real lookup tables ---
    wb2 = openpyxl.load_workbook(DEFINITIONS_XLSX, data_only=True)
    ws = wb2["Enums with Descriptions"]
    enum_rows = list(rows(ws))

    def enum_group(entity, name):
        return [
            r["enum-options"]
            for r in enum_rows
            if r.get("Entity") == entity and r.get("Name") == name and r.get("enum-options")
        ]

    dump("sex", [{"name": v} for v in enum_group("Individuals", "Sex")])
    dump(
        "experience_level",
        [{"name": v} for v in enum_group("Recoveries", "ExperienceLevelOfSampler")],
    )
    dump(
        "dna_shedding_propensity_category",
        [{"name": v} for v in enum_group("Individuals", "DNAsheddingPropensity")],
    )
    condition_records = [
        {"name": r["enum-options"], "description": r.get("Description")}
        for r in enum_rows
        if r.get("Entity") == "Items" and r.get("Name") == "Condition"
    ]
    dump("condition_of_item_part_category", condition_records)


if __name__ == "__main__":
    main()
