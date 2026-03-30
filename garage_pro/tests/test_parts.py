"""Tests pour les pièces & stock garage."""

from odoo.tests.common import TransactionCase


class TestGarageParts(TransactionCase):
    """Tests extension product.template pour pièces garage."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categ = cls.env.ref(
            'garage_pro.garage_product_categ_oem', raise_if_not_found=False
        )

    def _create_part(self, **kwargs):
        vals = {
            'name': 'Aile avant gauche Golf 7',
            'is_garage_part': True,
            'garage_part_category': 'oem',
            'type': 'consu',
            'list_price': 350.0,
            'standard_price': 200.0,
        }
        vals.update(kwargs)
        return self.env['product.template'].create(vals)

    def test_01_create_oem_part(self):
        """Création d'une pièce OEM."""
        part = self._create_part(
            oem_reference='5G0821105A',
            tecdoc_reference='123456',
        )
        self.assertTrue(part.is_garage_part)
        self.assertEqual(part.garage_part_category, 'oem')
        self.assertEqual(part.oem_reference, '5G0821105A')

    def test_02_aftermarket_part(self):
        """Création d'une pièce aftermarket."""
        part = self._create_part(
            name='Disque de frein avant',
            garage_part_category='aftermarket',
            oem_reference='',
        )
        self.assertEqual(part.garage_part_category, 'aftermarket')

    def test_03_consignment_part(self):
        """Pièce consignée avec montant."""
        part = self._create_part(
            name='Turbo échange standard',
            garage_part_category='exchange',
            is_consignment=True,
            consignment_amount=200.0,
        )
        self.assertTrue(part.is_consignment)
        self.assertEqual(part.consignment_amount, 200.0)

    def test_04_paint_product(self):
        """Produit peinture."""
        part = self._create_part(
            name='Vernis bi-composant 2K',
            garage_part_category='paint',
            type='consu',
        )
        self.assertEqual(part.garage_part_category, 'paint')

    def test_05_consumable_product(self):
        """Consommable atelier."""
        part = self._create_part(
            name='Disque abrasif P800',
            garage_part_category='consumable',
            type='consu',
        )
        self.assertEqual(part.garage_part_category, 'consumable')

    def test_06_product_categories_exist(self):
        """Les catégories de produits garage existent."""
        categ_ids = [
            'garage_pro.garage_product_categ_parts',
            'garage_pro.garage_product_categ_oem',
            'garage_pro.garage_product_categ_aftermarket',
            'garage_pro.garage_product_categ_used',
            'garage_pro.garage_product_categ_exchange',
            'garage_pro.garage_product_categ_paint',
            'garage_pro.garage_product_categ_consumable',
        ]
        for xml_id in categ_ids:
            categ = self.env.ref(xml_id, raise_if_not_found=False)
            self.assertTrue(categ, f"Catégorie {xml_id} introuvable")

    def test_07_oem_categ_parent(self):
        """OEM est enfant de 'Pièces garage'."""
        parent = self.env.ref('garage_pro.garage_product_categ_parts')
        oem = self.env.ref('garage_pro.garage_product_categ_oem')
        self.assertEqual(oem.parent_id, parent)

    def test_08_compatible_vehicles(self):
        """Champ véhicules compatibles renseigné."""
        part = self._create_part(
            compatible_vehicle_models='VW Golf 7, VW Golf 8, Audi A3 8V',
        )
        self.assertIn('Golf 7', part.compatible_vehicle_models)

    def test_09_used_part(self):
        """Pièce d'occasion."""
        part = self._create_part(
            name='Rétroviseur occasion',
            garage_part_category='used',
        )
        self.assertEqual(part.garage_part_category, 'used')
