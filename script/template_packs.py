#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Färdiga mallpaket som användaren kan kopiera och anpassa.

Paketen ligger inbäddade i koden så att de följer med appens
uppdateringar även till installationer där ``Mallar/`` är skyddad
användardata. När ett paket installeras skapas vanliga TXT-mallar i
användarens mallmapp; befintliga filer skrivs aldrig över.

FIL: script/template_packs.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from script.templates import (
    build_template_body,
    clear_scan_cache,
    create_template,
    sanitize_template_filename,
)


@dataclass(frozen=True)
class TemplatePackItem:
    """En färdig mall i ett mallpaket."""

    item_id: str
    file_stem: str
    name_sv: str
    name_en: str
    subject: str
    body_sv: str
    body_en: str

    @property
    def filename(self) -> str:
        return sanitize_template_filename(self.file_stem, ".txt")

    def display_name(self, language: str = "sv") -> str:
        return self.name_en if language.lower().startswith("en") else self.name_sv


@dataclass(frozen=True)
class TemplatePack:
    """En grupp relaterade färdiga mallar."""

    pack_id: str
    name_sv: str
    name_en: str
    description_sv: str
    description_en: str
    templates: Tuple[TemplatePackItem, ...]

    def display_name(self, language: str = "sv") -> str:
        return self.name_en if language.lower().startswith("en") else self.name_sv

    def display_description(self, language: str = "sv") -> str:
        return (
            self.description_en
            if language.lower().startswith("en")
            else self.description_sv
        )


@dataclass
class TemplatePackInstallResult:
    created: List[Path] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def created_names(self) -> List[str]:
        return [path.name for path in self.created]


