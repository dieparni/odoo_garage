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
    ],
    'data': [
        # Sécurité (TOUJOURS en premier)
        'security/garage_pro_groups.xml',
        'security/ir.model.access.csv',

        # Données
        'data/garage_sequences.xml',

        # Vues
        'views/vehicle_views.xml',
        'views/customer_views.xml',
        'views/insurance_views.xml',
        'views/claim_views.xml',
        'views/quotation_views.xml',
        'views/repair_order_views.xml',
        'views/trade_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
