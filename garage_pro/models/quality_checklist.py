"""Contrôle qualité — checklists et points de contrôle."""

from odoo import api, fields, models


class GarageQualityChecklist(models.Model):
    """Checklist de contrôle qualité liée à un OR."""

    _name = 'garage.quality.checklist'
    _description = 'Checklist contrôle qualité'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="OR",
        required=True,
        ondelete='cascade',
    )
    checklist_type = fields.Selection([
        ('bodywork', 'Contrôle carrosserie'),
        ('paint', 'Contrôle peinture'),
        ('mechanic', 'Contrôle mécanique'),
        ('general', 'Contrôle général pré-livraison'),
    ], string="Type de contrôle", required=True, default='general')

    item_ids = fields.One2many(
        'garage.quality.check.item',
        'checklist_id',
        string="Points de contrôle",
    )
    is_fully_checked = fields.Boolean(
        string="Tous contrôlés",
        compute='_compute_fully_checked',
        store=True,
    )
    checked_by = fields.Many2one(
        'res.users',
        string="Contrôlé par",
    )
    check_date = fields.Datetime(string="Date du contrôle")
    overall_result = fields.Selection([
        ('pass', 'Conforme'),
        ('fail', 'Non conforme'),
        ('partial', 'Partiellement conforme'),
    ], string="Résultat global",
        compute='_compute_result',
        store=True,
        tracking=True,
    )
    notes = fields.Text(string="Remarques générales")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('item_ids.result')
    def _compute_fully_checked(self):
        for rec in self:
            items = rec.item_ids
            if not items:
                rec.is_fully_checked = False
            else:
                rec.is_fully_checked = all(
                    item.result for item in items
                )

    @api.depends('item_ids.result')
    def _compute_result(self):
        for rec in self:
            items = rec.item_ids
            if not items or not rec.is_fully_checked:
                rec.overall_result = False
                continue
            results = items.mapped('result')
            if all(r in ('ok', 'na') for r in results):
                rec.overall_result = 'pass'
            elif any(r == 'nok' for r in results):
                has_ok = any(r == 'ok' for r in results)
                rec.overall_result = 'partial' if has_ok else 'fail'
            else:
                rec.overall_result = 'pass'

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_validate(self):
        """Valide la checklist et enregistre le contrôleur."""
        self.write({
            'checked_by': self.env.user.id,
            'check_date': fields.Datetime.now(),
        })

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------

    @api.model
    def create_from_repair_order(self, repair_order):
        """Crée une checklist auto basée sur les types d'opérations de l'OR."""
        checklist = self.create({
            'repair_order_id': repair_order.id,
            'checklist_type': 'general',
        })
        # Items standards pré-livraison
        standard_items = [
            ('Propreté extérieure du véhicule', 'visual'),
            ('Propreté intérieure du véhicule', 'visual'),
            ('Vérification éclairage', 'functional'),
            ('Vérification niveaux (huile, LR, lave-glace)', 'functional'),
            ('Pression pneus', 'measurement'),
        ]
        # Items carrosserie si applicable
        if repair_order.line_ids.filtered(
            lambda l: l.line_type == 'labor_body'
        ):
            standard_items += [
                ('Ajustement jeux de carrosserie', 'measurement'),
                ('Alignement panneaux', 'visual'),
                ('Étanchéité joints', 'functional'),
            ]
        # Items peinture
        if repair_order.line_ids.filtered(
            lambda l: l.line_type == 'labor_paint'
        ):
            standard_items += [
                ('Qualité peinture — pas de coulure', 'visual'),
                ('Qualité peinture — pas de grain', 'visual'),
                ('Raccord de teinte uniforme', 'visual'),
                ('Brillance et vernis', 'visual'),
            ]
        # Items mécanique
        if repair_order.line_ids.filtered(
            lambda l: l.line_type == 'labor_mech'
        ):
            standard_items += [
                ('Essai routier effectué', 'functional'),
                ('Pas de bruit anormal', 'functional'),
                ('Voyants tableau de bord éteints', 'visual'),
                ('Codes défaut effacés', 'functional'),
            ]
        ItemModel = self.env['garage.quality.check.item']
        for seq, (item_name, check_type) in enumerate(standard_items, 1):
            ItemModel.create({
                'checklist_id': checklist.id,
                'name': item_name,
                'check_type': check_type,
                'sequence': seq * 10,
            })
        return checklist


class GarageQualityCheckItem(models.Model):
    """Point individuel du contrôle qualité."""

    _name = 'garage.quality.check.item'
    _description = 'Point de contrôle qualité'
    _order = 'sequence, id'

    checklist_id = fields.Many2one(
        'garage.quality.checklist',
        ondelete='cascade',
        required=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Point de contrôle", required=True)
    check_type = fields.Selection([
        ('visual', 'Contrôle visuel'),
        ('functional', 'Contrôle fonctionnel'),
        ('measurement', 'Mesure'),
    ], string="Type")
    result = fields.Selection([
        ('ok', 'OK'),
        ('nok', 'Non conforme'),
        ('na', 'Non applicable'),
    ], string="Résultat")
    notes = fields.Char(string="Remarque")
    photo = fields.Binary(string="Photo")
