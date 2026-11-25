"""Predefined data models offered to everyone.

They live in code rather than the database so they change together with the
field catalog; a test checks that each one validates against it.
"""

from dataclasses import dataclass

from app.schemas.data_model import DataModelDefinition


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    description: str
    definition: DataModelDefinition


_STUDY = ["study.title", "study.year", "study.doi", "laboratory.name"]


PRESETS: list[Preset] = [
    Preset(
        id="preset-transfer-results",
        name="Transfer results",
        description=(
            "DNA quantity recovered per sample across all transfer experiments, "
            "with the contact, the donor and recipient surfaces and how the "
            "sample was taken. A good starting point for transfer rates."
        ),
        definition=DataModelDefinition(
            dataset="results",
            columns=[
                *_STUDY,
                "scenario.name",
                "scenario.category",
                "contact.name",
                "contact.duration",
                "contact.pressure_estimate",
                "contact.friction_applied_estimate",
                "contact.activity",
                "donor_surface.label",
                "donor_surface.individual.shedding_propensity",
                "recipient_surface.label",
                "recipient_surface.surface_material",
                "sample.name",
                "sample.surface_role",
                "sampling_method.kind",
                "sampling_method.swab_type",
                "extraction_method.principle",
                "quantification_method.kit",
                "result.dna_concentration",
                "sample.elution_volume",
                "result.degradation",
                "result.inhibition",
            ],
        ),
    ),
    Preset(
        id="preset-str-profiles",
        name="STR profiles",
        description=(
            "One row per PCR with the kit, CE and analysis settings and the "
            "profile summary (number of contributors, total RFU, alleles)."
        ),
        definition=DataModelDefinition(
            dataset="pcr_profiles",
            columns=[
                *_STUDY,
                "scenario.name",
                "sample.name",
                "sampled_surface.label",
                "result.dna_concentration",
                "pcr.dna_input_amount",
                "pcr_method.kit",
                "pcr_method.no_of_cycles",
                "ce_method.device",
                "ce_method.injection_time",
                "epg_analysis.analytical_threshold",
                "pcr.no_of_contributors",
                "pcr.average_rfu",
                "pcr.total_no_of_alleles",
            ],
        ),
    ),
    Preset(
        id="preset-mixture-contributors",
        name="Mixture contributors",
        description=(
            "Who contributed how much to each DNA profile, with the "
            "contributor's sex, age and shedder status - for modelling "
            "transfer and shedder effects."
        ),
        definition=DataModelDefinition(
            dataset="pcr_contributors",
            columns=[
                *_STUDY,
                "scenario.name",
                "sample.name",
                "sample.surface_role",
                "donor_surface.individual.name",
                "contributor.label",
                "contributor.known",
                "contributor.mixture_proportion",
                "contributor.individual.sex",
                "contributor.individual.age",
                "contributor.individual.shedding_propensity",
                "pcr.no_of_contributors",
            ],
        ),
    ),
    Preset(
        id="preset-contacts",
        name="Contacts",
        description=(
            "Every contact performed, with duration, pressure, friction, "
            "activity, the conditions it took place in and both surfaces."
        ),
        definition=DataModelDefinition(
            dataset="contacts",
            columns=[
                *_STUDY,
                "scenario.name",
                "contact.name",
                "contact.previous",
                "contact.duration",
                "contact.pressure",
                "contact.pressure_estimate",
                "contact.friction_applied_estimate",
                "contact.activity",
                "contact_condition.temperature",
                "contact_condition.humidity",
                "donor_surface.label",
                "recipient_surface.label",
                "contact.samples_taken",
            ],
        ),
    ),
    Preset(
        id="preset-participants",
        name="Participants",
        description="Study participants with sex, age, shedder status and skin conditions.",
        definition=DataModelDefinition(
            dataset="individuals",
            columns=[
                *_STUDY,
                "individual.name",
                "individual.sex",
                "individual.age",
                "individual.shedding_propensity",
                "individual.shedding_propensity_determination",
                "individual.skin_disease",
                "individual.scenarios",
            ],
        ),
    ),
    Preset(
        id="preset-study-catalogue",
        name="Study catalogue",
        description="All available studies with authors, journal, DOI and how much data each holds.",
        definition=DataModelDefinition(
            dataset="studies",
            columns=[
                "study.title",
                "study.authors",
                "study.year",
                "study.journal",
                "study.doi",
                "laboratory.name",
                "laboratory.country",
                "study.scenarios",
                "count.individuals",
                "count.samples",
                "count.results",
            ],
        ),
    ),
]

PRESETS_BY_ID: dict[str, Preset] = {preset.id: preset for preset in PRESETS}
