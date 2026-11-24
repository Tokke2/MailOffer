#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regressionstester för placeholder-översättning (reg/vin skip, batch, cache, rate-limit)."""

from __future__ import annotations

import ast
import logging
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.email_sender as email_sender
from core.email_sender import (
    _PLACEHOLDER_TRANSLATION_CACHE,
    _should_skip_placeholder_translation,
    _translate_placeholder_values,
    send_email,
)


class PlaceholderTranslationSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        _PLACEHOLDER_TRANSLATION_CACHE.clear()

    def tearDown(self) -> None:
        _PLACEHOLDER_TRANSLATION_CACHE.clear()

    def test_identifiers_and_codes_never_call_google_translator(self) -> None:
        fake_mod = types.ModuleType("deep_translator")
        translator_cls = mock.MagicMock()
        fake_mod.GoogleTranslator = translator_cls

        replacements = {
            "reg": "JKH649",
            "vin": "KE201251209",
            "modell": "Volvo XC60",
            "order_id": "ORD-99812",
            "email": "kund@example.se",
            "pris": "4 995 kr",
            "datum": "2026-11-24",
            "glastyp": "Vindruta",
            "sensor": "regnsensor",
            "kod": "7012AGNVW",
        }
        with mock.patch.dict(sys.modules, {"deep_translator": fake_mod}):
            result = _translate_placeholder_values(replacements, True, True)

        translator_cls.assert_not_called()
        self.assertEqual(result["reg"], "JKH649")
        self.assertEqual(result["vin"], "KE201251209")
        self.assertEqual(result["modell"], "Volvo XC60")
        self.assertEqual(result["order_id"], "ORD-99812")
        self.assertEqual(result["email"], "kund@example.se")
        self.assertEqual(result["pris"], "4 995 kr")
        self.assertEqual(result["glastyp"], "Windshield")
        self.assertEqual(result["sensor"], "Rain sensor")
        self.assertEqual(result["kod"], "7012AGNVW")

    def test_skip_helper_recognizes_reg_vin_and_alphanumeric_tokens(self) -> None:
        self.assertTrue(_should_skip_placeholder_translation("reg", "JKH649"))
        self.assertTrue(_should_skip_placeholder_translation("VIN", "KE201251209"))
        self.assertTrue(_should_skip_placeholder_translation("custom", "JKH649"))
        self.assertTrue(_should_skip_placeholder_translation("custom", "KE201251209"))
        self.assertTrue(_should_skip_placeholder_translation("custom", "2026-10-23"))
        self.assertTrue(_should_skip_placeholder_translation("custom", "info@glas.se"))
        self.assertFalse(
            _should_skip_placeholder_translation(
                "notering", "Stenskott i siktfältet behöver bytas"
            )
        )

    def test_prose_placeholders_use_single_batch_call_and_memory_cache(self) -> None:
        fake_mod = types.ModuleType("deep_translator")
        instance = mock.MagicMock()
        instance.translate_batch.return_value = [
            "Stone chip in driver line of sight",
            "Requires camera calibration",
        ]
        translator_cls = mock.MagicMock(return_value=instance)
        fake_mod.GoogleTranslator = translator_cls

        payload = {
            "reg": "JKH649",
            "vin": "KE201251209",
            "skada": "Stenskott i siktfältet",
            "extra": "Kräver kamerakalibrering",
        }
        with mock.patch.dict(sys.modules, {"deep_translator": fake_mod}):
            first = _translate_placeholder_values(payload, True, True)
            second = _translate_placeholder_values(payload, True, True)

        self.assertEqual(instance.translate_batch.call_count, 1)
        instance.translate.assert_not_called()
        self.assertEqual(first["reg"], "JKH649")
        self.assertEqual(first["vin"], "KE201251209")
        self.assertEqual(first["skada"], "Stone chip in driver line of sight")
        self.assertEqual(first["extra"], "Requires camera calibration")
        self.assertEqual(second, first)

    def test_rate_limit_error_breaks_cleanly_and_preserves_originals(self) -> None:
        fake_mod = types.ModuleType("deep_translator")
        instance = mock.MagicMock()
        rate_err = RuntimeError(
            "Server Error: You made too many requests to the server. "
            "According to google, you are allowed to make 5 requests per second"
        )
        instance.translate_batch.side_effect = rate_err
        translator_cls = mock.MagicMock(return_value=instance)
        fake_mod.GoogleTranslator = translator_cls

        payload = {
            "skada": "Spricka från vänster kant",
            " kommentar_extra": "Behöver bokas omgående",
        }
        with mock.patch.dict(sys.modules, {"deep_translator": fake_mod}):
            with self.assertLogs("core.email_sender", level=logging.WARNING) as logs:
                out = _translate_placeholder_values(payload, True, True)

        self.assertEqual(out, payload)
        # Vid batch rate-limit ska styckvis fallback INTE hamra servern igen
        instance.translate.assert_not_called()
        self.assertEqual(len(logs.output), 1)

    def test_send_email_skips_translation_when_no_english_recipients(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "mall.docx"
            doc = Document()
            doc.add_paragraph("Ämne SV: Offert ::reg::")
            doc.add_paragraph("Ämne EN: Quote ::reg::")
            doc.add_paragraph("SV:")
            doc.add_paragraph("Hej! Reg ::reg::, skada: ::skada::")
            doc.add_paragraph("EN:")
            doc.add_paragraph("Hello! Reg ::reg::, damage: ::skada::")
            doc.save(str(tpl))

            with mock.patch.object(
                email_sender,
                "_translate_placeholder_values",
                wraps=_translate_placeholder_values,
            ) as spy:
                res = send_email(
                    smtp_server="smtp.example.se",
                    smtp_port=587,
                    sender_email="avs@example.se",
                    sender_name="Avsändare",
                    username="",
                    password="",
                    word_file_path=str(tpl),
                    replacements={"reg": "JKH649", "skada": "Stenskott i rutan"},
                    include_english=True,
                    translate_placeholders=True,
                    recipients_to=["kund@example.se"],
                    recipients_bcc=[],
                    attachments=[],
                    recipients_to_lang={"kund@example.se": "sv"},
                    dry_run=True,
                )
            self.assertTrue(res.success)
            spy.assert_not_called()

    def test_send_email_translates_prose_but_never_reg_or_vin_for_english_recipient(self) -> None:
        fake_mod = types.ModuleType("deep_translator")
        instance = mock.MagicMock()
        instance.translate.return_value = "Stone chip in windshield"
        fake_mod.GoogleTranslator = mock.MagicMock(return_value=instance)

        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "mall.docx"
            doc = Document()
            doc.add_paragraph("Ämne SV: Offert ::reg::")
            doc.add_paragraph("Ämne EN: Quote ::reg::")
            doc.add_paragraph("SV:")
            doc.add_paragraph("Hej! Reg ::reg::, skada: ::skada::")
            doc.add_paragraph("EN:")
            doc.add_paragraph("Hello! Reg ::reg::, VIN: ::vin::, damage: ::skada::")
            doc.save(str(tpl))

            with mock.patch.dict(sys.modules, {"deep_translator": fake_mod}):
                res = send_email(
                    smtp_server="smtp.example.se",
                    smtp_port=587,
                    sender_email="avs@example.se",
                    sender_name="Avsändare",
                    username="",
                    password="",
                    word_file_path=str(tpl),
                    replacements={
                        "reg": "JKH649",
                        "vin": "KE201251209",
                        "skada": "Stenskott i rutan",
                    },
                    include_english=True,
                    translate_placeholders=True,
                    recipients_to=["en@example.com"],
                    recipients_bcc=[],
                    attachments=[],
                    recipients_to_lang={"en@example.com": "en"},
                    dry_run=True,
                )

        self.assertTrue(res.success)
        self.assertTrue(res.had_placeholder_translation)
        # Endast 'Stenskott i rutan' ska ha skickats till GoogleTranslator – aldrig JKH649 eller KE201251209!
        instance.translate.assert_called_once_with("Stenskott i rutan")

    def test_send_worker_does_not_duplicate_placeholder_translation(self) -> None:
        source = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        send_worker = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "SendWorker"
        )
        run_fn = next(
            node
            for node in send_worker.body
            if isinstance(node, ast.FunctionDef) and node.name == "run"
        )
        calls = [
            n.func.id
            for n in ast.walk(run_fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        ]
        self.assertNotIn(
            "_translate_placeholder_value",
            calls,
            "SendWorker.run() får inte dubblera placeholder-översättning före send_email()",
        )


if __name__ == "__main__":
    unittest.main()
