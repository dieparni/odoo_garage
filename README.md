# Odoo Garage Pro — Spécification technique complète

## Vue d'ensemble

Module Odoo custom pour la gestion complète d'un atelier de carrosserie, peinture et mécanique automobile. Conçu pour Odoo 17 Community/Enterprise.

**Nom technique** : `garage_pro`
**Dépendances Odoo natives** : `base`, `contacts`, `fleet`, `stock`, `purchase`, `account`, `calendar`, `mail`, `portal`, `web`

---

## Architecture des modules

```
garage_pro/                          # Module principal (manifest, dépendances)
├── garage_pro_vehicle/              # Fiches véhicules
├── garage_pro_customer/             # Extension contacts / clients garage
├── garage_pro_insurance/            # Assurances, sinistres, experts
├── garage_pro_quotation/            # Devis et ordres de réparation (OR)
├── garage_pro_bodywork/             # Métier carrosserie
├── garage_pro_paint/                # Métier peinture
├── garage_pro_mechanic/             # Métier mécanique
├── garage_pro_planning/             # Planning atelier, postes, techniciens
├── garage_pro_parts/                # Pièces détachées (extension stock)
├── garage_pro_subcontract/          # Sous-traitance
├── garage_pro_courtesy/             # Véhicules de courtoisie
├── garage_pro_documentation/        # Photos, rapports, PV
├── garage_pro_billing/              # Extension facturation (multi-payeur)
├── garage_pro_communication/        # Notifications SMS/email, portail
├── garage_pro_quality/              # Checklists contrôle qualité
├── garage_pro_reporting/            # Tableaux de bord et KPIs
└── garage_pro_carvertical/          # Intégration CarVertical (phase 2)
```

---

## Stratégie d'intégration Odoo natif

### Modules Odoo réutilisés (NE PAS recoder)

| Besoin | Module Odoo natif | Stratégie |
|--------|-------------------|-----------|
| Contacts clients | `res.partner` | Hériter et étendre avec champs garage |
| Flotte véhicules | `fleet.vehicle` | Hériter et étendre (VIN, code peinture...) |
| Stock pièces | `stock.product` / `stock.move` | Utiliser tel quel + catégories custom |
| Achats fournisseurs | `purchase.order` | Utiliser tel quel, lier aux OR |
| Facturation | `account.move` | Hériter pour multi-payeur, franchise |
| Comptabilité | `account.*` | Utiliser tel quel |
| Calendrier/Planning | `calendar.event` | Utiliser comme base du planning |
| Messagerie | `mail.thread` / `mail.activity` | Intégrer dans chaque modèle métier |
| Portail client | `portal` | Étendre pour afficher OR/photos |
| Séquences | `ir.sequence` | Pour numéros de devis, OR, sinistre |

### Règle d'or
> **Hériter (`_inherit`) plutôt que recréer.** Chaque modèle custom qui a un équivalent Odoo DOIT en hériter. Cela garantit la compatibilité avec l'écosystème (rapports, exports, API, droits d'accès).

---

## Convention de nommage

| Élément | Convention | Exemple |
|---------|------------|---------|
| Modèle Python | `garage.xxx` | `garage.vehicle`, `garage.repair.order` |
| Vue XML | `garage_xxx_view_form` | `garage_repair_order_view_form` |
| Menu | `garage_menu_xxx` | `garage_menu_repair_orders` |
| Séquence | `garage.seq.xxx` | `garage.seq.repair_order` |
| Groupe sécurité | `garage_pro.group_xxx` | `garage_pro.group_manager` |
| Droit d'accès | `garage_pro.access_xxx` | `garage_pro.access_repair_order_user` |

---

## Groupes de sécurité

```
garage_pro.group_receptionist    — Réceptionniste (devis, accueil, planning lecture)
garage_pro.group_technician      — Technicien (pointage temps, consommation pièces)
garage_pro.group_workshop_chief  — Chef d'atelier (validation QC, planning écriture)
garage_pro.group_accountant      — Comptable garage (facturation, suivi paiements)
garage_pro.group_manager         — Gérant (tout accès, reporting, configuration)
```

---

## Flux principal (happy path)

```
Client arrive
    → Création/sélection véhicule
    → Création/sélection client
    → [Si sinistre] Création sinistre + lien assurance
    → Création devis (lignes MO + pièces + sous-traitance)
    → [Si assurance] Envoi devis à l'expert
    → Accord expert / client
    → Conversion devis → OR
    → Planification atelier (poste + technicien + dates)
    → [Si pièces manquantes] Commande fournisseur
    → Exécution travaux (pointage temps réel)
    → [Si supplément] Avenant devis → ré-accord
    → Contrôle qualité (checklist)
    → Facturation (client + assurance si applicable)
    → Notification client "véhicule prêt"
    → Restitution véhicule
```

---

## Phase 2 — Intégrations futures

- **CarVertical** : préremplissage fiche véhicule par VIN (voir `/integrations/carvertical.md`)
- **Audatex / DAT / GT Motive** : import barèmes temps
- **TecDoc / PartsLink24** : catalogue pièces par VIN
- **SMS gateway** : OVH SMS, Twilio, ou équivalent
- **Portail client avancé** : suivi temps réel, photos, signature électronique

---

## Instructions pour Claude Code

Voir `CLAUDE_CODE_PLAN.md` pour la stratégie d'exécution par agents.
