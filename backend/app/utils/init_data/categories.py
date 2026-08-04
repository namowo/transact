"""Loads lookup/category tables from app/utils/init_data/data/*.json.

The JSON files are extracted from app/utils/init_data/*.xlsx by
extract_categories.py, which documents why each sheet/column maps to
the model it does (several Excel names differ from their model). This
module only seeds tables that are still empty, so it's safe to run on
every startup.
"""

import json
from pathlib import Path
from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_async_session
from app.crud.base import CRUDBase
from app.crud.activity_category import crud_activity_category
from app.crud.application_analytical_threshold import (
    crud_application_analytical_threshold,
)
from app.crud.body_part_condition_category import crud_body_part_condition_category
from app.crud.classification_criteria import crud_classification_criteria
from app.crud.classification_scheme import crud_classification_scheme
from app.crud.condition_of_item_part_category import (
    crud_condition_of_item_part_category,
)
from app.crud.cutting_device import crud_cutting_device
from app.crud.degradation_category import crud_degradation_category
from app.crud.determination_of_shedding_propensity_category import (
    crud_determination_of_shedding_propensity_category,
)
from app.crud.disturbance_category import crud_disturbance_category
from app.crud.dna_shedding_propensity_category import (
    crud_dna_shedding_propensity_category,
)
from app.crud.experience_level import crud_experience_level
from app.crud.friction_applied_estimate import crud_friction_applied_estimate
from app.crud.geographic_location_category import crud_geographic_location_category
from app.crud.inhibition_category import crud_inhibition_category
from app.crud.pressure_estimate import crud_pressure_estimate
from app.crud.item_category import crud_item_category
from app.crud.item_parts_category import crud_item_parts_category
from app.crud.item_subcategory import crud_item_subcategory
from app.crud.location_of_body_category import crud_location_of_body_category
from app.crud.monitored_transfer_factor import crud_monitored_transfer_factor
from app.crud.principle_of_extraction_method_category import (
    crud_principle_of_extraction_method_category,
)
from app.crud.principle_of_quant_method_category import (
    crud_principle_of_quant_method_category,
)
from app.crud.restriction_prior_to_sampling import crud_restriction_prior_to_sampling
from app.crud.scenario_category import crud_scenario_category
from app.crud.sex import crud_sex
from app.crud.shedder_test import crud_shedder_test
from app.crud.skin_disease_category import crud_skin_disease_category
from app.crud.source_of_dna_category import crud_source_of_dna_category
from app.crud.stutter_filter import crud_stutter_filter
from app.crud.supplier import crud_supplier
from app.crud.surface_material_category import crud_surface_material_category
from app.crud.swabbing_technique_category import crud_swabbing_technique_category
from app.crud.type_of_swab_category import crud_type_of_swab_category
from app.schemas.activity_category import ActivityCategoryCreate
from app.schemas.application_analytical_threshold import (
    ApplicationAnalyticalThresholdCreate,
)
from app.schemas.author import AuthorCreate
from app.schemas.body_part_condition_category import BodyPartConditionCategoryCreate
from app.schemas.condition_of_item_part_category import (
    ConditionOfItemPartCategoryCreate,
)
from app.schemas.cutting_device import CuttingDeviceCreate
from app.schemas.degradation_category import DegradationCategoryCreate
from app.schemas.determination_of_shedding_propensity_category import (
    DeterminationOfSheddingPropensityCategoryCreate,
)
from app.schemas.determination_of_shedding_propensity_category_restriction import (
    DeterminationOfSheddingPropensityCategoryRestrictionCreate,
)
from app.schemas.determination_of_shedding_propensity_category_shedder_test import (
    DeterminationOfSheddingPropensityCategoryShedderTestCreate,
)
from app.schemas.disturbance_category import DisturbanceCategoryCreate
from app.schemas.dna_shedding_propensity_category import (
    DNASheddingPropensityCategoryCreate,
)
from app.schemas.experience_level import ExperienceLevelCreate
from app.schemas.friction_applied_estimate import FrictionAppliedEstimateCreate
from app.schemas.geographic_location_category import GeographicLocationCategoryCreate
from app.schemas.inhibition_category import InhibitionCategoryCreate
from app.schemas.item_category import ItemCategoryCreate
from app.schemas.item_parts_category import ItemPartsCategoryCreate
from app.schemas.item_subcategory import ItemSubcategoryCreate
from app.schemas.location_of_body_category import LocationOfBodyCategoryCreate
from app.schemas.pressure_estimate import PressureEstimateCreate
from app.schemas.principle_of_extraction_method_category import (
    PrincipleOfExtractionMethodCategoryCreate,
)
from app.schemas.principle_of_quant_method_category import (
    PrincipleOfQuantMethodCategoryCreate,
)
from app.schemas.scenario_category import ScenarioCategoryCreate
from app.schemas.sex import SexCreate
from app.schemas.skin_disease_category import SkinDiseaseCategoryCreate
from app.schemas.source_of_dna_category import SourceOfDNACategoryCreate
from app.schemas.stutter_filter import StutterFilterCreate
from app.schemas.supplier import SupplierCreate
from app.schemas.surface_material_category import SurfaceMaterialCategoryCreate
from app.schemas.swabbing_technique_category import SwabbingTechniqueCategoryCreate
from app.schemas.type_of_swab_category import TypeOfSwabCategoryCreate

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_json(name: str) -> list[dict]:
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


