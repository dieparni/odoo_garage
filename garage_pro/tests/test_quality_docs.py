"""Tests pour les modules Qualité et Documentation (Agent 9)."""

import base64
from datetime import date, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestGarageQualityDocs(TransactionCase):
    """Tests unitaires pour qualité, documentation, crons et mail templates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Client
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client QC Test',
            'is_garage_customer': True,
        })
        # Véhicule
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandQC',
        })
        cls.model_fleet = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelQC',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model_fleet.id,
            'license_plate': 'QC-001',
            'driver_id': cls.partner.id,
        })
        # Assurance
        cls.insurance_partner = cls.env['res.partner'].create({
            'name': 'Assurance QC SA',
            'is_company': True,
        })
        cls.insurance = cls.env['garage.insurance.company'].create({
            'name': 'Assurance QC',
            'partner_id': cls.insurance_partner.id,
            'code': 'AQCT',
            'convention_type': 'direct',
            'hourly_rate_bodywork': 50.0,
            'hourly_rate_paint': 50.0,
        })
        # OR de base
        cls.repair_order = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })
        # Ligne carrosserie + peinture + mécanique pour tests QC
        cls.env['garage.repair.order.line'].create({
            'repair_order_id': cls.repair_order.id,
            'line_type': 'labor_body',
            'name': 'Redressage pare-chocs',
            'quantity': 1,
            'unit_price': 200.0,
        })
        cls.env['garage.repair.order.line'].create({
            'repair_order_id': cls.repair_order.id,
            'line_type': 'labor_paint',
            'name': 'Peinture pare-chocs',
            'quantity': 1,
            'unit_price': 300.0,
        })
        cls.env['garage.repair.order.line'].create({
            'repair_order_id': cls.repair_order.id,
            'line_type': 'labor_mech',
            'name': 'Diagnostic moteur',
            'quantity': 1,
            'unit_price': 100.0,
        })

    # ==================================================================
    # Tests Qualité — Checklist
    # ==================================================================

    def test_create_quality_checklist_general(self):
        """La création auto génère les items standards + métiers."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        self.assertEqual(checklist.checklist_type, 'general')
        self.assertEqual(checklist.repair_order_id, self.repair_order)
        # 5 standards + 3 carrosserie + 4 peinture + 4 mécanique = 16
        self.assertEqual(len(checklist.item_ids), 16)

    def test_checklist_items_bodywork_only(self):
        """OR avec carrosserie seulement : 5 + 3 = 8 items."""
        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'line_type': 'labor_body',
            'name': 'Test',
            'quantity': 1,
            'unit_price': 100,
        })
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(ro)
        self.assertEqual(len(checklist.item_ids), 8)

    def test_checklist_items_no_trade(self):
        """OR sans opération métier : 5 items standards uniquement."""
        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'line_type': 'parts',
            'name': 'Pièce test',
            'quantity': 1,
            'unit_price': 50,
        })
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(ro)
        self.assertEqual(len(checklist.item_ids), 5)

    def test_checklist_fully_checked_false_initially(self):
        """is_fully_checked est False à la création."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        self.assertFalse(checklist.is_fully_checked)
        self.assertFalse(checklist.overall_result)

    def test_checklist_all_ok(self):
        """Tous les items OK → overall_result = pass."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        for item in checklist.item_ids:
            item.result = 'ok'
        self.assertTrue(checklist.is_fully_checked)
        self.assertEqual(checklist.overall_result, 'pass')

    def test_checklist_some_nok(self):
        """Mix ok/nok → partial."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        items = checklist.item_ids
        items[0].result = 'nok'
        for item in items[1:]:
            item.result = 'ok'
        self.assertTrue(checklist.is_fully_checked)
        self.assertEqual(checklist.overall_result, 'partial')

    def test_checklist_all_nok(self):
        """Tous nok → fail."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        for item in checklist.item_ids:
            item.result = 'nok'
        self.assertTrue(checklist.is_fully_checked)
        self.assertEqual(checklist.overall_result, 'fail')

    def test_checklist_na_counted_as_ok(self):
        """Tous NA + OK → pass."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        items = checklist.item_ids
        items[0].result = 'na'
        for item in items[1:]:
            item.result = 'ok'
        self.assertTrue(checklist.is_fully_checked)
        self.assertEqual(checklist.overall_result, 'pass')

    def test_checklist_validate_action(self):
        """action_validate enregistre le contrôleur et la date."""
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        checklist.action_validate()
        self.assertEqual(checklist.checked_by, self.env.user)
        self.assertTrue(checklist.check_date)

    def test_ro_quality_checklist_count(self):
        """L'OR compte ses checklists qualité."""
        self.assertEqual(self.repair_order.quality_checklist_count, 0)
        self.env['garage.quality.checklist'].create_from_repair_order(
            self.repair_order
        )
        self.assertEqual(self.repair_order.quality_checklist_count, 1)

    def test_ro_create_quality_checklist_action(self):
        """action_create_quality_checklist renvoie une action window."""
        result = self.repair_order.action_create_quality_checklist()
        self.assertEqual(result['res_model'], 'garage.quality.checklist')
        self.assertTrue(result['res_id'])

    # ==================================================================
    # Tests Documentation
    # ==================================================================

    def test_create_documentation(self):
        """Création d'un document avec fichier."""
        # Fichier assez gros pour que file_size > 0 (> 1 Ko)
        raw = b'Test file content ' * 100
        file_content = base64.b64encode(raw)
        doc = self.env['garage.documentation'].create({
            'name': 'Photo test',
            'doc_type': 'photo_before',
            'file': file_content,
            'filename': 'test.jpg',
            'repair_order_id': self.repair_order.id,
            'vehicle_id': self.vehicle.id,
        })
        self.assertEqual(doc.doc_type, 'photo_before')
        self.assertTrue(doc.file_size > 0)
        self.assertEqual(doc.taken_by, self.env.user)

    def test_documentation_on_claim(self):
        """Document rattaché à un sinistre."""
        claim = self.env['garage.insurance.claim'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'insurance_company_id': self.insurance.id,
            'claim_date': date.today(),
            'claim_type': 'collision',
        })
        file_content = base64.b64encode(b'Claim doc')
        doc = self.env['garage.documentation'].create({
            'name': 'Constat',
            'doc_type': 'accident_report',
            'file': file_content,
            'filename': 'constat.pdf',
            'claim_id': claim.id,
        })
        self.assertEqual(claim.document_count, 1)
        self.assertEqual(claim.document_ids[0], doc)

    def test_ro_photo_count(self):
        """L'OR compte ses documents."""
        self.assertEqual(self.repair_order.photo_count, 0)
        file_content = base64.b64encode(b'Photo content')
        self.env['garage.documentation'].create({
            'name': 'Photo avant',
            'doc_type': 'photo_before',
            'file': file_content,
            'repair_order_id': self.repair_order.id,
        })
        self.assertEqual(self.repair_order.photo_count, 1)

    def test_documentation_portal_visibility(self):
        """Par défaut is_visible_portal est True."""
        file_content = base64.b64encode(b'Portal doc')
        doc = self.env['garage.documentation'].create({
            'name': 'Doc portail',
            'doc_type': 'photo_after',
            'file': file_content,
        })
        self.assertTrue(doc.is_visible_portal)

    def test_documentation_damage_zone(self):
        """Zone de dommage peut être définie."""
        file_content = base64.b64encode(b'Damage photo')
        doc = self.env['garage.documentation'].create({
            'name': 'Dommage pare-chocs',
            'doc_type': 'photo_damage',
            'file': file_content,
            'damage_zone': 'front_bumper',
        })
        self.assertEqual(doc.damage_zone, 'front_bumper')

    def test_file_size_compute(self):
        """La taille du fichier est calculée en Ko."""
        # 1024 bytes de données brutes → base64 ≈ 1368 chars → ~1 Ko
        raw = b'x' * 1024
        file_content = base64.b64encode(raw)
        doc = self.env['garage.documentation'].create({
            'name': 'Size test',
            'doc_type': 'other',
            'file': file_content,
        })
        self.assertTrue(doc.file_size >= 1)

    # ==================================================================
    # Tests Crons
    # ==================================================================

    def test_cron_vehicle_not_picked_up(self):
        """Cron crée une activité sur les OR 'ready' depuis > 7 jours."""
        self.repair_order.write({'state': 'ready'})
        # Flush ORM writes avant SQL brut
        self.env.flush_all()
        # Simuler un write_date ancien via SQL
        old_date = fields.Datetime.now() - timedelta(days=8)
        self.env.cr.execute(
            "UPDATE garage_repair_order SET write_date = %s WHERE id = %s",
            (old_date, self.repair_order.id),
        )
        self.env.invalidate_all()
        self.env['garage.repair.order'].cron_vehicle_not_picked_up()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'garage.repair.order'),
            ('res_id', '=', self.repair_order.id),
        ])
        self.assertTrue(len(activities) >= 1)

    def test_cron_reminder_expertise(self):
        """Cron crée une activité pour sinistres en attente > 5 jours."""
        claim = self.env['garage.insurance.claim'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'insurance_company_id': self.insurance.id,
            'claim_date': date.today(),
            'claim_type': 'collision',
        })
        claim.action_declare()
        claim.action_request_expertise()
        # Flush ORM writes avant SQL brut
        self.env.flush_all()
        # Simuler un write_date ancien via SQL
        old_date = fields.Datetime.now() - timedelta(days=6)
        self.env.cr.execute(
            "UPDATE garage_insurance_claim SET write_date = %s WHERE id = %s",
            (old_date, claim.id),
        )
        self.env.invalidate_all()
        self.env['garage.insurance.claim'].cron_reminder_expertise()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'garage.insurance.claim'),
            ('res_id', '=', claim.id),
            ('summary', 'ilike', 'Relance expertise'),
        ])
        self.assertTrue(len(activities) >= 1)

    def test_cron_ct_alerts(self):
        """Cron crée une activité pour CT à venir dans les 30 jours."""
        self.vehicle.write({
            'ct_last_date': date.today() - timedelta(days=340),
        })
        # ct_next_date sera dans ~25 jours
        self.env['fleet.vehicle'].cron_ct_alerts()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'fleet.vehicle'),
            ('res_id', '=', self.vehicle.id),
            ('summary', 'ilike', 'CT à renouveler'),
        ])
        self.assertTrue(len(activities) >= 1)

    def test_cron_maintenance_alerts(self):
        """Cron crée une activité pour entretien à venir."""
        plan = self.env['garage.maintenance.plan'].create({
            'vehicle_id': self.vehicle.id,
        })
        item = self.env['garage.maintenance.plan.item'].create({
            'plan_id': plan.id,
            'name': 'Vidange huile',
            'interval_months': 12,
            'last_done_date': date.today() - timedelta(days=345),
        })
        self.env['garage.maintenance.plan.item'].cron_maintenance_alerts()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'fleet.vehicle'),
            ('res_id', '=', self.vehicle.id),
            ('summary', 'ilike', 'Vidange huile'),
        ])
        self.assertTrue(len(activities) >= 1)

    # ==================================================================
    # Tests Mail Templates
    # ==================================================================

    def test_mail_template_quotation_exists(self):
        """Le template email devis existe."""
        template = self.env.ref('garage_pro.email_template_quotation_sent')
        self.assertTrue(template)
        self.assertEqual(template.model_id.model, 'garage.quotation')

    def test_mail_template_or_in_progress_exists(self):
        """Le template email OR en cours existe."""
        template = self.env.ref('garage_pro.email_template_or_in_progress')
        self.assertTrue(template)
        self.assertEqual(template.model_id.model, 'garage.repair.order')

    def test_mail_template_or_ready_exists(self):
        """Le template email véhicule prêt existe."""
        template = self.env.ref('garage_pro.email_template_or_ready')
        self.assertTrue(template)
        self.assertEqual(template.model_id.model, 'garage.repair.order')

    # ==================================================================
    # Tests Actions OR
    # ==================================================================

    def test_ro_action_view_quality_checklists(self):
        """action_view_quality_checklists renvoie l'action correcte."""
        result = self.repair_order.action_view_quality_checklists()
        self.assertEqual(result['res_model'], 'garage.quality.checklist')

    def test_ro_action_view_documentation(self):
        """action_view_documentation renvoie l'action correcte."""
        result = self.repair_order.action_view_documentation()
        self.assertEqual(result['res_model'], 'garage.documentation')
