from fastapi import APIRouter

from app.core.deps import auth_backend, fastapi_users

from app.api.routers import utils
from app.schemas.user import UserRead, UserCreate, UserUpdate

# TransAct routers
from app.api.routers import activity_category
from app.api.routers import body_part_condition_category
from app.api.routers import ce_method
from app.api.routers import condition_during_contact
from app.api.routers import condition_of_item_part_category
from app.api.routers import contact
from app.api.routers import cutting_method
from app.api.routers import determination_of_shedding_propensity_category
from app.api.routers import disturbance_category
from app.api.routers import epg_analysis_method
from app.api.routers import epg_interpretation_method
from app.api.routers import extraction_method
from app.api.routers import geographic_location_category
from app.api.routers import individual
from app.api.routers import item
from app.api.routers import item_category
from app.api.routers import item_parts_category
from app.api.routers import item_subcategory
from app.api.routers import laboratory
from app.api.routers import location_of_body_category
from app.api.routers import pcr_method
from app.api.routers import persistence
from app.api.routers import picking_method
from app.api.routers import post_pcr_treatment_method
from app.api.routers import principle_of_extraction_method_category
from app.api.routers import principle_of_quant_method_category
from app.api.routers import quantification_method
from app.api.routers import recovery
from app.api.routers import result
from app.api.routers import sampling_method
from app.api.routers import scenario
from app.api.routers import scenario_category
from app.api.routers import scraping_method
from app.api.routers import skin_disease_category
from app.api.routers import source_of_dna_category
from app.api.routers import study
from app.api.routers import surface
from app.api.routers import surface_material_category
from app.api.routers import swab_method
from app.api.routers import swabbing_technique_category
from app.api.routers import tape_method
from app.api.routers import type_of_swab_category
from app.api.routers import vacuum_method

api_router = APIRouter()

api_router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["Auth"]
)
api_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
api_router.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["Auth"]
)
api_router.include_router(
    fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["Auth"]
)
api_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
)

# Categories
api_router.include_router(activity_category.router, prefix="/activity-categories", tags=["Categories"])
api_router.include_router(body_part_condition_category.router, prefix="/body-part-condition-categories", tags=["Categories"])
api_router.include_router(condition_of_item_part_category.router, prefix="/condition-of-item-part-categories", tags=["Categories"])
api_router.include_router(determination_of_shedding_propensity_category.router, prefix="/determination-of-shedding-propensity-categories", tags=["Categories"])
api_router.include_router(disturbance_category.router, prefix="/disturbance-categories", tags=["Categories"])
api_router.include_router(geographic_location_category.router, prefix="/geographic-location-categories", tags=["Categories"])
api_router.include_router(item_category.router, prefix="/item-categories", tags=["Categories"])
api_router.include_router(item_parts_category.router, prefix="/item-parts-categories", tags=["Categories"])
api_router.include_router(item_subcategory.router, prefix="/item-subcategories", tags=["Categories"])
api_router.include_router(location_of_body_category.router, prefix="/location-of-body-categories", tags=["Categories"])
api_router.include_router(principle_of_extraction_method_category.router, prefix="/principle-of-extraction-method-categories", tags=["Categories"])
api_router.include_router(principle_of_quant_method_category.router, prefix="/principle-of-quant-method-categories", tags=["Categories"])
api_router.include_router(scenario_category.router, prefix="/scenario-categories", tags=["Categories"])
api_router.include_router(skin_disease_category.router, prefix="/skin-disease-categories", tags=["Categories"])
api_router.include_router(source_of_dna_category.router, prefix="/source-of-dna-categories", tags=["Categories"])
api_router.include_router(surface_material_category.router, prefix="/surface-material-categories", tags=["Categories"])
api_router.include_router(swabbing_technique_category.router, prefix="/swabbing-technique-categories", tags=["Categories"])
api_router.include_router(type_of_swab_category.router, prefix="/type-of-swab-categories", tags=["Categories"])

# Laboratories
api_router.include_router(laboratory.router, prefix="/laboratories", tags=["Laboratories"])

# Methods
api_router.include_router(ce_method.router, prefix="/ce-methods", tags=["Methods"])
api_router.include_router(cutting_method.router, prefix="/cutting-methods", tags=["Methods"])
api_router.include_router(epg_analysis_method.router, prefix="/epg-analysis-methods", tags=["Methods"])
api_router.include_router(epg_interpretation_method.router, prefix="/epg-interpretation-methods", tags=["Methods"])
api_router.include_router(extraction_method.router, prefix="/extraction-methods", tags=["Methods"])
api_router.include_router(pcr_method.router, prefix="/pcr-methods", tags=["Methods"])
api_router.include_router(picking_method.router, prefix="/picking-methods", tags=["Methods"])
api_router.include_router(post_pcr_treatment_method.router, prefix="/post-pcr-treatment-methods", tags=["Methods"])
api_router.include_router(quantification_method.router, prefix="/quantification-methods", tags=["Methods"])
api_router.include_router(sampling_method.router, prefix="/sampling-methods", tags=["Methods"])
api_router.include_router(scraping_method.router, prefix="/scraping-methods", tags=["Methods"])
api_router.include_router(swab_method.router, prefix="/swab-methods", tags=["Methods"])
api_router.include_router(tape_method.router, prefix="/tape-methods", tags=["Methods"])
api_router.include_router(vacuum_method.router, prefix="/vacuum-methods", tags=["Methods"])

# Studies
api_router.include_router(study.router, prefix="/studies", tags=["Studies"])

# Individuals
api_router.include_router(individual.router, prefix="/individuals", tags=["Individuals"])

# Items
api_router.include_router(item.router, prefix="/items", tags=["Items"])

# Surfaces
api_router.include_router(surface.router, prefix="/surfaces", tags=["Surfaces"])

# Contacts
api_router.include_router(condition_during_contact.router, prefix="/conditions-during-contact", tags=["Contacts"])
api_router.include_router(contact.router, prefix="/contacts", tags=["Contacts"])

# Scenarios
api_router.include_router(persistence.router, prefix="/persistences", tags=["Scenarios"])
api_router.include_router(scenario.router, prefix="/scenarios", tags=["Scenarios"])

# Results
api_router.include_router(recovery.router, prefix="/recoveries", tags=["Results"])
api_router.include_router(result.router, prefix="/results", tags=["Results"])
