# Génération de reporting à partir du grand livre

Ce projet fournit un petit outil Python qui applique un **mapping de comptes** à un
**grand livre comptable** exporté en CSV afin de produire un reporting synthétique
de vos chiffres.

## Structure du dépôt

```
gl_reporting/        # Cœur de la librairie (lecture du grand livre, mapping, reporting)
data/                # Jeux de données d'exemple
README.md            # Ce fichier
```

## Installation et exécution

Le projet ne dépend que de la bibliothèque standard de Python 3.10+. Pour tester
rapidement, créez un environnement virtuel puis lancez la commande suivante :

```bash
python -m gl_reporting.report \
    --ledger data/sample_ledger.csv \
    --mapping data/sample_mapping.csv
```

La commande affiche un tableau récapitulatif directement dans le terminal. Vous
pouvez également générer des fichiers CSV :

```bash
python -m gl_reporting.report \
    --ledger data/sample_ledger.csv \
    --mapping data/sample_mapping.csv \
    --output reporting.csv \
    --details details.csv
```

* `reporting.csv` contiendra un tableau synthétique (catégorie / montant).
* `details.csv` contiendra le détail de chaque écriture et la règle appliquée.

## Préparer vos propres fichiers

1. **Grand livre** : exportez-le en CSV avec au minimum les colonnes `account`,
   `debit` et `credit`. Les colonnes supplémentaires comme `date`, `journal` ou
   `libellé` sont automatiquement reconnues.
2. **Mapping** : créez un fichier CSV avec au moins deux colonnes :
   * `pattern` — motif au format "glob" (`70*`, `401??`, `6?32*`, ...),
   * `category` — nom de la ligne de reporting.

   Colonnes optionnelles :
   * `label` — description libre,
   * `sign` — `1` ou `-1` pour inverser le signe (utile pour les comptes de produits).

Le moteur applique toujours la règle la plus spécifique (celle qui contient le
moins de jokers). Les écritures non couvertes sont regroupées dans la catégorie
« Non affecté » (personnalisable via `--default-category`).

## Tests

Les tests unitaires utilisent `pytest` :

```bash
pytest
```

## Aller plus loin

Le code source (`gl_reporting/report.py`) peut facilement être intégré dans un
pipeline plus large (ETL, notebook, etc.) pour automatiser la production d'un
reporting périodique.
