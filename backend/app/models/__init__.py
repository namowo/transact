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