TEMPLATE_PACKS: Tuple[TemplatePack, ...] = (
    TemplatePack(
        pack_id="customer_care",
        name_sv="Kundvård & uppföljning",
        name_en="Customer care & follow-up",
        description_sv="Påminnelser, tackmail och kampanjer för befintliga kunder.",
        description_en="Reminders, thank-you emails and campaigns for existing customers.",
        templates=(
            TemplatePackItem(
                item_id="reminder_quote",
                file_stem="Påminnelse – offertförfrågan",
                name_sv="Påminnelse om offertförfrågan",
                name_en="Quote request reminder",
                subject="Påminnelse: offertförfrågan ::modell:: (::reg::)",
                body_sv=(
                    "Hej,\n\n"
                    "Jag vill följa upp vår offertförfrågan från ::date:: "
                    "gällande ::modell:: (::reg::).\n\n"
                    "Vi önskar fortfarande pris och leveranstid för:\n"
                    "::kommentar::\n\n"
                    "Återkom gärna när ni har möjlighet. Tack på förhand!"
                ),
                body_en=(
                    "Hello,\n\n"
                    "I would like to follow up on our quote request from "
                    "::date:: regarding ::modell:: (::reg::).\n\n"
                    "We still need a price and delivery time for:\n"
                    "::kommentar::\n\n"
                    "Please reply when you have a moment. Thank you in advance!"
                ),
            ),
            TemplatePackItem(
                item_id="thanks_inquiry",
                file_stem="Tack för förfrågan",
                name_sv="Tack för förfrågan",
                name_en="Thank you for your enquiry",
                subject="Tack för din förfrågan – ::company::",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Tack för din förfrågan till ::company::. Vi har tagit "
                    "emot uppgifterna om ::modell:: (::reg::) och återkommer "
                    "med pris och förslag på tid.\n\n"
                    "Behöver du komplettera med något går det bra att svara "
                    "på detta mail.\n\n"
                    "Med vänlig hälsning"
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "Thank you for contacting ::company::. We have received "
                    "the details for ::modell:: (::reg::) and will get back "
                    "to you with a price and a proposed time.\n\n"
                    "If you need to add anything, just reply to this email.\n\n"
                    "Kind regards"
                ),
            ),
            TemplatePackItem(
                item_id="thanks_completed",
                file_stem="Tack efter utfört arbete",
                name_sv="Tack efter utfört arbete",
                name_en="Thank you after completed work",
                subject="Tack för förtroendet – ::modell::",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Tack för förtroendet! Vi hoppas att du är nöjd med "
                    "arbetet på din ::modell:: (::reg::).\n\n"
                    "::kommentar::\n\n"
                    "Hör gärna av dig om något känns oklart eller om vi kan "
                    "hjälpa till med något mer.\n\n"
                    "Med vänlig hälsning"
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "Thank you for choosing us! We hope you are happy with "
                    "the work on your ::modell:: (::reg::).\n\n"
                    "::kommentar::\n\n"
                    "Please get in touch if anything is unclear or if we "
                    "can help with anything else.\n\n"
                    "Kind regards"
                ),
            ),
            TemplatePackItem(
                item_id="seasonal_campaign",
                file_stem="Säsongskampanj",
                name_sv="Säsongskampanj",
                name_en="Seasonal campaign",
                subject="Säsongskampanj: ::kommentar:: – ::price::",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Just nu erbjuder vi ::kommentar:: för ::price::.\n\n"
                    "Erbjudandet gäller till och med ::date::. Svara på "
                    "detta mail för att boka eller få mer information.\n\n"
                    "Välkommen in!"
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "We are currently offering ::kommentar:: for ::price::.\n\n"
                    "The offer is valid until ::date::. Reply to this "
                    "email to book or to get more information.\n\n"
                    "Welcome in!"
                ),
            ),
        ),
    ),
    TemplatePack(
        pack_id="cars_workshops",
        name_sv="Bil & verkstad",
        name_en="Cars & workshops",
        description_sv="För service, reparation, däck och verkstadsbokningar.",
        description_en="For servicing, repairs, tyres and workshop bookings.",
        templates=(
            TemplatePackItem(
                item_id="car_service_quote",
                file_stem="Offertförfrågan – bilservice",
                name_sv="Offertförfrågan bilservice/reparation",
                name_en="Car service/repair quote request",
                subject="Offertförfrågan service ::modell:: (::reg::)",
                body_sv=(
                    "Hej,\n\n"
                    "Vi önskar offert på service/reparation av följande bil:\n\n"
                    "Bilmodell: ::modell::\n"
                    "Reg.nr: ::reg::\n"
                    "Önskat arbete: ::kommentar::\n\n"
                    "Återkom gärna med pris, vad som ingår och möjliga tider."
                ),
                body_en=(
                    "Hello,\n\n"
                    "Please quote for servicing/repairing the following car:\n\n"
                    "Car model: ::modell::\n"
                    "Reg. no.: ::reg::\n"
                    "VIN: ::vin::\n"
                    "Requested work: ::kommentar::\n\n"
                    "Please reply with a price, what is included and "
                    "available times."
                ),
            ),
            TemplatePackItem(
                item_id="tyre_season",
                file_stem="Säsongsbyte – däck",
                name_sv="Säsongsbyte däck",
                name_en="Seasonal tyre change",
                subject="Dags för däckbyte – ::modell:: (::reg::)",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Det börjar bli dags för säsongsbyte av däck på din "
                    "::modell:: (::reg::).\n\n"
                    "Just nu erbjuder vi däckskifte för ::price::. "
                    "::kommentar::\n\n"
                    "Svara på mailet så bokar vi en tid som passar dig."
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "It is soon time for the seasonal tyre change on your "
                    "::modell:: (::reg::).\n\n"
                    "We currently offer a tyre change for ::price::. "
                    "::kommentar::\n\n"
                    "Reply to this email and we will book a time that suits you."
                ),
            ),
            TemplatePackItem(
                item_id="booking_confirmation",
                file_stem="Bokningsbekräftelse – verkstadsbesök",
                name_sv="Bokningsbekräftelse verkstadsbesök",
                name_en="Workshop booking confirmation",
                subject="Bokningsbekräftelse ::date:: – ::modell:: (::reg::)",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Här kommer en bekräftelse på din bokning.\n\n"
                    "Datum/tid: ::date::\n"
                    "Bil: ::modell:: (::reg::)\n"
                    "Ärende: ::kommentar::\n\n"
                    "Meddela oss så snart som möjligt om tiden inte passar.\n\n"
                    "Välkommen!"
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "Here is a confirmation of your booking.\n\n"
                    "Date/time: ::date::\n"
                    "Car: ::modell:: (::reg::)\n"
                    "Reason: ::kommentar::\n\n"
                    "Please let us know as soon as possible if the time "
                    "does not work for you.\n\n"
                    "Welcome!"
                ),
            ),
        ),
    ),
    TemplatePack(
        pack_id="trades_services",
        name_sv="Hantverk & service",
        name_en="Trades & services",
        description_sv="Generella mallar för hantverk, installation och service.",
        description_en="General templates for trades, installation and service work.",
        templates=(
            TemplatePackItem(
                item_id="trades_quote",
                file_stem="Offertförfrågan – hantverk",
                name_sv="Offertförfrågan hantverk",
                name_en="Trades quote request",
                subject="Offertförfrågan – ::company::",
                body_sv=(
                    "Hej,\n\n"
                    "Vi önskar offert på följande arbete:\n\n"
                    "::kommentar::\n\n"
                    "Önskad start: ::date::\n\n"
                    "Återkom gärna med prisuppskattning, villkor och om ni "
                    "behöver boka ett platsbesök först.\n\n"
                    "Med vänlig hälsning\n::name::"
                ),
                body_en=(
                    "Hello,\n\n"
                    "We would like a quote for the following work:\n\n"
                    "::kommentar::\n\n"
                    "Preferred start date: ::date::\n\n"
                    "Please reply with an estimated price, your terms and "
                    "whether you need to book a site visit first.\n\n"
                    "Kind regards\n::name::"
                ),
            ),
            TemplatePackItem(
                item_id="work_completed",
                file_stem="Arbetet är klart",
                name_sv="Arbetet är klart",
                name_en="The work is complete",
                subject="Arbetet är klart – ::company::",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Arbetet är nu klart.\n\n"
                    "Sammanfattning:\n::kommentar::\n\n"
                    "Totalt att betala: ::price::\n\n"
                    "Säg till om något behöver kontrolleras eller "
                    "kompletteras.\n\n"
                    "Tack för denna gång!"
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "The work has now been completed.\n\n"
                    "Summary:\n::kommentar::\n\n"
                    "Total amount due: ::price::\n\n"
                    "Let us know if anything needs to be checked or added.\n\n"
                    "Thank you!"
                ),
            ),
        ),
    ),
    TemplatePack(
        pack_id="suppliers_orders",
        name_sv="Leverantörer & beställningar",
        name_en="Suppliers & orders",
        description_sv="Produktförfrågningar och orderbekräftelser.",
        description_en="Product enquiries and order confirmations.",
        templates=(
            TemplatePackItem(
                item_id="supplier_product_inquiry",
                file_stem="Produktförfrågan till leverantör",
                name_sv="Produktförfrågan till leverantör",
                name_en="Supplier product enquiry",
                subject="Förfrågan: ::produkt::",
                body_sv=(
                    "Hej,\n\n"
                    "Vi önskar pris och leveranstid på följande:\n\n"
                    "Produkt: ::produkt::\n"
                    "Antal: ::antal::\n"
                    "Önskad leverans: ::date::\n\n"
                    "Kommentar: ::kommentar::\n\n"
                    "Tack på förhand!"
                ),
                body_en=(
                    "Hello,\n\n"
                    "Please quote a price and delivery time for the "
                    "following:\n\n"
                    "Product: ::produkt::\n"
                    "Quantity: ::antal::\n"
                    "Requested delivery: ::date::\n\n"
                    "Comment: ::kommentar::\n\n"
                    "Thank you in advance!"
                ),
            ),
            TemplatePackItem(
                item_id="order_confirmation",
                file_stem="Orderbekräftelse",
                name_sv="Orderbekräftelse",
                name_en="Order confirmation",
                subject="Orderbekräftelse ::ordernummer:: – ::company::",
                body_sv=(
                    "Hej ::name::,\n\n"
                    "Tack för din beställning! Här är en sammanfattning:\n\n"
                    "Ordernummer: ::ordernummer::\n"
                    "Beställningsdatum: ::date::\n"
                    "Totalt: ::price::\n\n"
                    "::kommentar::\n\n"
                    "Vi hör av oss om något behöver kompletteras."
                ),
                body_en=(
                    "Hello ::name::,\n\n"
                    "Thank you for your order! Here is a summary:\n\n"
                    "Order number: ::ordernummer::\n"
                    "Order date: ::date::\n"
                    "Total: ::price::\n\n"
                    "::kommentar::\n\n"
                    "We will contact you if anything needs to be added."
                ),
            ),
        ),
    ),
)


