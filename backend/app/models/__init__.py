from app.core.db import Base

from .assoziation_immobilie_nutzungsart import assoziation_immobilie_nutzungsart
from .assoziation_satzung_momamassnahme import assoziation_satzung_momamassnahme
from .bundesland import Bundesland
from .entfernung_berechnung import EntfernungBerechnung
from .entfernung_einheit import EntfernungEinheit
from .gebietszone import Gebietszone
from .gemeinde import Gemeinde
from .gemeinde_anfrage import GemeindeAnfrage
from .immobilie import Immobilie
from .immobilie_eingabefelder import ImmobilieEingabefelder
from .immobilie_export import ImmobilieExport
from .moma_massnahme import MomaMassnahme
from .moma_massnahme_kategorie import MomaMassnahmeKategorie
from .nutzungsart import Nutzungsart
from .nutzungsart_kategorie import NutzungsartKategorie
from .nutzungsart_nutzungsart import NutzungsartNutzungsart
from .nutzungsart_parameter import NutzungsartParameter
from .nutzungsart_parameter_bezugseinheit_besucher import (
    NutzungsartParameterBezugseinheitBesucher,
)
from .nutzungsart_parameter_einheit import NutzungsartParameterEinheit
from .nutzungsart_parameter_fahrrad_berechnung import (
    NutzungsartParameterFahrradBerechnung,
)
from .nutzungsart_parameter_pkw_berechnung import NutzungsartParameterPkwBerechnung
from .satzung import Satzung
from .satzung_abloese import SatzungAbloese
from .satzung_regulatorische_ebene import SatzungRegulatorischeEbene
from .user import User

# TransAct models
from .activity_category import ActivityCategory
from .body_part_condition_category import BodyPartConditionCategory
from .ce_method import CEMethod
from .condition_during_contact import ConditionDuringContact
from .condition_of_item_part_category import ConditionOfItemPartCategory
from .contact import Contact
from .cutting_method import CuttingMethod
from .determination_of_shedding_propensity_category import DeterminationOfSheddingPropensityCategory
from .disturbance_category import DisturbanceCategory
from .epg_analysis_method import EPGAnalysisMethod
from .epg_interpretation_method import EPGInterpretationMethod
from .extraction_method import ExtractionMethod
from .geographic_location_category import GeographicLocationCategory
from .individual import Individual
from .item import Item
from .item_category import ItemCategory
from .item_parts_category import ItemPartsCategory
from .item_subcategory import ItemSubcategory
from .laboratory import Laboratory
from .location_of_body_category import LocationOfBodyCategory
from .pcr_method import PCRMethod
from .persistence import Persistence
from .picking_method import PickingMethod
from .post_pcr_treatment_method import PostPCRTreatmentMethod
from .principle_of_extraction_method_category import PrincipleOfExtractionMethodCategory
from .principle_of_quant_method_category import PrincipleOfQuantMethodCategory
from .quantification_method import QuantificationMethod
from .recovery import Recovery
from .result import Result
from .sampling_method import SamplingMethod
from .scenario import Scenario
from .scenario_category import ScenarioCategory
from .scraping_method import ScrapingMethod
from .skin_disease_category import SkinDiseaseCategory
from .source_of_dna_category import SourceOfDNACategory
from .study import Study
from .surface import Surface
from .surface_material_category import SurfaceMaterialCategory
from .swab_method import SwabMethod
from .swabbing_technique_category import SwabbingTechniqueCategory
from .tape_method import TapeMethod
from .type_of_swab_category import TypeOfSwabCategory