async def seed(
    db: AsyncSession,
    crud: CRUDBase,
    schema: Type,
    file_name: str,
) -> None:
    result = await db.execute(select(crud.model.id).limit(1))
    if result.scalars().first() is not None:
        print(f"Skipping {file_name}: table already has data")
        return

    for record in load_json(file_name):
        await crud.create(db, schema(**record))
    print(f"Seeded {file_name}")


async def _id_by_name(db: AsyncSession, model, name: str | None) -> int | None:
    if not name:
        return None
    result = await db.execute(select(model.id).where(model.name == name))
    return result.scalars().first()


async def _get_or_create_id_by_name(db: AsyncSession, crud: CRUDBase, name: str) -> int:
    result = await db.execute(select(crud.model.id).where(crud.model.name == name))
    id_ = result.scalars().first()
    if id_ is not None:
        return id_
    instance = crud.model(name=name)
    db.add(instance)
    await db.flush()
    return instance.id


async def seed_type_of_swab_category(db: AsyncSession) -> None:
    result = await db.execute(select(crud_type_of_swab_category.model.id).limit(1))
    if result.scalars().first() is not None:
        print("Skipping type_of_swab_category: table already has data")
        return

    for record in load_json("type_of_swab_category"):
        supplier_name = record.pop("supplier_name", None)
        record["supplier_id"] = await _id_by_name(db, crud_supplier.model, supplier_name)
        await crud_type_of_swab_category.create(db, TypeOfSwabCategoryCreate(**record))
    print("Seeded type_of_swab_category")


async def seed_item_linked_category(
    db: AsyncSession, crud: CRUDBase, schema: Type, file_name: str
) -> None:
    result = await db.execute(select(crud.model.id).limit(1))
    if result.scalars().first() is not None:
        print(f"Skipping {file_name}: table already has data")
        return

    for record in load_json(file_name):
        item_category_name = record.pop("item_category_name", None)
        record["item_category_id"] = await _id_by_name(
            db, crud_item_category.model, item_category_name
        )
        await crud.create(db, schema(**record))
    print(f"Seeded {file_name}")


async def seed_determination_of_shedding_propensity_category(db: AsyncSession) -> None:
    result = await db.execute(
        select(crud_determination_of_shedding_propensity_category.model.id).limit(1)
    )
    if result.scalars().first() is not None:
        print(
            "Skipping determination_of_shedding_propensity_category: "
            "table already has data"
        )
        return

    for record in load_json("determination_of_shedding_propensity_category"):
        authors = [AuthorCreate(**author) for author in record.pop("authors", [])]

        restrictions = []
        for restriction in record.pop("restrictions", []):
            restriction_id = await _get_or_create_id_by_name(
                db, crud_restriction_prior_to_sampling, restriction["name"]
            )
            restrictions.append(
                DeterminationOfSheddingPropensityCategoryRestrictionCreate(
                    restriction_prior_to_sampling_id=restriction_id,
                    duration=restriction.get("duration"),
                )
            )

        shedder_tests = []
        for shedder_test in record.pop("shedder_tests", []):
            shedder_test_id = await _get_or_create_id_by_name(
                db, crud_shedder_test, shedder_test["name"]
            )
            shedder_tests.append(
                DeterminationOfSheddingPropensityCategoryShedderTestCreate(
                    shedder_test_id=shedder_test_id,
                    duration=shedder_test.get("duration"),
                )
            )

        monitored_transfer_factor_ids = [
            await _get_or_create_id_by_name(db, crud_monitored_transfer_factor, name)
            for name in record.pop("monitored_transfer_factor_names", [])
        ]

        record["classification_criteria_id"] = await _id_by_name(
            db,
            crud_classification_criteria.model,
            record.pop("classification_criteria_name", None),
        )
        record["classification_scheme_id"] = await _id_by_name(
            db,
            crud_classification_scheme.model,
            record.pop("classification_scheme_name", None),
        )

        await crud_determination_of_shedding_propensity_category.create(
            db,
            DeterminationOfSheddingPropensityCategoryCreate(
                **record,
                authors=authors,
                restrictions=restrictions,
                monitored_transfer_factor_ids=monitored_transfer_factor_ids,
                shedder_tests=shedder_tests,
            ),
        )
    print("Seeded determination_of_shedding_propensity_category")


