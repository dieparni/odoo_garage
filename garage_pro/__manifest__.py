{
    'name': 'Garage Pro',
    'version': '17.0.1.0.0',
    'category': 'Services/Garage',
    'summary': 'Gestion complète atelier carrosserie, peinture et mécanique',
    'description': """
        Module de gestion garage automobile :
        - Fiches véhicules étendues (VIN, peinture, historique)
        - Gestion sinistres et assurances
        - Devis et ordres de réparation multi-métier
        - Planning atelier et techniciens
        - Sous-traitance et véhicules de courtoisie
        - Facturation multi-payeur (client, assurance, franchise)
        - Contrôle qualité et documentation photo
        - Reporting et tableaux de bord
        - Intégration CarVertical (phase 2)
    """,
    'author': 'Volpe Services',
    'website': 'https://volpe-services.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'fleet',
        'mail',
        'account',
        'hr',
        'stock',
        'purchase',
        'purchase_stock',
        'product',
        'portal',
        'calendar',
        'web',
    ],
    'data': [
        # Sécurité (TOUJOURS en premier)
        'security/garage_pro_groups.xml',
        'security/ir.model.access.csv',
        'security/garage_pro_rules.xml',

        # Données
        'data/garage_sequences.xml',
        'data/garage_product_categories.xml',
        'data/garage_mail_templates.xml',
        'data/garage_crons.xml',
        'data/garage_config_defaults.xml',
        'data/garage_fiscal_position.xml',

        # Wizards (avant les vues pour les références d'action)
        'wizard/courtesy_return_wizard.xml',

        # Rapports
        'report/quotation_report.xml',
        'report/repair_order_report.xml',
        'report/invoice_garage_report.xml',
        'report/quality_checklist_report.xml',

        # Vues
        'views/vehicle_views.xml',
        'views/customer_views.xml',
        'views/insurance_views.xml',
        'views/claim_views.xml',
        'views/quotation_views.xml',
        'views/repair_order_views.xml',
        'views/trade_views.xml',
        'views/planning_views.xml',
        'views/parts_views.xml',
        'views/subcontract_views.xml',
        'views/courtesy_views.xml',
        'views/billing_views.xml',
        'views/quality_views.xml',
        'views/documentation_views.xml',
        'views/reporting_views.xml',
        'views/carvertical_views.xml',
        'views/config_views.xml',
        'views/portal_templates.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
