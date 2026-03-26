"""Opérations mécaniques liées aux ordres de réparation."""

from odoo import fields, models


class GarageMechanicOperation(models.Model):
    """Opération mécanique détaillée sur un OR."""

    _name = 'garage.mechanic.operation'
    _description = 'Opération mécanique'
    _inherit = ['mail.thread']
    _order = 'repair_order_id, id'

    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(string="Description", required=True)
    operation_category = fields.Selection([
        ('maintenance', 'Entretien courant'),
        ('repair', 'Réparation'),
        ('diagnostic', 'Diagnostic'),
        ('ct_prep', 'Préparation CT'),
        ('geometry', 'Géométrie / Parallélisme'),
        ('aircon', 'Climatisation'),
        ('electrical', 'Électricité / Électronique'),
        ('tires', 'Pneumatiques'),
        ('exhaust', 'Échappement'),
        ('other', 'Autre'),
    ], string="Catégorie", required=True)

    operation_type = fields.Selection([
        # Entretien
        ('oil_change', 'Vidange moteur'),
        ('filter_change', 'Remplacement filtres'),
        ('brake_pads', 'Plaquettes de frein'),
        ('brake_discs', 'Disques de frein'),
        ('timing_belt', 'Courroie de distribution'),
        ('spark_plugs', 'Bougies'),
        ('battery', 'Batterie'),
        ('coolant', 'Liquide de refroidissement'),
        # Réparation
        ('engine', 'Moteur'),
        ('gearbox', 'Boîte de vitesses'),
        ('clutch', 'Embrayage'),
        ('suspension', 'Suspension'),
        ('steering', 'Direction'),
        ('turbo', 'Turbo'),
        ('injectors', 'Injecteurs'),
        ('starter', 'Démarreur'),
        ('alternator', 'Alternateur'),
        # Diagnostic
        ('obd_scan', 'Lecture codes défaut OBD'),
        ('road_test', 'Essai routier'),
        ('compression', 'Test compression'),
        ('electrical_diag', 'Diagnostic électrique'),
        # Autre
        ('geometry_check', 'Contrôle géométrie'),
        ('aircon_recharge', 'Recharge climatisation'),
        ('tire_change', 'Changement pneumatiques'),
        ('tire_balance', 'Équilibrage'),
        ('other', 'Autre'),
    ], string="Type d'opération")

    # === DIAGNOSTIC ===
    obd_codes = fields.Text(
        string="Codes défaut OBD",
        help="Codes lus par la valise diagnostic (ex: P0300, P0171)",
    )
    obd_codes_cleared = fields.Boolean(string="Codes effacés")
    diagnosis_result = fields.Html(string="Résultat diagnostic")

    # === ENTRETIEN ===
    is_scheduled_maintenance = fields.Boolean(string="Entretien planifié")
    maintenance_plan_item_id = fields.Many2one(
        'garage.maintenance.plan.item',
        string="Point du plan d'entretien",
    )
    next_maintenance_km = fields.Integer(
        string="Prochain entretien (km)",
        help="Km du prochain entretien pour ce poste",
    )
    next_maintenance_date = fields.Date(string="Prochain entretien (date)")

    # === PNEUS ===
    tire_brand = fields.Char(string="Marque pneu")
    tire_size = fields.Char(string="Dimensions pneu (ex: 205/55 R16)")
    tire_dot = fields.Char(string="Code DOT (date fabrication)")
    tire_tread_depth = fields.Float(string="Profondeur sculpture (mm)")
    tire_position = fields.Selection([
        ('fl', 'Avant gauche'),
        ('fr', 'Avant droit'),
        ('rl', 'Arrière gauche'),
        ('rr', 'Arrière droit'),
        ('spare', 'Roue de secours'),
    ], string="Position pneu")

    # === EXÉCUTION ===
    allocated_time = fields.Float(string="Temps alloué (h)")
    actual_time = fields.Float(string="Temps réel (h)")
    technician_id = fields.Many2one('hr.employee', string="Mécanicien")

    state = fields.Selection([
        ('todo', 'À faire'),
        ('in_progress', 'En cours'),
        ('waiting_parts', 'Attente pièces'),
        ('done', 'Terminé'),
    ], default='todo', tracking=True, string="Statut")

    notes = fields.Text(string="Notes techniques")

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def action_start(self):
        """À faire → En cours."""
        self.write({'state': 'in_progress'})

    def action_wait_parts(self):
        """En cours → Attente pièces."""
        self.write({'state': 'waiting_parts'})

    def action_done(self):
        """En cours / Attente pièces → Terminé."""
        self.write({'state': 'done'})