async def main() -> None:
    async for db in get_async_session():
        # supplier must be seeded before type_of_swab_category (FK lookup by name)
        await seed(db, crud_supplier, SupplierCreate, "supplier")
        await seed_type_of_swab_category(db)

        await seed(db, crud_scenario_category, ScenarioCategoryCreate, "scenario_category")
        await seed(db, crud_disturbance_category, DisturbanceCategoryCreate, "disturbance_category")
        await seed(db, crud_geographic_location_category, GeographicLocationCategoryCreate, "geographic_location_category")
        await seed(db, crud_activity_category, ActivityCategoryCreate, "activity_category")
        await seed(db, crud_source_of_dna_category, SourceOfDNACategoryCreate, "source_of_dna_category")
        await seed(db, crud_location_of_body_category, LocationOfBodyCategoryCreate, "location_of_body_category")
        await seed(db, crud_body_part_condition_category, BodyPartConditionCategoryCreate, "body_part_condition_category")
        await seed(db, crud_surface_material_category, SurfaceMaterialCategoryCreate, "surface_material_category")
        await seed(db, crud_skin_disease_category, SkinDiseaseCategoryCreate, "skin_disease_category")

        # item_category must be seeded before item_parts_category/item_subcategory
        # (FK lookup by name)
        await seed(db, crud_item_category, ItemCategoryCreate, "item_category")
        await seed_item_linked_category(
            db, crud_item_parts_category, ItemPartsCategoryCreate, "item_parts_category"
        )
        await seed_item_linked_category(
            db, crud_item_subcategory, ItemSubcategoryCreate, "item_subcategory"
        )

        await seed(db, crud_pressure_estimate, PressureEstimateCreate, "pressure_estimate")
        await seed(db, crud_friction_applied_estimate, FrictionAppliedEstimateCreate, "friction_applied_estimate")
        await seed(db, crud_swabbing_technique_category, SwabbingTechniqueCategoryCreate, "swabbing_technique_category")
        await seed(db, crud_principle_of_extraction_method_category, PrincipleOfExtractionMethodCategoryCreate, "principle_of_extraction_method_category")
        await seed(db, crud_principle_of_quant_method_category, PrincipleOfQuantMethodCategoryCreate, "principle_of_quant_method_category")
        await seed(db, crud_sex, SexCreate, "sex")
        await seed(db, crud_experience_level, ExperienceLevelCreate, "experience_level")
        await seed(db, crud_dna_shedding_propensity_category, DNASheddingPropensityCategoryCreate, "dna_shedding_propensity_category")
        await seed(db, crud_condition_of_item_part_category, ConditionOfItemPartCategoryCreate, "condition_of_item_part_category")
        await seed(db, crud_cutting_device, CuttingDeviceCreate, "cutting_device")
        await seed(db, crud_degradation_category, DegradationCategoryCreate, "degradation_category")
        await seed(db, crud_inhibition_category, InhibitionCategoryCreate, "inhibition_category")
        await seed(db, crud_application_analytical_threshold, ApplicationAnalyticalThresholdCreate, "application_analytical_threshold")
        await seed(db, crud_stutter_filter, StutterFilterCreate, "stutter_filter")

        await seed_determination_of_shedding_propensity_category(db)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
