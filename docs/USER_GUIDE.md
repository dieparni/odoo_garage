# Guide Utilisateur — Garage Pro (Odoo 17)

**Module de gestion complète pour atelier carrosserie, peinture et mécanique**
**Version** : 17.0.1.0.0 | **Auteur** : Volpe Services

---

## Table des matières

1. [Présentation générale](#1-présentation-générale)
2. [Gestion des accès et sécurité](#2-gestion-des-accès-et-sécurité)
3. [Guide par module fonctionnel](#3-guide-par-module-fonctionnel)
4. [Scénarios pas à pas](#4-scénarios-pas-à-pas)
5. [Configuration et paramétrage](#5-configuration-et-paramétrage)
6. [FAQ et dépannage](#6-faq-et-dépannage)

---

## 1. Présentation générale

### 1.1. À quoi sert le module Garage Pro ?

Garage Pro est un module Odoo 17 conçu pour gérer l'intégralité du flux de travail d'un atelier de carrosserie, peinture et mécanique. Il couvre :

- **L'accueil du client** : enregistrement du véhicule, création du devis
- **La gestion des sinistres assurance** : déclaration, expertise, suppléments, franchise
- **Les ordres de réparation** : planification, suivi des opérations par métier, temps réel
- **Le planning atelier** : affectation des techniciens, postes de travail, calendrier
- **La gestion des pièces et du stock** : commandes fournisseurs automatiques, pièces OEM/aftermarket
- **La sous-traitance** : bons de sous-traitance pour les travaux externalisés
- **Les véhicules de courtoisie** : prêt, suivi, facturation des jours excédentaires
- **La facturation multi-payeur** : client intégral, split assurance/franchise, acomptes
- **Le contrôle qualité** : checklists par métier, validation chef d'atelier
- **La documentation** : photos avant/pendant/après, rapports d'expertise
- **Le reporting** : chiffre d'affaires par activité, productivité atelier, marges
- **Le portail client** : consultation des devis, OR et factures en ligne
- **L'intégration CarVertical** : vérification de l'historique véhicule par VIN

### 1.2. Les 5 profils utilisateur

| Profil | Rôle | Utilisation typique |
|--------|------|---------------------|
| **Réceptionniste** | Accueil client, création devis, gestion administrative | Enregistre les véhicules, crée les devis, gère les sinistres, prête les véhicules de courtoisie |
| **Technicien** | Exécution des travaux en atelier | Pointe son temps, met à jour l'avancement des opérations, consomme les pièces |
| **Chef d'atelier** | Supervision de l'atelier | Gère le planning, crée les OR, affecte les techniciens, valide le contrôle qualité |
| **Comptable** | Gestion financière | Crée les factures, suit les paiements, consulte le reporting financier |
| **Gérant** | Direction complète | Accès total : configuration, reporting, suppression, gestion des utilisateurs |

### 1.3. Flux principal

```
Client arrive → Enregistrement véhicule → Création devis
                                              ↓
                               [Sinistre ?] → Déclaration assurance → Expertise
                                              ↓
                                    Approbation devis (client ou assurance)
                                              ↓
                                    Conversion en Ordre de Réparation (OR)
                                              ↓
                         Planification (techniciens, postes, planning)
                                              ↓
                    ┌─────────────┬────────────┬──────────────┐
                    ↓             ↓            ↓              ↓
              Carrosserie    Peinture    Mécanique    Sous-traitance
                    ↓             ↓            ↓              ↓
                    └─────────────┴────────────┴──────────────┘
                                              ↓
                                    Contrôle qualité (QC)
                                              ↓
                                    Validation QC
                                              ↓
                                    Véhicule prêt → Notification client
                                              ↓
                                    Facturation (client / assurance / split)
                                              ↓
                                    Restitution véhicule
```

---

## 2. Gestion des accès et sécurité

### 2.1. Groupes de sécurité

Le module définit 5 groupes de sécurité organisés en hiérarchie. Chaque groupe hérite des droits du groupe précédent.

#### Hiérarchie des groupes

```
Gérant (accès complet)
├── Chef d'atelier
│   └── Technicien
│       └── Réceptionniste
└── Comptable garage
    └── Réceptionniste
```

#### Réceptionniste (`garage_pro.group_receptionist`)

- **Ce qu'il peut VOIR** : véhicules, clients, devis, sinistres, suppléments, compagnies d'assurance, experts, plans d'entretien, pièces (catalogue), véhicules de courtoisie, prêts, documents/photos, systèmes de peinture, rapports CA et activité, cache CarVertical
- **Ce qu'il peut FAIRE** : créer des devis et lignes de devis, créer des sinistres et suppléments, modifier des véhicules, modifier des prêts de courtoisie, créer des sous-traitances, créer des documents/photos, utiliser le wizard de facturation, lancer une recherche CarVertical, créer des demandes de supplément, restituer un véhicule de courtoisie
- **Ce qu'il ne peut PAS faire** : créer des OR, créer des postes de travail, modifier les formules peinture, supprimer des enregistrements, accéder à la configuration

#### Technicien (`garage_pro.group_technician`)

*Hérite de tous les droits du Réceptionniste, plus :*

- **Ce qu'il peut FAIRE en plus** : modifier les OR et lignes d'OR (pointer le temps, marquer terminé), modifier les opérations carrosserie/peinture/mécanique, créer des consommations peinture, modifier les créneaux planning, créer des documents/photos
- **Ce qu'il ne peut PAS faire** : créer des OR, créer des opérations, créer des postes de travail, supprimer des enregistrements

#### Chef d'atelier (`garage_pro.group_workshop_chief`)

*Hérite de tous les droits du Technicien, plus :*

- **Ce qu'il peut FAIRE en plus** : créer des OR et lignes d'OR, créer des opérations (carrosserie, peinture, mécanique), créer des créneaux planning, modifier les postes de travail, créer des checklists qualité et items, créer des sous-traitances
- **Ce qu'il ne peut PAS faire** : supprimer des enregistrements, modifier la configuration, gérer les compagnies d'assurance

#### Comptable garage (`garage_pro.group_accountant`)

*Hérite de tous les droits du Réceptionniste, plus :*

- **Ce qu'il peut FAIRE en plus** : utiliser le wizard de facturation, consulter les rapports CA et activité
- **Ce qu'il ne peut PAS faire** : modifier les opérations atelier, gérer le planning, supprimer des enregistrements

#### Gérant (`garage_pro.group_manager`)

*Hérite de tous les droits du Chef d'atelier ET du Comptable, plus :*

- **Ce qu'il peut FAIRE en plus** : tout créer, modifier et supprimer, gérer la configuration (taux horaires, TVA, CarVertical), gérer les compagnies d'assurance et experts, gérer les systèmes et formules peinture, anonymiser les clients (RGPD), gérer les postes de travail

### 2.2. Tableau récapitulatif des permissions

Légende : **L** = Lecture | **E** = Écriture | **C** = Création | **S** = Suppression

| Modèle | Réceptionniste | Technicien | Chef atelier | Comptable | Gérant |
|--------|:-:|:-:|:-:|:-:|:-:|
| **Véhicules** (fleet.vehicle) | L E C | L E | L E C | L E C | L E C S |
| **Systèmes peinture** | L | L | L | L | L E C S |
| **Compagnies assurance** | L | L | L | L | L E C S |
| **Experts** | L | L | L | L | L E C S |
| **Sinistres** | L E C | L E C | L E C | L E C | L E C S |
| **Suppléments sinistre** | L E C | L E C | L E C | L E C | L E C S |
| **Devis** | L E C | L E C | L E C | L E C | L E C S |
| **Lignes de devis** | L E C | L E C | L E C | L E C | L E C S |
| **Ordres de réparation** | L E | L E | L E C | L E | L E C S |
| **Lignes d'OR** | – | L E | L E C | – | L E C S |
| **Opérations carrosserie** | – | L E | L E C | – | L E C S |
| **Opérations peinture** | – | L E | L E C | – | L E C S |
| **Opérations mécanique** | – | L E | L E C | – | L E C S |
| **Formules peinture** | – | L | L | – | L E C S |
| **Consommation peinture** | – | L E | L E | – | L E C S |
| **Plans d'entretien** | L | L | L | L | L E C S |
| **Items entretien** | L | L | L | L | L E C S |
| **Postes de travail** | – | L | L E | – | L E C S |
| **Créneaux planning** | – | L E | L E C | – | L E C S |
| **Sous-traitance** | L E C | L E C | L E C | L E C | L E C S |
| **Véhicules courtoisie** | L E | L E | L E | L E | L E C S |
| **Prêts courtoisie** | L E C | L E C | L E C | L E C | L E C S |
| **Wizard facturation** | L E C | L E C | L E C | L E C | L E C S |
| **Checklists qualité** | – | L E | L E C | – | L E C S |
| **Items checklist** | – | L E | L E C | – | L E C S |
| **Documents / Photos** | L E C | L E C | L E C | L E C | L E C S |
| **Rapport CA** | L | L | L | L | L |
| **Rapport activité** | L | L | L | L | L |
| **Cache CarVertical** | L | L | L | L | L E C S |
| **Wizard CarVertical** | L E C | L E C | L E C | L E C | L E C S |
| **Wizard supplément** | L E C | L E C | L E C | L E C | L E C S |
| **Wizard restitution courtoisie** | L E C | L E C | L E C | L E C | L E C S |

### 2.3. Règles multi-société

Trois règles d'isolation assurent que chaque société ne voit que ses propres données :

- **Devis** : filtrés par société de l'utilisateur
- **Ordres de réparation** : filtrés par société de l'utilisateur
- **Sous-traitance** : filtrés par société de l'utilisateur

### 2.4. Comment modifier les accès d'un utilisateur

1. Allez dans **Configuration > Utilisateurs et sociétés > Utilisateurs**
2. Ouvrez la fiche de l'utilisateur concerné
3. Dans l'onglet **Droits d'accès**, cherchez la section **Garage**
4. Sélectionnez le groupe souhaité dans la liste déroulante :
   - Réceptionniste
   - Technicien
   - Chef d'atelier
   - Comptable garage
   - Gérant
5. Cliquez sur **Enregistrer**

> **Attention** : Le groupe Gérant inclut automatiquement les droits de Chef d'atelier ET de Comptable. Pas besoin de cocher plusieurs groupes.

---

## 3. Guide par module fonctionnel

### 3.1. Véhicules

**Accès** : Menu **Garage > Réception > Véhicules**

#### Navigation

Le menu ouvre une liste de tous les véhicules enregistrés. Vous pouvez basculer entre les vues liste, formulaire et kanban.

#### Champs du formulaire

**En-tête :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Modèle | Marque et modèle du véhicule (champ natif Odoo fleet) | Oui |
| Immatriculation | Plaque d'immatriculation | Oui |
| VIN (vin_sn) | Numéro d'identification du véhicule (17 caractères) | Non (mais recommandé) |
| Référence garage | Code interne auto-généré (ex: VEH/2026/00001) | Auto |

**Onglet Carrosserie / Peinture :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Type de carrosserie | Berline, Break, SUV, Coupé, Cabriolet, Monospace, Utilitaire, Pickup, Citadine, Autre | Non |
| Code peinture | Code couleur constructeur (ex: LY9T, 475) | Non |
| Nom de la teinte | Nom commercial de la couleur | Non |
| Système de peinture | Fabricant peinture utilisé (Standox, Sikkens, PPG...) | Non |

**Onglet Mécanique :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Code moteur | Référence du moteur (ex: N47D20A) | Non |
| Cylindrée (cm³) | Volume moteur en centimètres cubes | Non |
| Puissance (kW) | Puissance en kilowatts | Non |
| Puissance (CV) | Calculé automatiquement (kW × 1,36) | Auto |
| Type de boîte | Manuelle, Automatique, Semi-auto, CVT | Non |
| Type de transmission | Traction (FWD), Propulsion (RWD), Intégrale (AWD), 4×4 | Non |

**Section Électrique/Hybride** (visible si véhicule électrique ou hybride) :

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Capacité batterie (kWh) | Capacité de la batterie haute tension | Non |
| Type de connecteur | Type 1, Type 2, CCS Combo, CHAdeMO, Tesla | Non |

**Onglet CT & Garantie :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Dernier contrôle technique | Date du dernier CT | Non |
| Prochain CT | Calculé automatiquement (+1 an) | Auto |
| Résultat CT | Favorable, Favorable avec remarques, Défavorable, Dangereux | Non |
| Fin de garantie | Date d'expiration de la garantie constructeur | Non |
| Sous garantie | Calculé automatiquement | Auto |

**Onglet Propriété :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Date 1ère immatriculation | Date de première mise en circulation | Non |
| Pays d'immatriculation | Pays d'origine de la plaque | Non |
| Type de propriété | Privé, Leasing, LLD, Flotte, Location | Non |
| Société de leasing | Si propriété = Leasing/LLD | Non |
| Propriétaire réel | Personne ou société propriétaire | Non |

**Onglet Formules peinture :**

Liste des formules de teinte enregistrées pour ce véhicule (code constructeur, système, variante, date spectro).

**Onglet Notes internes :**

Champ texte libre pour notes internes sur le véhicule.

#### Smart buttons (boutons compteurs)

- **OR** : Nombre d'ordres de réparation — cliquez pour les voir
- **Sinistres** : Nombre de sinistres — cliquez pour les voir
- **Total dépensé** : Montant total des réparations effectuées

#### Bouton CarVertical

Visible dans l'en-tête si un VIN est renseigné. Lance une recherche dans la base CarVertical pour vérifier l'historique du véhicule (kilométrage, dommages, rappels).

#### Filtres de recherche

- **Sous garantie** : véhicules avec garantie encore valide
- **Électrique/Hybride** : véhicules à motorisation électrique ou hybride
- **Par type de carrosserie** : Berline, SUV, Utilitaire
- **Regrouper par** : type de carrosserie, type de propriété, système de peinture

---

### 3.2. Clients

**Accès** : Menu **Garage > Réception > Clients**

#### Champs du formulaire

Le formulaire client hérite du formulaire standard Odoo (res.partner) et ajoute un onglet **Garage**.

**Onglet Garage :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Client garage | Coché automatiquement à la création d'un devis | Auto |
| Type de client | Particulier, Professionnel, Gestionnaire de flotte, Société de leasing, Compagnie d'assurance, Sous-traitant, Concessionnaire | Non |
| Grille tarifaire | Standard, Flotte, VIP, Assurance | Non |
| Remise garage (%) | Taux de remise appliqué par défaut | Non |
| Conditions de paiement | Conditions de paiement spécifiques au garage | Non |
| Plafond crédit | Montant maximum d'encours autorisé | Non |
| Langue préférée | FR, NL, EN, DE | Non |
| Mode de contact | Email, SMS, Téléphone, Portail | Non |
| Alertes entretien | Recevoir les alertes de maintenance | Non |
| Alertes CT | Recevoir les alertes de contrôle technique | Non |

**Onglet Véhicules :**

Liste des véhicules associés au client (en tant que conducteur et en tant que propriétaire).

**Onglet Flotte** (visible pour les gestionnaires de flotte) :

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Approbation requise | Demander une approbation avant conversion devis→OR | Non |
| Seuil d'approbation (€) | Montant au-delà duquel l'approbation est requise | Non |
| Conducteurs de la flotte | Liste des conducteurs rattachés | Non |

**Section Facturation garage** (en bas du formulaire) :

| Indicateur | Description |
|------------|-------------|
| Total facturé | Montant total facturé au client via le garage |
| Encours | Solde impayé des factures garage |
| Dernière visite | Date de la dernière restitution de véhicule |
| Nombre de factures | Total des factures garage émises |

#### Blocage client

| Champ | Description |
|-------|-------------|
| Bloqué (garage) | Si coché, empêche la conversion de devis en OR |
| Raison du blocage | Obligatoire si le client est bloqué |

> **Attention** : Un client bloqué ne pourra pas recevoir de nouvelle commande de réparation. Débloquez-le en décochant la case "Bloqué".

#### Bouton Anonymiser (RGPD)

Accessible uniquement au Gérant. Anonymise de manière irréversible toutes les données personnelles du client. Bloqué si des OR sont en cours.

#### Smart buttons

- **OR** : Nombre d'ordres de réparation du client
- **Véhicules** : Nombre de véhicules associés

---

### 3.3. Assurances

#### 3.3.1. Compagnies d'assurance

**Accès** : Menu **Garage > Assurances > Compagnies**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Nom | Nom de la compagnie (AXA, Ethias, AG...) | Oui |
| Contact Odoo | Partenaire Odoo lié (pour la facturation) | Oui |
| Code interne | Code court (ex: AXA, ETH) | Non |

**Onglet Barèmes :**

| Champ | Description |
|-------|-------------|
| Taux horaire carrosserie (€/h) | Taux agréé pour la main d'œuvre carrosserie |
| Taux horaire peinture (€/h) | Taux agréé pour la main d'œuvre peinture |
| Taux horaire mécanique (€/h) | Taux agréé pour la main d'œuvre mécanique |
| Coefficient pièces | Multiplicateur appliqué aux pièces (défaut : 1,0) |
| Taux matière peinture (€/h) | Taux par heure peinte pour la matière |
| Pièces aftermarket autorisées | L'assurance accepte les pièces non-OEM |
| Pièces occasion autorisées | L'assurance accepte les pièces d'occasion |
| Âge max pièces neuves (ans) | Âge véhicule au-delà duquel les pièces occasion sont autorisées |

**Onglet Contacts :**

| Champ | Description |
|-------|-------------|
| Contact principal | Nom du contact principal |
| Téléphone / Email | Coordonnées du contact |
| Email déclaration sinistres | Adresse pour les déclarations |
| URL portail | Lien vers le portail en ligne de l'assurance |
| Experts agréés | Liste des experts liés à cette compagnie |

**Onglet Conditions :**

| Champ | Description |
|-------|-------------|
| Type de convention | Directe, Indirecte, Mixte |
| Conditions de paiement | Conditions de paiement de l'assurance |
| Délai moyen constaté (j) | Délai moyen de paiement observé |
| Notes / Particularités | Informations complémentaires |

**Smart buttons :**
- **Sinistres** : Nombre de sinistres avec cette compagnie
- **Encours** : Montant total des factures impayées

#### 3.3.2. Sinistres

**Accès** : Menu **Garage > Assurances > Sinistres**

Les sinistres peuvent être vus en liste, formulaire ou **kanban** (colonnes par statut).

**Workflow du sinistre (13 états) :**

```
Brouillon → Déclaré → Expertise demandée → Expertise réalisée → Approuvé
                                                                    ↓
                                              [Supplément ?] → Supplément demandé → Supplément approuvé
                                                                    ↓
                                                          Travaux en cours → Facturé → Payé
                                                                    ↓
                                            Alternatives : VEI (perte totale) / Litige / Annulé
```

**Boutons d'action :**

| Bouton | Transition | Condition |
|--------|-----------|-----------|
| Déclarer | Brouillon → Déclaré | – |
| Demander expertise | Déclaré → Expertise demandée | Crée une activité de suivi |
| Expertise réalisée | Expertise demandée → Expertise réalisée | – |
| Approuver | Expertise réalisée → Approuvé | Montant approuvé doit être renseigné |
| Approuver (sans expertise) | Déclaré → Approuvé | Pour les petits sinistres sans expertise |
| Démarrer travaux | Approuvé → Travaux en cours | Un OR doit être lié au sinistre |
| Demander supplément | Ouvre un wizard | Crée un supplément et passe en "Supplément demandé" |
| VEI | Tout état → VEI | Envoie un email au client |
| Marquer facturé | Travaux en cours → Facturé | – |
| Marquer payé | Facturé → Payé | – |
| Litige | Tout état → Litige | – |
| Annuler | Tout état → Annulé | – |

**Champs du formulaire :**

**Onglet Sinistre :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Véhicule | Véhicule concerné | Oui |
| Client (assuré) | Propriétaire/conducteur assuré | Oui |
| Compagnie d'assurance | Assureur du véhicule | Oui |
| Date du sinistre | Date de l'accident/événement | Oui |
| Date de déclaration | Date de déclaration à l'assurance | Non |
| Type de sinistre | Collision, Vol, Vandalisme, Grêle, Bris de glace, Catastrophe naturelle, Incendie, Parking, Animal, Autre | Oui |
| N° de police | Numéro de la police d'assurance | Non |
| N° sinistre assurance | Numéro de dossier chez l'assureur | Non |
| Circonstances | Description détaillée de l'événement | Non |
| Tiers impliqué | Un autre véhicule/personne est impliqué | Non |
| PV de police | Un procès-verbal a été dressé | Non |

**Onglet Expertise :**

| Champ | Description |
|-------|-------------|
| Expert assigné | Expert désigné pour l'évaluation |
| Type d'expertise | Sur site, À distance, Dispensée |
| Date expertise prévue | Date planifiée |
| Date expertise réalisée | Date effective |
| Rapport d'expertise | Fichier du rapport (PDF) |
| Montant estimé | Montant du devis initial |
| Montant approuvé | Montant validé par l'expert |

**Onglet Suppléments :**

Liste des demandes de supplément avec état (Brouillon, Envoyé, Approuvé, Rejeté), montant demandé, montant approuvé, date de réponse.

**Onglet VEI (Perte totale) :**

| Champ | Description |
|-------|-------------|
| Véhicule Économiquement Irréparable | Case à cocher |
| Valeur vénale | Valeur estimée du véhicule |
| Coût réparation estimé | Coût si réparation effectuée |
| Décision client | En attente, Accepte la perte, Répare à ses frais, Conteste |

**Onglet Financier :**

| Champ | Description |
|-------|-------------|
| Type de franchise | Aucune, Fixe, Pourcentage, Variable |
| Montant franchise | Montant fixe ou calculé |
| Franchise (%) | Pourcentage si franchise en % |
| Franchise calculée | Montant final de la franchise |
| Montant facturé | Total des factures liées au sinistre |
| Montant encaissé | Total des paiements reçus |
| Différence assurance | Écart entre montant approuvé et montant payé |
| Action différence | Absorbée, Refacturée au client, Contestée |

**Onglet Documents :**

Constat amiable (fichier) et liste des documents/photos associés.

---

### 3.4. Devis

**Accès** : Menu **Garage > Réception > Devis**

#### Workflow du devis

```
Brouillon → Envoyé → Accepté → Converti en OR
                 ↓
              Refusé / Annulé
```

#### Boutons d'action

| Bouton | Transition | Description |
|--------|-----------|-------------|
| Envoyer | Brouillon → Envoyé | Envoie le devis par email au client (et à l'assurance si sinistre lié) |
| Accepter | Envoyé → Accepté | Le client a donné son accord |
| Refuser | Envoyé → Refusé | Le client refuse le devis |
| Convertir en OR | Accepté → Converti | Crée un ordre de réparation avec toutes les lignes |
| Créer avenant | Tout état → Nouveau devis | Crée une copie comme supplément / avenant |
| Annuler | Tout état → Annulé | Annule le devis |

> **Attention lors de la conversion en OR :**
> - Le client ne doit pas être **bloqué**
> - Si le client est un gestionnaire de flotte avec approbation requise, le montant ne doit pas dépasser le seuil
> - L'encours du client + le montant du devis ne doivent pas dépasser le plafond crédit

#### Champs du formulaire

**En-tête :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Référence | Auto-générée (DEV/2026/0001) | Auto |
| Véhicule | Véhicule concerné | Oui |
| Client | Client destinataire | Oui |
| Facturer à | Adresse de facturation différente | Non |
| Sinistre | Sinistre assurance lié | Non |
| Date du devis | Date de création | Auto |
| Date de validité | Date d'expiration (configurable, défaut 30 jours) | Auto |
| Responsable | Utilisateur qui gère le devis | Auto |
| Km à l'entrée | Kilométrage relevé à la réception | Non |

**Onglet Lignes de devis :**

Chaque ligne représente une prestation ou pièce. Types disponibles :

| Type de ligne | Description | Champs spécifiques |
|---------------|-------------|-------------------|
| MO Carrosserie | Main d'œuvre carrosserie | Temps alloué (h), Taux horaire |
| MO Peinture | Main d'œuvre peinture | Temps alloué (h), Taux horaire |
| MO Mécanique | Main d'œuvre mécanique | Temps alloué (h), Taux horaire |
| Pièces | Pièces détachées | Quantité, Prix unitaire, Catégorie (OEM/aftermarket/occasion/échange) |
| Matière peinture | Produits de peinture | Quantité, Prix unitaire |
| Sous-traitance | Travaux sous-traités | Quantité, Prix unitaire |
| Consommable | Consommables atelier | Quantité, Prix unitaire |
| Divers | Autres frais | Quantité, Prix unitaire |

**Champs communs à toutes les lignes :**

| Champ | Description |
|-------|-------------|
| Description | Libellé de la prestation |
| Produit/Pièce | Produit Odoo lié (optionnel) |
| Remise (%) | Remise sur cette ligne |
| Total ligne | Calculé automatiquement |
| Code opération barème | Code Audatex/DAT/GT Motive |
| Source barème | Audatex, DAT, GT Motive, Manuel |
| Zone endommagée | Zone du véhicule concernée |
| Niveau de dommage | Léger, Moyen, Grave, Remplacement |

> **Astuce** : Quand vous sélectionnez un type de ligne MO et qu'un sinistre est lié, le taux horaire se remplit automatiquement avec le barème de l'assurance.

**Section Totaux (bas du formulaire) :**

| Indicateur | Description |
|------------|-------------|
| Total MO | Somme des lignes main d'œuvre |
| Total pièces | Somme des lignes pièces |
| Total sous-traitance | Somme des lignes sous-traitance |
| Total matière peinture | Somme des lignes peinture |
| Remise globale (%) | Taux de remise appliqué au total |
| Montant remise | Montant de la remise calculé |
| Total HT | Total hors taxes |
| TVA | Montant de la TVA (taux configurable) |
| **Total TTC** | **Total toutes taxes comprises** |
| Part assurance | Montant pris en charge par l'assurance (si sinistre) |
| Part franchise client | Montant de la franchise à la charge du client |

**Onglet Suppléments :**

Liste des avenants liés à ce devis (devis enfants). Un devis peut être marqué comme "Supplément" et lié à un devis parent.

**Onglet Notes :**

| Champ | Description |
|-------|-------------|
| Notes internes | Visibles uniquement en interne |
| Notes client | Imprimées sur le devis PDF |

#### Impression

Cliquez sur **Imprimer > Devis** pour générer le PDF. Le rapport inclut :
- Informations client et véhicule
- Lignes groupées par catégorie (MO, Pièces, Matière peinture, Sous-traitance, Divers)
- Totaux HT/TVA/TTC
- Zone de signature "Bon pour accord"
- Mention du sinistre si applicable

---

### 3.5. Ordres de réparation (OR)

**Accès** : Menu **Garage > Atelier > Ordres de réparation**

#### Workflow de l'OR (12 états)

```
Brouillon → Confirmé → [Attente pièces] → En cours
                                              ↓
                                     Cabine peinture → Remontage
                                              ↓
                                     QC demandé → QC validé → Prêt → Livré → Facturé
                                                                                ↓
                                                                            Annulé
```

#### Boutons d'action

| Bouton | Transition | Description |
|--------|-----------|-------------|
| Confirmer | Brouillon → Confirmé | Vérifie le stock, crée les commandes fournisseur si rupture |
| Démarrer travaux | Confirmé → En cours | Enregistre la date réelle de début, envoie un email au client |
| Cabine peinture | En cours → Cabine peinture | Le véhicule entre en cabine de peinture |
| Remontage | Cabine peinture → Remontage | Sortie de cabine, début du remontage |
| Demander QC | Remontage → QC demandé | Auto-crée une checklist si aucune n'existe |
| Valider QC | QC demandé → QC validé | Vérifie que tous les points de contrôle sont remplis |
| Prêt à livrer | QC validé → Prêt | Envoie une notification "Véhicule prêt" au client |
| Livrer | Prêt → Livré | Restitue le véhicule de courtoisie automatiquement, envoie un email de restitution |
| Facturer | Ouvre le wizard de facturation | Permet de choisir le scénario de facturation |
| Annuler | Tout état → Annulé | Annule l'OR |

#### Champs du formulaire

**En-tête :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Référence | Auto-générée (OR/2026/0001) | Auto |
| Véhicule | Véhicule en réparation | Oui |
| Client | Client propriétaire/conducteur | Oui |
| Facturer à | Si différent du client | Non |
| Sinistre | Sinistre lié | Non |
| Devis d'origine | Devis qui a généré cet OR | Auto |
| Priorité | Normal, Urgent, Très urgent | Non |
| Responsable | Utilisateur responsable | Auto |
| Localisation véhicule | Extérieur, Atelier, Cabine peinture, Sous-traitant, Livré | Non |

**Section Équipe (dans le formulaire) :**

| Champ | Description |
|-------|-------------|
| Chef d'atelier | Chef responsable de cet OR |
| Techniciens affectés | Liste des techniciens qui travaillent sur cet OR |

**Section Dates :**

| Champ | Description |
|-------|-------------|
| Début planifié / Fin planifiée | Dates prévues |
| Début réel / Fin réelle | Dates effectives |
| Durée estimée (jours) | Nombre de jours ouvrés estimés |
| Date restitution estimée | Date prévue de remise au client |
| Km à l'entrée / Km à la sortie | Kilométrage relevé |

**Onglet Lignes :**

Même structure que les lignes de devis, avec en plus :

| Champ supplémentaire | Description |
|----------------------|-------------|
| Technicien | Technicien affecté à cette ligne |
| Temps réel (h) | Heures réellement travaillées |
| Terminé | Case à cocher quand le travail est fini |
| Date fin | Date de complétion |
| Coût unitaire | Pour le calcul de marge |
| Pièces reçues | Automatique quand le stock est livré |

**Onglet Planning :**

Liste des créneaux planning liés : poste, technicien, dates, durée, statut.

**Onglet Carrosserie / Peinture / Mécanique :**

Listes des opérations détaillées par métier (voir sections 3.8, 3.9, 3.10).

**Onglet Sous-traitance :**

Liste des bons de sous-traitance liés.

**Onglet Courtoisie :**

Informations sur le véhicule de courtoisie prêté.

**Onglet Qualité :**

Checklists de contrôle qualité et résultats.

**Onglet Documents :**

Photos et documents liés à cet OR.

**Onglet Factures :**

Bouton "Facturer" et liste des factures émises pour cet OR.

**Onglet Notes :**

Notes internes et notes de restitution.

**Section Totaux (bas du formulaire) :**

| Indicateur | Description |
|------------|-------------|
| Heures allouées / Heures travaillées | Suivi du temps |
| Taux de productivité | Alloué / Travaillé (en %) |
| Total HT / TVA / Total TTC | Montants financiers |
| Coût total / Marge / Taux de marge | Indicateurs de rentabilité |

#### Smart buttons

- **Factures** : nombre et accès aux factures
- **Planning** : nombre de créneaux
- **QC** : nombre de checklists qualité
- **Documents** : nombre de photos/documents

#### Impression

**Imprimer > Ordre de réparation** génère un PDF avec :
- Informations client, véhicule, sinistre
- Toutes les lignes avec zones de dommage
- Heures allouées vs travaillées
- Totaux HT/TVA/TTC
- Liste des techniciens
- Notes de restitution
- Zone de signature

---

### 3.6. Planning

**Accès** : Menu **Garage > Atelier > Planning**

Le planning est visible en **kanban**, **calendrier**, **liste** et **formulaire**.

#### Vue Calendrier

Affichée par semaine, chaque créneau est coloré selon le poste de travail. Permet de visualiser rapidement la charge de l'atelier.

#### Créneaux planning

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Ordre de réparation | OR concerné | Oui |
| Poste de travail | Pont, cabine, banc... | Oui |
| Technicien | Technicien affecté | Non |
| Type d'opération | Carrosserie, Préparation peinture, Cabine peinture, Mécanique, Remontage, QC, Lavage | Non |
| Début / Fin | Horaires du créneau | Oui |
| Durée (h) | Calculée automatiquement | Auto |

**Statuts :** Planifié → En cours → Terminé (ou Annulé)

> **Contrainte** : Deux créneaux ne peuvent pas se chevaucher sur un même poste de travail (sauf si la capacité du poste > 1).

#### Filtres

- **Aujourd'hui** / **Cette semaine** : créneaux de la période
- **Planifié** / **En cours** : par statut
- **Regrouper par** : poste, technicien, statut, type d'opération, date

---

### 3.7. Postes de travail

**Accès** : Menu **Garage > Configuration > Postes de travail**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Nom | Nom du poste (ex: "Pont 1", "Cabine A") | Oui |
| Code | Code court | Non |
| Type de poste | Pont carrosserie, Pont mécanique, Banc de redressage, Cabine peinture, Zone préparation, Poste soudure, Diagnostic, Lavage, Général | Oui |
| Capacité | Nombre de véhicules simultanés | Non (défaut : 1) |
| Goulot d'étranglement | Poste à capacité limitée (prioritaire en planning) | Non |

---

### 3.8. Opérations carrosserie

**Accès** : Menu **Garage > Atelier > Carrosserie** (ou onglet dans l'OR)

Vue kanban groupée par statut ou vue liste.

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Description | Libellé de l'opération | Oui |
| Type d'opération | Redressage, Remplacement, Soudure, Masticage, Châssis, Vitrage, Garniture, PDR (débosselage sans peinture), Démontage, Remontage, Autre | Oui |
| Zone | Zone du véhicule (pare-chocs avant, capot, aile, porte...) | Non |
| Niveau de dommage | Léger, Moyen, Grave, Remplacement | Non |
| Temps alloué (h) | Heures prévues | Non |
| Temps réel (h) | Heures effectivement passées | Non |
| Carrossier | Technicien affecté | Non |
| Nécessite peinture | Si oui, crée automatiquement une opération peinture | Non |

**Statuts :** À faire → En cours → Terminé (ou Bloqué)

> **Véhicule électrique** : Si le véhicule est électrique/hybride, le technicien doit posséder l'habilitation VE pour démarrer l'opération.

---

### 3.9. Opérations peinture

**Accès** : Menu **Garage > Atelier > Peinture** (ou onglet dans l'OR)

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Description | Libellé de l'opération | Oui |
| Type d'opération | Apprêt, Ponçage, Couche de base, Vernis, Raccord, Panneau complet, Véhicule complet, Retouche, Polissage | Oui |
| Zone | Zone peinte | Non |
| Code peinture | Repris automatiquement du véhicule | Auto |
| Formule | Formule de teinte utilisée | Non |
| Système peinture | Repris automatiquement du véhicule | Auto |

**Section Cabine :**

| Champ | Description |
|-------|-------------|
| Créneau cabine début/fin | Horaires de cabine réservés |
| Température cabine (°C) | Conditions d'application |
| Hygrométrie (%) | Taux d'humidité |

**Onglet Consommation produits :**

| Champ | Description |
|-------|-------------|
| Produit | Produit peinture utilisé |
| Type | Base, Vernis, Durcisseur, Diluant, Apprêt, Mastic, Autre |
| Quantité | Quantité consommée |
| Unité | Unité de mesure (litre par défaut) |
| Coût unitaire | Prix au litre/kg |
| Coût total | Calculé automatiquement |

> **Stock** : Chaque consommation crée automatiquement un mouvement de stock sortant.

**Workflow peinture (7 états) :**

```
En attente → Préparation → Cabine → Séchage → Polissage → Terminé
                                                              ↓
                                                           Reprise → Retour en préparation
```

---

### 3.10. Opérations mécanique

**Accès** : Menu **Garage > Atelier > Mécanique** (ou onglet dans l'OR)

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Description | Libellé de l'opération | Oui |
| Catégorie | Entretien, Réparation, Diagnostic, Préparation CT, Géométrie, Climatisation, Électricité, Pneumatiques, Échappement, Autre | Oui |
| Type d'opération | Vidange, Filtres, Plaquettes, Disques, Embrayage, Distribution, Turbo, Injecteurs, Démarreur, Alternateur, Radiateur, etc. (26 options) | Non |

**Section Diagnostic** (visible si catégorie = Diagnostic) :

| Champ | Description |
|-------|-------------|
| Codes défaut OBD | Codes relevés (ex: P0300, P0171) |
| Codes effacés | Les codes ont été effacés |
| Résultat diagnostic | Analyse détaillée |

**Section Pneumatiques** (visible si catégorie = Pneumatiques) :

| Champ | Description |
|-------|-------------|
| Marque pneu | Fabricant |
| Dimensions | Ex: 205/55 R16 |
| Code DOT | Date de fabrication |
| Profondeur sculpture (mm) | Usure mesurée |
| Position | Avant gauche/droite, Arrière gauche/droite, Roue de secours |

**Section Entretien** (visible si catégorie = Entretien planifié) :

| Champ | Description |
|-------|-------------|
| Entretien planifié | Case à cocher |
| Point du plan | Lié au plan d'entretien du véhicule |
| Prochain entretien (km/date) | Planification du prochain passage |

**Statuts :** À faire → En cours → Terminé (ou Attente pièces)

---

### 3.11. Plans d'entretien

**Accès** : Menu **Garage > Atelier > Plans d'entretien**

Un plan d'entretien est associé à un véhicule et contient des points d'entretien (items) avec des intervalles de maintenance.

**Items du plan :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Opération | Nom de l'opération (ex: "Vidange moteur") | Oui |
| Intervalle (km) | Tous les X km (ex: 15 000 km) | Non |
| Intervalle (mois) | Tous les X mois (ex: 12 mois) | Non |
| Dernier entretien (km) | Km au dernier passage | Non |
| Dernier entretien (date) | Date du dernier passage | Non |
| Prochain (km) | Calculé : dernier + intervalle | Auto |
| Prochain (date) | Calculé : dernière date + intervalle mois | Auto |
| En retard | Vrai si la date prochaine est dépassée | Auto |

> **Tâche automatique** : Un cron vérifie chaque semaine les entretiens à venir dans les 30 jours et crée des alertes.

---

### 3.12. Techniciens

**Accès** : Menu **Garage > Atelier > Techniciens**

Le formulaire hérite du formulaire employé (hr.employee) et ajoute des champs spécifiques.

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Technicien atelier | Coché pour apparaître dans les listes | Oui |
| Spécialité | Carrossier, Peintre, Mécanicien, Électricien, Polyvalent | Non |
| Habilitation VE | Certifié pour les véhicules électriques | Non |
| Date habilitation VE | Date de certification | Non |
| Coût horaire interne (€/h) | Pour le calcul de marge | Non |
| Capacité journalière (h) | Nombre d'heures par jour (défaut : 8) | Non |

---

### 3.13. Pièces et stock

**Accès** : Menu **Garage > Pièces & Stock > Pièces**

La liste affiche uniquement les produits marqués comme "Pièce garage". Le formulaire hérite du formulaire produit standard Odoo et ajoute un onglet **Garage**.

**Onglet Garage :**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Pièce garage | Identifie le produit comme pièce auto | Oui |
| Catégorie pièce | OEM, Aftermarket, Occasion, Échange standard, Consommable, Peinture | Non |
| Référence OEM | Référence constructeur d'origine | Non |
| Référence TecDoc | Référence catalogue TecDoc | Non |
| Véhicules compatibles | Description des véhicules compatibles | Non |
| Pièce consignée | Pièce avec consigne (turbo, injecteur...) | Non |
| Montant consigne (€) | Montant de la consigne | Non |

**Catégories de produits disponibles :**
- Pièces OEM (constructeur)
- Pièces aftermarket (équipementier)
- Pièces occasion
- Échange standard
- Produits peinture
- Consommables atelier

**Filtres de recherche :**
- OEM, Aftermarket, Occasion, Consommable, Peinture, Consigne

> **Commandes fournisseur automatiques** : Quand un OR est confirmé et qu'une pièce est en rupture de stock, une commande fournisseur (Purchase Order) est automatiquement créée en brouillon, groupée par fournisseur.

---

### 3.14. Sous-traitance

**Accès** : Menu **Garage > Atelier > Sous-traitance**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Référence | Auto-générée (ST/2026/0001) | Auto |
| Ordre de réparation | OR lié | Oui |
| Sous-traitant | Partenaire marqué comme sous-traitant | Oui |
| Type de service | PDR, Vitrage, Sellerie, Électronique, Calibrage ADAS, Climatisation, Géométrie, Remorquage, Peinture, Autre | Oui |
| Description | Détail des travaux | Non |
| Coût estimé | Devis du sous-traitant | Non |
| Coût réel | Montant facturé | Non |
| Date d'envoi | Date d'envoi du véhicule/pièce | Non |
| Retour prévu | Date de retour attendue | Non |
| Retour réel | Date de retour effective | Non |
| En retard | Calculé si retour réel > retour prévu | Auto |
| Mode d'envoi | Véhicule entier, Pièce seule, Sur site | Non |
| Qualité validée | Le travail est conforme | Non |

**Workflow :** Brouillon → Envoyé → En cours → Terminé → Facturé (ou Annulé)

---

### 3.15. Véhicules de courtoisie

**Accès** : Menu **Garage > Réception > Véhicules de courtoisie**

#### Fiche véhicule de courtoisie

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Véhicule | Véhicule Odoo lié | Oui |
| Immatriculation | Reprise automatiquement du véhicule | Auto |
| État | Disponible, Prêté, En maintenance, Indisponible | Auto |
| Échéance assurance | Date d'expiration de l'assurance | Non |
| Échéance CT | Date d'expiration du contrôle technique | Non |
| Coût journalier interne | Coût pour le garage par jour | Non |
| Tarif facturable / jour | Prix facturé au client par jour | Non |
| Jours gratuits max | Nombre de jours offerts | Non (défaut : 0) |

**Smart button** : Nombre de prêts effectués.

#### Prêts de courtoisie

**Accès** : Menu **Garage > Réception > Prêts de courtoisie**

| Champ | Description |
|-------|-------------|
| Véhicule de courtoisie | Véhicule prêté |
| Ordre de réparation | OR justifiant le prêt |
| Client | Client emprunteur |

**Onglet Départ :**

| Champ | Description |
|-------|-------------|
| Date de prêt | Enregistrée à l'activation |
| Km départ | Kilométrage au départ |
| Niveau carburant | Plein, 3/4, 1/2, 1/4, Vide |
| État des lieux départ | Description de l'état du véhicule |
| Photos départ | Photos de l'état initial |
| Convention signée | Le client a signé la convention |

**Onglet Retour :**

| Champ | Description |
|-------|-------------|
| Date de retour | Enregistrée à la restitution |
| Km retour | Kilométrage au retour |
| Niveau carburant | Niveau à la restitution |
| État des lieux retour | Description de l'état |
| Photos retour | Photos de l'état au retour |
| Dommage constaté | Nouveau dommage identifié |
| Description dommage | Détail du dommage |

**Indicateurs financiers :**

| Indicateur | Calcul |
|------------|--------|
| Jours de prêt | Nombre de jours entre départ et retour |
| Jours facturables | Jours de prêt - Jours gratuits max |
| Montant facturable | Jours facturables × Tarif jour |

**Workflow :** Réservé → Actif → Restitué (ou Endommagé)

**Bouton "Restituer"** : Ouvre un wizard avec les champs de retour (km, carburant, état des lieux, dommage).

> **Note** : À la livraison d'un OR, si un véhicule de courtoisie est actif, il est automatiquement restitué.

---

### 3.16. Facturation

**Accès** : Menu **Garage > Facturation > Factures**

La liste affiche uniquement les factures garage (marquées `is_garage_invoice`).

#### Wizard de facturation

Accessible depuis un OR via le bouton **Facturer**. Le wizard propose 7 scénarios :

| Scénario | Description | Quand l'utiliser |
|----------|-------------|-----------------|
| **Client intégral** | Une seule facture au client pour la totalité | Client sans assurance |
| **Assurance + Franchise** | Deux factures : une à l'assurance, une franchise au client | Sinistre classique |
| **Assurance seule** | Une facture à l'assurance uniquement | Franchise à zéro |
| **Acompte** | Facture partielle d'un montant défini | Demande d'avance |
| **Facture partielle** | Facture des lignes terminées uniquement | Facturation progressive |
| **Courtoisie** | Facture des jours de courtoisie excédentaires | Véhicule de courtoisie au-delà des jours gratuits |
| **Différence assurance** | Facture au client de l'écart assurance | Montant remboursé < montant réel |

#### Champs spécifiques sur les factures garage

| Champ | Description |
|-------|-------------|
| OR garage | Ordre de réparation lié |
| Sinistre | Sinistre lié (si applicable) |
| Type facture garage | Client intégral, Assurance, Franchise, Acompte, Sous-traitance, Courtoisie, Garantie |
| Véhicule / Immatriculation | Repris de l'OR |

#### Rapport facture personnalisé

Le PDF de facture garage inclut :
- Bloc véhicule, OR, sinistre
- Récapitulatif par catégorie (MO carrosserie/peinture/mécanique, pièces, sous-traitance)
- Mention franchise si facture franchise
- Mention assurance si facture assurance
- Mention **autoliquidation TVA** si position fiscale intracommunautaire (Luxembourg)

---

### 3.17. Contrôle qualité

**Accès** : Menu **Garage > Atelier > Contrôle qualité**

#### Checklist qualité

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Ordre de réparation | OR concerné | Oui |
| Type de contrôle | Carrosserie, Peinture, Mécanique, Général | Oui |
| Contrôlé par | Utilisateur qui a fait le contrôle | Auto |
| Date du contrôle | Date de validation | Auto |
| Résultat global | Conforme, Partiellement conforme, Non conforme | Auto |

**Points de contrôle :**

| Champ | Description |
|-------|-------------|
| Point de contrôle | Nom du point vérifié |
| Type | Visuel, Fonctionnel, Mesure |
| Résultat | OK, NOK, N/A |
| Remarque | Commentaire si NOK |
| Photo | Photo de preuve |

> **Auto-création** : Quand vous cliquez "Demander QC" sur un OR, une checklist est créée automatiquement avec des items standards basés sur les types de travaux de l'OR.

**Résultat global :**
- **Conforme** (vert) : Tous les items sont OK ou N/A
- **Partiellement conforme** (orange) : Mélange de OK et NOK
- **Non conforme** (rouge) : Au moins un item NOK

#### Impression

**Imprimer > Contrôle Qualité** génère un PDF avec :
- Badge de résultat coloré
- Liste des points avec mise en évidence des NOK
- Statistiques OK/NOK/N/A
- Zones de signature (contrôleur + chef d'atelier)

---

### 3.18. Documents et photos

**Accès** : Menu **Garage > Réception > Documents / Photos**

| Champ | Description | Obligatoire |
|-------|-------------|:-----------:|
| Description | Titre du document | Non |
| Type | Photo avant, Photo pendant, Photo après, Photo dommage, Constat, Rapport expertise, Facture fournisseur, Rapport technique, Check-in courtoisie, Autre | Oui |
| Fichier | Le fichier uploadé | Oui |
| OR / Sinistre / Véhicule | Lien vers l'enregistrement parent | Non |
| Zone de dommage | Zone concernée (si photo dommage) | Non |
| Pris par | Utilisateur ayant pris la photo | Auto |
| Date | Date de capture | Auto |
| Visible sur le portail | Le client peut voir ce document | Non (défaut : Oui) |

> **Miniature** : Une miniature 128×128 est générée automatiquement pour les images.

---

### 3.19. Reporting

**Accès** : Menu **Garage > Reporting**

#### 3.19.1. Chiffre d'affaires

**Accès** : Menu **Garage > Reporting > Chiffre d'affaires**

Vue pivot/graphique du CA par activité. Basé sur les lignes des OR livrés ou facturés.

| Indicateur | Description |
|------------|-------------|
| CA HT | Chiffre d'affaires hors taxes |
| Coût | Coût des prestations |
| Marge | CA - Coût |
| Taux de marge (%) | Marge / CA |
| Nombre d'OR | Ordres de réparation |

**Dimensions d'analyse :**
- Type d'activité : Carrosserie, Peinture, Mécanique, Pièces, Sous-traitance
- Période : Mois, Année
- Client, Véhicule, État de l'OR

**Filtres :**
- Par type d'activité (carrosserie, peinture, mécanique, pièces, sous-traitance)
- Ce mois, Cette année

#### 3.19.2. Activité atelier

**Accès** : Menu **Garage > Reporting > Activité atelier**

Vue pivot/graphique des KPIs atelier.

| Indicateur | Description |
|------------|-------------|
| Nombre d'OR | Ordres de réparation dans la période |
| Heures allouées | Total des heures prévues |
| Heures travaillées | Total des heures réellement passées |
| Taux de productivité (%) | Heures allouées / Heures travaillées |
| Délai moyen (j) | Nombre moyen de jours entre début et livraison |
| CA HT | Chiffre d'affaires hors taxes |

**Dimensions :** Mois, Année

---

### 3.20. Portail client

Le portail client permet aux clients de suivre leurs dossiers en ligne via l'URL `/my`.

#### Pages disponibles

| Page | URL | Description |
|------|-----|-------------|
| Ordres de réparation | `/my/repair-orders` | Liste de tous les OR du client |
| Détail OR | `/my/repair-orders/{id}` | Détail d'un OR avec lignes, totaux, état |
| Documents OR | `/my/repair-orders/{id}/documents` | Photos et documents liés à l'OR |
| Devis | `/my/garage-quotations` | Liste des devis du client |
| Détail devis | `/my/garage-quotations/{id}` | Détail avec lignes et possibilité d'accepter/refuser |
| Factures | `/my/garage-invoices` | Liste des factures garage |
| Détail facture | `/my/garage-invoices/{id}` | Détail de la facture |

> **Accepter / Refuser un devis** : Le client peut accepter ou refuser un devis directement depuis le portail (uniquement si le devis est en état "Envoyé").

---

### 3.21. CarVertical

**Accès** : Bouton **CarVertical** sur la fiche véhicule, ou **Configuration > Cache CarVertical**

#### Recherche CarVertical

1. Ouvrez la fiche d'un véhicule
2. Cliquez sur le bouton **CarVertical** (visible si un VIN est renseigné)
3. Le wizard s'ouvre avec le VIN pré-rempli
4. Cliquez **Rechercher**
5. Les résultats s'affichent : marque, modèle, année, motorisation, historique kilométrique, dommages, rappels
6. Cliquez **Appliquer au véhicule** pour mettre à jour la fiche automatiquement

**Résultats disponibles :**
- Marque, Modèle, Année
- Type de carrosserie, Code moteur, Cylindrée, Puissance
- Carburant, Boîte de vitesses, Transmission
- Couleur
- Dernier kilométrage connu, Falsification détectée
- Nombre et détail des dommages
- Rappels constructeur
- Nombre d'immatriculations
- URL vers le rapport complet

**Cache :** Les résultats sont mis en cache pour éviter les appels API répétitifs (durée configurable).

**Recherche automatique :** Si activé dans la configuration, une recherche est lancée automatiquement à chaque saisie ou modification du VIN.

---

## 4. Scénarios pas à pas

### Scénario A : Un particulier vient pour une réparation mécanique simple

**Contexte** : M. Dupont arrive avec sa Volkswagen Golf pour un bruit de freins.

1. **Accueil** : Allez dans **Réception > Clients**, cherchez "Dupont"
   - Si le client n'existe pas, cliquez **Créer**, remplissez nom, téléphone, email, cochez "Client garage", type = Particulier
2. **Véhicule** : Allez dans **Réception > Véhicules**, cherchez la plaque
   - Si le véhicule n'existe pas, cliquez **Créer**, sélectionnez marque/modèle, immatriculation, VIN, relevez le kilométrage
3. **Devis** : Allez dans **Réception > Devis**, cliquez **Créer**
   - Sélectionnez le véhicule et le client
   - Ajoutez les lignes :
     - Type "MO Mécanique" : "Diagnostic freinage", 0,5h, taux horaire mécanique
     - Type "MO Mécanique" : "Remplacement plaquettes AV", 1h, taux horaire mécanique
     - Type "Pièces" : "Plaquettes de frein AV", qté 1, prix unitaire
   - Vérifiez les totaux HT/TVA/TTC
4. **Envoi** : Cliquez **Envoyer** → un email est envoyé au client avec le devis en pièce jointe
5. **Acceptation** : Quand le client accepte, cliquez **Accepter**
6. **Conversion** : Cliquez **Convertir en OR** → un OR est créé automatiquement avec les mêmes lignes
7. **Planification** : Dans l'OR, onglet Planning, ajoutez un créneau :
   - Poste : Pont mécanique 1
   - Technicien : [mécanicien disponible]
   - Dates début/fin
8. **Exécution** : Cliquez **Confirmer** puis **Démarrer travaux**
   - Le mécanicien pointe son temps dans l'onglet Lignes (colonne "Temps réel")
   - Il coche "Terminé" sur chaque ligne achevée
9. **Contrôle qualité** : Cliquez **Demander QC** → **Valider QC**
10. **Prêt** : Cliquez **Prêt à livrer** → le client reçoit un email "Votre véhicule est prêt"
11. **Facturation** : Cliquez **Facturer**, choisissez "Client intégral", cliquez **Créer les factures**
12. **Restitution** : Cliquez **Livrer**, relevez le km de sortie

---

### Scénario B : Un client arrive après un accident avec sinistre assurance

**Contexte** : Mme Martin arrive avec sa Peugeot 308 accidentée. Elle est assurée chez AXA.

1. **Accueil** : Enregistrez ou retrouvez le client et le véhicule (voir Scénario A étapes 1-2)
2. **Sinistre** : Allez dans **Assurances > Sinistres**, cliquez **Créer**
   - Véhicule : la Peugeot 308
   - Client : Mme Martin
   - Compagnie d'assurance : AXA
   - Date du sinistre, Type : Collision
   - Remplissez les circonstances, tiers impliqué, PV de police si applicable
   - Cliquez **Déclarer**
3. **Expertise** : Cliquez **Demander expertise**
   - Sélectionnez l'expert assigné par AXA
   - Renseignez la date prévue
   - Le système crée une activité de suivi
4. **Photos** : Allez dans **Réception > Documents / Photos**, ajoutez les photos des dommages en les liant au sinistre et au véhicule (type = "Photo dommage", sélectionnez la zone)
5. **Devis** : Créez un devis en sélectionnant le sinistre
   - Les taux horaires se remplissent automatiquement avec les barèmes AXA
   - Ajoutez toutes les lignes (MO carrosserie, peinture, pièces, sous-traitance...)
   - Vérifiez les montants : part assurance et franchise sont calculés automatiquement
   - Cliquez **Envoyer** (l'email est aussi envoyé en copie à l'adresse sinistres d'AXA)
6. **Expertise réalisée** : Quand l'expert a validé, retournez au sinistre
   - Cliquez **Expertise réalisée**
   - Renseignez le montant approuvé et uploadez le rapport
   - Cliquez **Approuver**
7. **Conversion et travaux** : Acceptez le devis, convertissez en OR
   - Sur le sinistre, cliquez **Démarrer travaux**
8. **Opérations** : Créez les opérations carrosserie, attendez la peinture, etc.
9. **Facturation split** : Cliquez **Facturer** sur l'OR
   - Choisissez "Assurance + Franchise"
   - Le wizard crée 2 factures : une pour AXA (montant - franchise), une pour Mme Martin (franchise)
10. **Suivi** : Le sinistre passe automatiquement en "Facturé" puis "Payé" quand les paiements sont enregistrés

---

### Scénario C : Gestion d'un sinistre grêle sur 10 véhicules

**Contexte** : Un orage de grêle a touché le parking d'une entreprise cliente. 10 véhicules sont endommagés.

1. **Préparation** : Pour chaque véhicule, créez un sinistre (type = Grêle) avec la même compagnie d'assurance
2. **Photos** : Photographiez chaque véhicule (photos type "Photo dommage") et liez-les au sinistre correspondant
3. **Expertise groupée** : Demandez l'expertise pour chaque sinistre. L'expert viendra évaluer tous les véhicules en une fois
4. **Devis** : Pour chaque véhicule, créez un devis lié au sinistre
   - Lignes typiques grêle : MO carrosserie (PDR/débosselage), éventuellement remplacement de pièces
   - Utilisez les taux horaires de l'assurance
5. **Planification** : Une fois les devis approuvés et convertis en OR, planifiez les passages en atelier
   - Utilisez la vue calendrier pour optimiser la charge des postes
   - Le PDR (débosselage sans peinture) ne nécessite pas de cabine
6. **Traitement en série** : Les techniciens traitent les véhicules un par un ou en parallèle selon les postes disponibles
7. **Facturation** : Facturez chaque OR individuellement (scénario "Assurance + Franchise" ou "Assurance seule" selon la franchise)

> **Astuce** : Utilisez les filtres "Grêle" et le regroupement par assurance dans la vue sinistres pour suivre l'ensemble du lot.

---

### Scénario D : Facturation split assurance + franchise

**Contexte** : L'OR de Mme Martin est terminé. Le sinistre AXA a une franchise de 250 €. Le total TTC est de 3 200 €.

1. Ouvrez l'OR et cliquez **Facturer**
2. Sélectionnez le scénario **"Assurance + Franchise"**
3. Le wizard affiche :
   - Client : Mme Martin
   - Assurance : AXA (partenaire de facturation)
   - Montant total HT : 2 644,63 €
   - Franchise : 250 €
4. Cliquez **Créer les factures**
5. Deux factures sont créées :
   - **Facture assurance** (AXA) : 2 950 € TTC (total - franchise)
   - **Facture franchise** (Mme Martin) : 250 € TTC
6. Les deux factures sont liées à l'OR et au sinistre
7. Le sinistre passe en état "Facturé"
8. Quand les deux paiements sont enregistrés, le sinistre passe automatiquement en "Payé"

---

### Scénario E : Véhicule de courtoisie — attribution et restitution

**Contexte** : M. Dupont a besoin d'un véhicule pendant la réparation de sa Golf (3 jours estimés).

1. **Vérifier la disponibilité** : Allez dans **Réception > Véhicules de courtoisie**
   - Filtrez par état "Disponible"
   - Choisissez un véhicule adapté
2. **Créer le prêt** : Allez dans **Réception > Prêts de courtoisie**, cliquez **Créer**
   - Sélectionnez le véhicule de courtoisie
   - Sélectionnez le client et l'OR
3. **Activation** : Cliquez **Activer le prêt**
   - Renseignez le km départ, le niveau de carburant
   - Décrivez l'état des lieux départ
   - Ajoutez les photos de l'état du véhicule
   - Faites signer la convention
   - Le véhicule passe en état "Prêté"
4. **Restitution** : Quand le client revient, cliquez **Restituer**
   - Le wizard s'ouvre :
     - Saisissez le km retour
     - Sélectionnez le niveau de carburant
     - Décrivez l'état des lieux retour
     - Indiquez si un dommage est constaté
   - Cliquez **Confirmer la restitution**
   - Le véhicule repasse en "Disponible"
5. **Facturation** (si jours excédentaires) :
   - Si le prêt a duré plus que les jours gratuits, utilisez le scénario de facturation "Courtoisie" dans le wizard de facturation de l'OR

> **Note** : À la livraison de l'OR (bouton "Livrer"), si un prêt de courtoisie est encore actif, il est automatiquement restitué.

---

### Scénario F : Supplément en cours de réparation

**Contexte** : En cours de réparation, le carrossier découvre un longeron endommagé non visible lors du chiffrage initial.

1. **Depuis le sinistre** : Ouvrez le sinistre lié à l'OR
2. Cliquez **Demander supplément**
3. Le wizard s'ouvre :
   - Description : "Longeron gauche déformé — non visible avant démontage"
   - Montant demandé : 850 €
   - Justification : expliquez en détail avec photos
4. Cliquez **Confirmer**
   - Un supplément est créé en état "Envoyé"
   - Le sinistre passe en état "Supplément demandé"
5. **Côté devis** : Créez un avenant au devis original (bouton "Créer avenant" sur le devis)
   - Ajoutez les lignes supplémentaires
   - Envoyez l'avenant à l'assurance
6. **Approbation** : Quand l'expert approuve le supplément :
   - Ouvrez le supplément, cliquez "Approuver"
   - Renseignez le montant approuvé
   - Le sinistre passe en "Supplément approuvé"
7. Les travaux peuvent continuer

---

### Scénario G : Client mauvais payeur — blocage et déblocage

**Contexte** : M. Durand a plusieurs factures impayées. Vous souhaitez bloquer son compte.

**Blocage :**

1. Ouvrez la fiche client de M. Durand (**Réception > Clients**)
2. Dans l'onglet Garage, cochez **Bloqué (garage)**
3. Renseignez la raison : "3 factures impayées — total 4 500 € — relances sans réponse"
4. Enregistrez

**Conséquence :** Si quelqu'un essaie de convertir un devis en OR pour M. Durand, le système bloquera avec un message d'erreur.

**Déblocage :**

1. Quand la situation est régularisée, ouvrez la fiche client
2. Décochez **Bloqué (garage)**
3. Videz la raison de blocage
4. Enregistrez

> **Plafond crédit** : Vous pouvez aussi définir un plafond de crédit (champ "Plafond crédit garage") qui empêchera automatiquement la conversion de devis en OR si l'encours dépasse le plafond.

---

### Scénario H : Gestion d'une flotte entreprise

**Contexte** : La société "TransLux SA" gère 50 véhicules et veut que son gestionnaire de flotte valide les réparations au-delà de 500 €.

1. **Configuration du client** :
   - Ouvrez la fiche de TransLux SA
   - Type de client : **Gestionnaire de flotte**
   - Onglet Flotte :
     - Cochez **Approbation flotte requise**
     - Seuil d'approbation : 500 €
     - Ajoutez le gestionnaire de flotte comme contact
2. **Ajout des conducteurs** :
   - Ajoutez les conducteurs dans la section "Conducteurs de la flotte"
   - Chaque conducteur est lié en tant que "conducteur" sur son véhicule dans Odoo Fleet
3. **Flux quotidien** :
   - Un conducteur amène son véhicule → Créez le devis au nom de TransLux SA
   - Si le devis dépasse 500 € HT, la conversion en OR sera bloquée avec un message demandant l'approbation du gestionnaire
   - Contactez le gestionnaire, obtenez l'accord, puis convertissez
4. **Facturation** : Toutes les factures sont au nom de TransLux SA
5. **Suivi** : Le gestionnaire peut utiliser le portail client pour suivre tous les OR de sa flotte

> **Grille tarifaire** : Vous pouvez appliquer la grille "Flotte" sur la fiche client pour des tarifs préférentiels.

---

## 5. Configuration et paramétrage

### 5.1. Paramètres Garage

**Accès** : Menu **Garage > Configuration > Paramètres**

#### Section Taux horaires

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| Taux horaire carrosserie (€/h) | Taux par défaut pour la MO carrosserie | 55,00 |
| Taux horaire peinture (€/h) | Taux par défaut pour la MO peinture | 55,00 |
| Taux horaire mécanique (€/h) | Taux par défaut pour la MO mécanique | 60,00 |

> Ces taux sont utilisés quand aucun barème assurance n'est applicable. Ils sont modifiables à tout moment.

#### Section Facturation

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| Taux TVA par défaut (%) | TVA appliquée aux devis et OR | 21,0 |
| Validité devis (jours) | Nombre de jours de validité par défaut | 30 |

#### Section CarVertical

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| Clé API | Clé d'accès à l'API CarVertical | (vide) |
| Recherche automatique | Recherche auto à la saisie du VIN | Non |
| Durée cache (jours) | Durée de validité du cache des résultats | 30 |

### 5.2. Compagnies d'assurance et barèmes

**Accès** : Menu **Garage > Assurances > Compagnies**

Pour chaque compagnie, configurez :
- Les taux horaires agréés (carrosserie, peinture, mécanique)
- Le coefficient pièces
- Le taux matière peinture
- Les conditions (aftermarket autorisé, occasion autorisée, âge max)
- Les conditions de paiement

### 5.3. Postes de travail

**Accès** : Menu **Garage > Configuration > Postes de travail**

Créez chaque poste physique de votre atelier :
- Donnez-lui un nom clair (ex: "Pont 1 — Carrosserie", "Cabine A")
- Choisissez le type
- Définissez la capacité (généralement 1)
- Cochez "Goulot d'étranglement" pour les postes critiques (cabine de peinture...)

### 5.4. Systèmes de peinture

**Accès** : Menu **Garage > Configuration > Systèmes de peinture**

Enregistrez les fabricants de peinture que vous utilisez (Standox, Sikkens, PPG, Cromax...) avec leur fournisseur Odoo.

### 5.5. Formules peinture

**Accès** : Menu **Garage > Configuration > Formules peinture** (ou onglet "Formules" dans la fiche véhicule)

Les formules sont associées à un véhicule et à un système de peinture. Elles permettent de retrouver rapidement la bonne teinte pour un véhicule déjà traité.

### 5.6. Modèles d'email

Le module utilise 5 modèles d'email automatiques :

| Modèle | Déclenchement | Contenu |
|--------|---------------|---------|
| Devis envoyé | Envoi du devis | Référence, montant, validité |
| Travaux en cours | Démarrage de l'OR | Plaque, date estimée de restitution |
| Véhicule prêt | OR en état "Prêt" | Plaque, invitation à prendre RDV |
| Véhicule restitué | Livraison de l'OR | Confirmation de restitution |
| VEI (perte totale) | Sinistre classé VEI | Information au client |

**Pour personnaliser les emails :**
1. Allez dans **Configuration > Technique > Email > Modèles**
2. Cherchez le modèle (ex: "Garage - Devis envoyé")
3. Modifiez le sujet et le corps du message
4. Utilisez les variables Jinja2 : `{{ object.name }}`, `{{ object.vehicle_id.license_plate }}`, etc.

### 5.7. Tâches automatiques (Crons)

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| Relance expertise | Quotidienne | Relance les sinistres en attente d'expertise depuis plus de 5 jours |
| Alertes CT | Hebdomadaire | Signale les véhicules dont le CT expire dans les 30 jours |
| Alertes entretien | Hebdomadaire | Signale les entretiens à venir dans les 30 jours |
| Véhicule non récupéré | Quotidienne | Signale les OR en état "Prêt" depuis plus de 7 jours |

**Pour activer/désactiver un cron :**
1. Allez dans **Configuration > Technique > Automatisation > Actions planifiées**
2. Cherchez le cron (préfixé "Garage —")
3. Cochez/décochez **Actif**
4. Vous pouvez aussi modifier l'intervalle d'exécution

### 5.8. Position fiscale Luxembourg

Le module inclut une position fiscale **"Intracommunautaire — Luxembourg"** qui s'applique automatiquement aux clients luxembourgeois assujettis à la TVA. Elle ajoute la mention d'autoliquidation (art. 44 CTVA) sur les factures.

### 5.9. Séquences

Les références sont générées automatiquement :

| Document | Format | Exemple |
|----------|--------|---------|
| Véhicule | VEH/AAAA/XXXXX | VEH/2026/00001 |
| Sinistre | SIN/AAAA/XXXX | SIN/2026/0001 |
| Devis | DEV/AAAA/XXXX | DEV/2026/0001 |
| Ordre de réparation | OR/AAAA/XXXX | OR/2026/0001 |
| Sous-traitance | ST/AAAA/XXXX | ST/2026/0001 |

---

## 6. FAQ et dépannage

### Q : Le module Garage ne s'affiche pas dans le menu

**Causes possibles :**
- Le module n'est pas installé → Allez dans **Applications**, cherchez "Garage Pro", cliquez **Installer**
- Vous n'avez pas les droits → Demandez à l'administrateur de vous affecter un groupe Garage (voir section 2.4)

### Q : Je ne vois pas le menu "Assurances"

Le menu Assurances est visible par tous les groupes Garage (y compris Réceptionniste). Vérifiez que :
- Votre utilisateur a bien un groupe Garage assigné
- Le module est bien installé et à jour (`-u garage_pro`)

### Q : Le devis ne se convertit pas en OR

**Causes possibles :**
- Le devis n'est pas en état "Accepté" → Il faut d'abord l'envoyer puis l'accepter
- Le client est bloqué → Débloquez-le dans sa fiche (onglet Garage, décochez "Bloqué")
- Plafond crédit dépassé → L'encours + le montant du devis dépasse le plafond. Régularisez les factures impayées ou augmentez le plafond
- Approbation flotte requise → Le montant dépasse le seuil du gestionnaire de flotte. Obtenez l'approbation avant de convertir

### Q : La facture assurance n'est pas générée

Vérifiez que :
- L'OR est lié à un sinistre (champ "Sinistre" renseigné)
- Le sinistre est lié à une compagnie d'assurance avec un partenaire Odoo valide
- Vous avez choisi le scénario "Assurance + Franchise" ou "Assurance seule" dans le wizard de facturation

### Q : Le taux horaire ne se remplit pas automatiquement

Le taux horaire se remplit automatiquement uniquement si :
- Le devis est lié à un sinistre
- Le sinistre est lié à une compagnie d'assurance
- La compagnie a des taux horaires configurés (onglet Barèmes)

Sinon, le taux par défaut de la configuration est utilisé (Configuration > Garage > Taux horaires).

### Q : Je ne peux pas démarrer une opération sur un véhicule électrique

Le technicien doit posséder l'**habilitation véhicules électriques** (case cochée dans sa fiche technicien). Sans cette habilitation, le système bloque le démarrage des opérations carrosserie, peinture et mécanique sur les véhicules électriques ou hybrides.

### Q : La commande fournisseur automatique ne se crée pas

Vérifiez que :
- Le produit (pièce) a un fournisseur défini (onglet "Achat" du produit)
- Le module `purchase_stock` est installé
- Le type de picking "Réception" existe dans le stock

Si le produit n'a pas de fournisseur, une notification d'activité est créée sur l'OR pour vous alerter.

### Q : Le contrôle qualité n'est pas généré automatiquement

La checklist QC est auto-créée quand vous cliquez **Demander QC** sur un OR. Si aucune checklist n'existe à ce moment, une checklist "Général" est créée avec des items standards basés sur les types de travaux de l'OR.

### Q : Comment modifier la TVA appliquée ?

Allez dans **Garage > Configuration > Paramètres**, section **Facturation**, modifiez le champ "Taux TVA par défaut". La modification s'applique aux nouveaux devis et OR. Les documents existants conservent l'ancien taux.

### Q : Comment anonymiser un client (RGPD) ?

1. Vous devez être **Gérant**
2. Ouvrez la fiche client
3. Cliquez **Anonymiser (RGPD)** en haut
4. Confirmez l'action

> **Attention** : Cette action est **irréversible**. Toutes les données personnelles (nom, adresse, téléphone, email) seront remplacées par des valeurs anonymes. Les OR en cours doivent être terminés avant l'anonymisation.

### Q : Le portail client ne montre rien

Vérifiez que :
- Le client a un accès portail activé (Configuration > Utilisateurs > onglet Portail)
- Le client a bien des devis/OR/factures associés
- Les documents sont marqués "Visible sur le portail" (champ `is_visible_portal`)

### Q : Comment voir le CA par type d'activité ?

Allez dans **Garage > Reporting > Chiffre d'affaires**. Utilisez la vue **Pivot** et mettez "Type d'activité" en ligne, "Mois" en colonne, et "CA HT" en valeur. Vous pouvez aussi passer en vue **Graphique** pour une représentation visuelle.

### Q : L'email de notification n'est pas envoyé

Vérifiez que :
- Le serveur de mail sortant est configuré dans Odoo (Configuration > Technique > Serveurs de mail sortant)
- Le client a une adresse email renseignée
- Le modèle d'email n'a pas été désactivé ou supprimé

### Q : Comment fonctionne la recherche CarVertical ?

1. Configurez d'abord votre clé API dans **Configuration > Paramètres > section CarVertical**
2. La recherche peut être lancée manuellement (bouton sur la fiche véhicule) ou automatiquement (si "Recherche auto" est activé)
3. Les résultats sont mis en cache pour la durée configurée
4. Sans clé API valide, la recherche échouera avec un message d'erreur

---

*Document généré le 2026-03-26 — Garage Pro v17.0.1.0.0*
