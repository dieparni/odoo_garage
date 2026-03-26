"""Documentation / Photos garage — gestion des documents liés aux OR et sinistres."""

import base64

from odoo import api, fields, models

from .constants import DAMAGE_ZONES


class GarageDocumentation(models.Model):
    """Document ou photo rattaché à un OR, sinistre ou véhicule."""

    _name = 'garage.documentation'
    _description = 'Document / Photo garage'
    _order = 'create_date desc'

    name = fields.Char(string="Description")
    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="OR",
    )
    claim_id = fields.Many2one(
        'garage.insurance.claim',
        string="Sinistre",
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Véhicule",
    )

    doc_type = fields.Selection([
        ('photo_before', 'Photo avant réparation'),
        ('photo_during', 'Photo pendant réparation'),
        ('photo_after', 'Photo après réparation'),
        ('photo_damage', 'Photo dommage'),
        ('accident_report', 'Constat amiable'),
        ('expertise_report', "Rapport d'expertise"),
        ('invoice_supplier', 'Facture fournisseur'),
        ('technical_report', 'Rapport technique'),
        ('courtesy_checkin', 'État des lieux courtoisie'),
        ('other', 'Autre'),
    ], string="Type de document", required=True, default='other')

    file = fields.Binary(string="Fichier", required=True)
    filename = fields.Char(string="Nom de fichier")
    thumbnail = fields.Binary(
        string="Miniature",
        compute='_compute_thumbnail',
        store=True,
        help="Miniature générée automatiquement pour les images",
    )
    file_size = fields.Integer(
        string="Taille (Ko)",
        compute='_compute_file_size',
        store=True,
    )

    damage_zone = fields.Selection(
        DAMAGE_ZONES,
        string="Zone (si photo dommage)",
    )
    taken_by = fields.Many2one(
        'res.users',
        string="Pris par",
        default=lambda self: self.env.user,
    )
    taken_date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
    )
    notes = fields.Text(string="Notes")
    is_visible_portal = fields.Boolean(
        string="Visible sur le portail client",
        default=True,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('file', 'filename')
    def _compute_thumbnail(self):
        for rec in self:
            if rec.file and rec.filename:
                ext = (rec.filename or '').rsplit('.', 1)[-1].lower()
                if ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'):
                    try:
                        image_data = base64.b64decode(rec.file)
                        from odoo.tools.image import image_process
                        rec.thumbnail = base64.b64encode(
                            image_process(image_data, size=(128, 128), crop='center')
                        )
                        continue
                    except Exception:
                        pass
            rec.thumbnail = False

    @api.depends('file')
    def _compute_file_size(self):
        for rec in self:
            if rec.file:
                # Binary field en base64 — taille réelle ≈ len(b64) * 3/4
                rec.file_size = int(len(rec.file) * 3 / 4 / 1024)
            else:
                rec.file_size = 0
