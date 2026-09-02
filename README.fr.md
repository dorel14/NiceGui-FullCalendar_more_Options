# Exemple de NiceGui FullCalendar

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/dorel14/NiceGui-FullCalendar_more_Options/blob/master/README.md)
[![fr](https://img.shields.io/badge/lang-fr-green.svg)](https://github.com/dorel14/NiceGui-FullCalendar_more_Options/blob/master/README.fr.md)

**Cet exemple est conçu pour NiceGui avec les plugins FullCalendar non premium activés.**

## Plugins Utilisés

- **@fullcalendar/daygrid** : Offre des vues Mois et DayGrid : `dayGridYear`, `dayGridMonth`, `dayGridWeek`, `dayGridDay`, `dayGrid` (générique)
- **@fullcalendar/timegrid** : Offre des vues TimeGrid : `timeGridWeek`, `timeGridDay`, `timeGrid` (générique)
- **@fullcalendar/list** : Offre des vues Listes : `listYear`, `listMonth`, `listWeek`, `listDay`, `list` (générique)
- **@fullcalendar/multimonth** : Offre des vues Multi-Mois : `multiMonthYear`, `multiMonth` (générique)
- **@fullcalendar/icalendar** : Pour charger des événements à partir d'un flux iCalendar
- **@fullcalendar/rrule** : Pour la gestion des évènements récurrents via rrule

## Fonctionnalités

- **Formulaire de Création d'Événements** : Un formulaire pour créer des événements.
- **Gestion des Clics sur les Dates et les Événements** : Un peu de code pour gérer les clics sur les dates et les événements.

## Instructions

1. Clonez ce dépôt.

## Exemple de Code

Un exemple de code pour la création des événements est présent dans le fichier `main.py`.

## Récupération dynamique des événements

Au lieu de charger tous les événements à l'initialisation, le calendrier peut demander les événements à la demande (ex: par mois/semaine) via une callback Python. Pratique pour les gros volumes de données.

Voir l'exemple fonctionnel dans [`basic_main.py`](basic_main.py).

> Le mécanisme de fetch est implémenté dans [`fullcalendar.py`](fullcalendar.py) et [`fullcalendar.js`](fullcalendar.js) — assurez-vous que ces fichiers se trouvent dans le même dossier que votre script.

### Mise en route rapide

1. Dans le dictionnaire `options`, mettez `"events": lambda *a, **k: None`.
2. Passez un callback `on_fetch_events` à `FullCalendar`.
3. À l'intérieur du callback, construisez la liste des événements et appelez `info.response(events_list)`.

```python
from fullcalendar import FullCalendar as fullcalendar

options = {
    "initialView": "dayGridMonth",
    "events": lambda *a, **k: None,  # active le mode fetch
}

def on_fetch(info):
    # info.start / info.end       -> chaines ISO des bornes visibles
    # info.start_value / info.end_value -> epoch ms (pratique pour les requêtes DB)
    events = load_events_from_database(info.start, info.end)
    info.response(events)   # renvoie la liste au calendrier

fullcalendar(options, on_fetch_events=on_fetch)
```

### Ce que reçoit le callback

`FetchInfoArguments` expose :

| attribut         | type | description                                         |
|------------------|------|-----------------------------------------------------|
| `start`          | `str` | chaine ISO de la borne de début (incluse).          |
| `end`            | `str` | chaine ISO de la borne de fin (exclue).             |
| `start_value`    | `int` | borne de début en epoch millisecondes (requêtes DB).|
| `end_value`      | `int` | borne de fin en epoch millisecondes.                |
| `time_zone`      | `str` | le paramètre timeZone du calendrier.                |
| `request_id`     | `int` | id interne servant à corréler la réponse.           |

> FullCalendar appelle `on_fetch_events` automatiquement à chaque navigation dans le calendrier. Seuls les événements intersectant la plage demandée sont renvoyés.

### Gestion des erreurs

Appelez `info.failure("message")` au lieu de `info.response(...)` pour signaler une erreur à FullCalendar (ex: timeout de base de données).

## Captures d'Écran

![Ajout Événement](./screenshots/add-event.png)
![Vue Semaine](./screenshots/weekview.png)
![Vue Multi-Mois + Calendrier iCal](./screenshots/multimonth+ical.png)

## Contributions

Les contributions sont les bienvenues ! Veuillez soumettre une pull request ou ouvrir une issue pour discuter des changements que vous souhaitez apporter.
