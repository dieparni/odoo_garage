"""Tests pour le planning atelier (postes, techniciens, créneaux)."""

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPlanningBase(TransactionCase):
    """Setup commun pour les tests planning."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Planning Test',
            'is_garage_customer': True,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'PlanningBrand',
        })
        cls.vmodel = cls.env['fleet.vehicle.model'].create({
            'name': 'PlanningModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vmodel.id,
            'license_plate': 'PLN-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.repair_order = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })
        cls.technician = cls.env['hr.employee'].create({
            'name': 'Jean Carrossier',
            'is_garage_technician': True,
            'garage_skill': 'body',
            'daily_capacity_hours': 8.0,
        })
        cls.post_pont = cls.env['garage.workshop.post'].create({
            'name': 'Pont 1',
            'code': 'P1',
            'post_type': 'body_lift',
            'capacity': 1,
        })
        cls.post_zone = cls.env['garage.workshop.post'].create({
            'name': 'Zone polyvalente',
            'code': 'ZP',
            'post_type': 'general',
            'capacity': 3,
        })


class TestWorkshopPost(TestPlanningBase):
    """Tests poste de travail."""

    def test_01_create_post(self):
        """Création d'un poste de travail."""
        self.assertEqual(self.post_pont.post_type, 'body_lift')
        self.assertEqual(self.post_pont.capacity, 1)
        self.assertTrue(self.post_pont.active)

    def test_02_bottleneck(self):
        """Marquage goulot d'étranglement."""
        booth = self.env['garage.workshop.post'].create({
            'name': 'Cabine peinture',
            'post_type': 'paint_booth',
            'is_bottleneck': True,
        })
        self.assertTrue(booth.is_bottleneck)

    def test_03_archive(self):
        """Archivage d'un poste."""
        self.post_pont.active = False
        self.assertFalse(self.post_pont.active)


class TestTechnician(TestPlanningBase):
    """Tests extension hr.employee pour techniciens."""

    def test_01_technician_fields(self):
        """Champs technicien correctement remplis."""
        self.assertTrue(self.technician.is_garage_technician)
        self.assertEqual(self.technician.garage_skill, 'body')
        self.assertEqual(self.technician.daily_capacity_hours, 8.0)

    def test_02_ev_certification(self):
        """Habilitation véhicule électrique."""
        self.technician.write({
            'has_ev_certification': True,
            'ev_certification_date': '2026-01-15',
        })
        self.assertTrue(self.technician.has_ev_certification)

    def test_03_multi_skill(self):
        """Technicien polyvalent."""
        tech = self.env['hr.employee'].create({
            'name': 'Paul Polyvalent',
            'is_garage_technician': True,
            'garage_skill': 'multi',
        })
        self.assertEqual(tech.garage_skill, 'multi')


class TestPlanningSlot(TestPlanningBase):
    """Tests créneaux planning."""

    def _create_slot(self, **kwargs):
        now = datetime(2026, 4, 1, 8, 0)
        vals = {
            'repair_order_id': self.repair_order.id,
            'post_id': self.post_pont.id,
            'technician_id': self.technician.id,
            'operation_type': 'body',
            'start_datetime': now,
            'end_datetime': now + timedelta(hours=4),
        }
        vals.update(kwargs)
        return self.env['garage.planning.slot'].create(vals)

    def test_01_create_slot(self):
        """Création d'un créneau planning."""
        slot = self._create_slot()
        self.assertEqual(slot.state, 'planned')
        self.assertEqual(slot.vehicle_plate, 'PLN-001-XX')

    def test_02_compute_duration(self):
        """Calcul automatique de la durée."""
        slot = self._create_slot()
        self.assertAlmostEqual(slot.duration_hours, 4.0, places=1)

    def test_03_workflow_start(self):
        """Workflow : planned → in_progress."""
        slot = self._create_slot()
        slot.action_start()
        self.assertEqual(slot.state, 'in_progress')

    def test_04_workflow_done(self):
        """Workflow : in_progress → done."""
        slot = self._create_slot()
        slot.action_start()
        slot.action_done()
        self.assertEqual(slot.state, 'done')

    def test_05_workflow_cancel(self):
        """Annulation d'un créneau."""
        slot = self._create_slot()
        slot.action_cancel()
        self.assertEqual(slot.state, 'cancelled')

    def test_06_workflow_reset(self):
        """Replanification d'un créneau annulé."""
        slot = self._create_slot()
        slot.action_cancel()
        slot.action_reset()
        self.assertEqual(slot.state, 'planned')

    def test_07_overlap_blocked_capacity_1(self):
        """Chevauchement interdit sur un poste à capacité 1."""
        now = datetime(2026, 4, 1, 8, 0)
        self._create_slot(
            start_datetime=now,
            end_datetime=now + timedelta(hours=4),
        )
        with self.assertRaises(ValidationError):
            self._create_slot(
                start_datetime=now + timedelta(hours=2),
                end_datetime=now + timedelta(hours=6),
            )

    def test_08_overlap_ok_capacity_multi(self):
        """Pas de blocage sur un poste à capacité > 1."""
        now = datetime(2026, 4, 1, 8, 0)
        self._create_slot(
            post_id=self.post_zone.id,
            start_datetime=now,
            end_datetime=now + timedelta(hours=4),
        )
        slot2 = self._create_slot(
            post_id=self.post_zone.id,
            start_datetime=now + timedelta(hours=2),
            end_datetime=now + timedelta(hours=6),
        )
        self.assertTrue(slot2.id)

    def test_09_cancelled_no_block(self):
        """Un créneau annulé ne bloque pas le poste."""
        now = datetime(2026, 4, 1, 8, 0)
        slot1 = self._create_slot(
            start_datetime=now,
            end_datetime=now + timedelta(hours=4),
        )
        slot1.action_cancel()
        slot2 = self._create_slot(
            start_datetime=now,
            end_datetime=now + timedelta(hours=4),
        )
        self.assertEqual(slot2.state, 'planned')

    def test_10_end_before_start_blocked(self):
        """Fin avant début interdit."""
        now = datetime(2026, 4, 1, 8, 0)
        with self.assertRaises(ValidationError):
            self._create_slot(
                start_datetime=now,
                end_datetime=now - timedelta(hours=1),
            )

    def test_11_ro_planning_count(self):
        """Compteur de créneaux sur l'OR."""
        self._create_slot()
        self.repair_order.invalidate_recordset()
        self.assertEqual(self.repair_order.planning_slot_count, 1)

    def test_12_ro_technician_assignment(self):
        """Affectation de techniciens sur l'OR."""
        self.repair_order.write({
            'technician_ids': [(4, self.technician.id)],
        })
        self.assertIn(self.technician, self.repair_order.technician_ids)

    def test_13_ro_workshop_chief(self):
        """Affectation du chef d'atelier sur l'OR."""
        self.repair_order.write({
            'workshop_chief_id': self.technician.id,
        })
        self.assertEqual(self.repair_order.workshop_chief_id, self.technician)

    def test_14_no_overlap_adjacent(self):
        """Créneaux adjacents autorisés (fin == début du suivant)."""
        now = datetime(2026, 4, 1, 8, 0)
        self._create_slot(
            start_datetime=now,
            end_datetime=now + timedelta(hours=4),
        )
        slot2 = self._create_slot(
            start_datetime=now + timedelta(hours=4),
            end_datetime=now + timedelta(hours=8),
        )
        self.assertTrue(slot2.id)

    def test_15_customer_name_related(self):
        """Champ customer_name rempli depuis l'OR."""
        slot = self._create_slot()
        self.assertEqual(slot.customer_name, 'Client Planning Test')
