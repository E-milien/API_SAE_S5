# Sensor Monitoring API

Une API Flask pour surveiller et analyser les données des capteurs environnementaux stockées dans InfluxDB.

## Configuration

L'API utilise les technologies suivantes :
- Flask
- InfluxDB Client
- Python DateTime

### Variables d'environnement
L'API se connecte à InfluxDB avec les paramètres suivants :
```python
url="http://10.103.1.44:5003"
org="DomoCorp"
```

## Seuils de confort

L'API utilise les seuils suivants pour détecter l'inconfort :

| Mesure | Seuil |
|--------|--------|
| CO2 | > 1000 ppm |
| Température | 20°C - 26°C |
| Humidité | 30% - 60% |
| Bruit | > 50 dB |
| Fumée | > 0 |

## Types de capteurs surveillés

- Température de l'air (air_temperature)
- Niveau de CO2 (co2_level)
- Point de rosée (dew_point)
- Humidité (humidity)
- Composés organiques volatils (volatile_organic_compound_level)
- Luminosité (illuminance)
- UV (ultraviolet)
- Niveau sonore (loudness)
- Densité de fumée (smoke_density)

## Endpoints

### GET /sensors
Récupère tous les capteurs disponibles.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
{
    "sensor_id": {
        "measurement": "string",
        "domain": "string",
        "friendly_name_str": "string",
        "room": "string"
    }
}
```

### GET /rooms
Liste toutes les pièces disponibles.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
["room1", "room2", "room3"]
```

### GET /getData/{sensor_id}
Récupère les données d'un capteur spécifique.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')
- `measure` (optionnel) : Type de mesure (défaut : '%', peut être 'binary')

**Réponse** :
```json
{
    "x": [timestamps],
    "y": [values],
    "measurement": "string",
    "discomfort": {
        "status": boolean,
        "causes": ["string"]
    }
}
```

### GET /getSensorByType/{room}
Récupère les données de tous les capteurs d'une pièce, organisées par type.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
{
    "sensor_type": {
        "x": [timestamps],
        "y": [values]
    }
}
```

### GET /getSensors/{room}
Liste tous les capteurs d'une pièce spécifique.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
["sensor_id1", "sensor_id2"]
```

## Gestion des erreurs

L'API renvoie des codes d'erreur HTTP appropriés :
- 404 : Données non trouvées
- 500 : Erreur serveur

Chaque erreur inclut un message explicatif :
```json
{
    "error": "Description de l'erreur"
}
```

## Exemple d'utilisation

```python
# Récupérer les données de température d'une pièce sur les dernières 24h
GET /getData/bedroom_temperature?range=-24h&measure=temperature

# Lister tous les capteurs d'une pièce
GET /getSensors/bedroom
```

## Note sur l'agrégation des données

- Les données binaires sont agrégées toutes les 10 minutes avec la dernière valeur
- Les autres mesures sont agrégées toutes les minutes avec la moyenne
- Pour la détection d'inconfort, seule la dernière heure est analysée
