#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för e-postlistor: text, CSV/TSV, inklistrade Excel-rader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.email_lists import (
    extract_email_addresses,
    format_email_list_text,
    parse_email_list_text,
    read_email_list_file,
    safe_txt_filename,
)


class TestExtractEmailAddresses(unittest.TestCase):
    def test_outlook_style_and_duplicates(self):
        text = (
            "Anna Andersson <ANNA@example.se>; bob@example.com, "
            "anna@example.se\nogiltig"
        )
        self.assertEqual(
            extract_email_addresses(text),
            ["anna@example.se", "bob@example.com"],
        )

    def test_rejects_obvious_invalid_addresses(self):
        text = "a@b @example.com a@example giltig@example.se"
        self.assertEqual(
            extract_email_addresses(text), ["giltig@example.se"]
        )


class TestParseEmailListText(unittest.TestCase):
    def test_plain_lines_names_duplicates_and_invalid(self):
        parsed = parse_email_list_text(
            "Anna <anna@example.se>; bob@example.com, anna@example.se\n"
            "inte-en-adress\n"
        )
        self.assertEqual(
            parsed.emails, ["anna@example.se", "bob@example.com"]
        )
        self.assertEqual(parsed.duplicates, 1)
        self.assertEqual(parsed.invalid, 1)
        by_email = {contact.email: contact for contact in parsed.contacts}
        self.assertEqual(by_email["anna@example.se"].name, "Anna")
        self.assertEqual(by_email["bob@example.com"].name, "")

    def test_swedish_semicolon_csv_headers(self):
        parsed = parse_email_list_text(
            "E-post;Namn;Företag;Språk;Kategori\n"
            "anna@example.se;Anna;Exempel AB;en;Bilglas\n"
            "bob@example.com;Bob;;sv;Bilglas\n"
        )
        self.assertEqual(
            parsed.emails, ["anna@example.se", "bob@example.com"]
        )
        anna, bob = parsed.contacts
        self.assertEqual(anna.name, "Anna")
        self.assertEqual(anna.company, "Exempel AB")
        self.assertEqual(anna.language, "en")
        self.assertEqual(anna.categories, ["Bilglas"])
        self.assertEqual(bob.language, "sv")

    def test_english_comma_csv_and_quoted_categories(self):
        parsed = parse_email_list_text(
            "email,name,company,language,categories\n"
            "anna@example.se,Anna,Exempel AB,en,\"VIP; Bilglas\"\n"
        )
        self.assertEqual(parsed.emails, ["anna@example.se"])
        contact = parsed.contacts[0]
        self.assertEqual(contact.language, "en")
        self.assertEqual(contact.categories, ["VIP", "Bilglas"])

    def test_headerless_excel_tsv_row(self):
        parsed = parse_email_list_text(
            "Anna\tanna@example.se\tExempel AB\ten"
        )
        self.assertEqual(parsed.emails, ["anna@example.se"])
        contact = parsed.contacts[0]
        self.assertEqual(contact.name, "Anna")
        self.assertEqual(contact.company, "Exempel AB")
        self.assertEqual(contact.language, "en")

    def test_multiple_angle_addresses_keep_own_names(self):
        parsed = parse_email_list_text(
            "Anna <anna@example.se>, Bob <bob@example.com>"
        )
        by_email = {contact.email: contact for contact in parsed.contacts}
        self.assertEqual(by_email["anna@example.se"].name, "Anna")
        self.assertEqual(by_email["bob@example.com"].name, "Bob")

    def test_duplicate_rows_merge_metadata_and_categories(self):
        parsed = parse_email_list_text(
            "email,name,categories\n"
            "anna@example.se,,VIP\n"
            "anna@example.se,Anna,Bilglas\n"
        )
        self.assertEqual(parsed.emails, ["anna@example.se"])
        self.assertEqual(parsed.duplicates, 1)
        contact = parsed.contacts[0]
        self.assertEqual(contact.name, "Anna")
        self.assertEqual(contact.categories, ["VIP", "Bilglas"])


class TestFormatEmailListText(unittest.TestCase):
    def test_semicolon_separated_and_roundtrip(self):
        text = format_email_list_text(
            [
                "Bob <bob@example.com>",
                "anna@example.se",
                "ANNA@example.se",
                "inte giltig",
            ]
        )
        self.assertEqual(text, "bob@example.com; anna@example.se\n")
        self.assertEqual(
            parse_email_list_text(text).emails,
            ["bob@example.com", "anna@example.se"],
        )

    def test_safe_txt_filename(self):
        self.assertEqual(
            safe_txt_filename("Taxi / Stockholm: norr"),
            "Taxi - Stockholm- norr.txt",
        )
        self.assertEqual(safe_txt_filename("CON"), "_CON.txt")
        self.assertEqual(safe_txt_filename(""), "kategori.txt")


class TestReadEmailListFile(unittest.TestCase):
    def test_reads_cp1252_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lista.txt"
            path.write_bytes(
                "Åsa <asa@example.se>\nanna@example.se\n".encode("cp1252")
            )
            parsed = read_email_list_file(path)
        self.assertEqual(
            parsed.emails, ["asa@example.se", "anna@example.se"]
        )
        self.assertEqual(parsed.contacts[0].name, "Åsa")

    def test_xlsx_binary_gets_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lista.xlsx"
            path.write_bytes(b"PK\x03\x04fake")
            with self.assertRaises(ValueError):
                read_email_list_file(path)


if __name__ == "__main__":
    unittest.main()