def all_template_packs() -> List[TemplatePack]:
    return list(TEMPLATE_PACKS)


def template_pack_by_id(pack_id: object) -> Optional[TemplatePack]:
    wanted = str(pack_id or "").strip().lower()
    for pack in TEMPLATE_PACKS:
        if pack.pack_id == wanted:
            return pack
    return None


def iter_template_pack_items() -> Iterable[TemplatePackItem]:
    for pack in TEMPLATE_PACKS:
        yield from pack.templates


def template_pack_item_by_id(item_id: object) -> Optional[TemplatePackItem]:
    wanted = str(item_id or "").strip().lower()
    for item in iter_template_pack_items():
        if item.item_id == wanted:
            return item
    return None


def install_template_items(
    templates_dir: Path,
    item_ids: Optional[Iterable[str]] = None,
) -> TemplatePackInstallResult:
    """Installera valda paketmallar som TXT-filer.

    Utan ``item_ids`` installeras alla mallar. Befintliga filer
    skrivs aldrig över utan rapporteras i ``skipped``.
    """
    directory = Path(templates_dir)
    directory.mkdir(parents=True, exist_ok=True)
    wanted = None if item_ids is None else {str(value).lower() for value in item_ids}
    result = TemplatePackInstallResult()
    for item in iter_template_pack_items():
        if wanted is not None and item.item_id.lower() not in wanted:
            continue
        target = directory / item.filename
        if target.exists():
            result.skipped.append(target.name)
            continue
        create_template(
            target,
            item.subject,
            build_template_body(item.body_sv, item.body_en),
            overwrite=False,
        )
        result.created.append(target)
    if result.created:
        clear_scan_cache()
    return result


def install_template_pack(
    templates_dir: Path, pack_id: str
) -> TemplatePackInstallResult:
    pack = template_pack_by_id(pack_id)
    if pack is None:
        raise ValueError(f"Okänt mallpaket: {pack_id}")
    return install_template_items(
        templates_dir, [item.item_id for item in pack.templates]
    )


def pack_template_counts() -> Dict[str, int]:
    return {pack.pack_id: len(pack.templates) for pack in TEMPLATE_PACKS}


__all__ = [
    "TEMPLATE_PACKS",
    "TemplatePack",
    "TemplatePackInstallResult",
    "TemplatePackItem",
    "all_template_packs",
    "install_template_items",
    "install_template_pack",
    "iter_template_pack_items",
    "pack_template_counts",
    "template_pack_by_id",
    "template_pack_item_by_id",
]
