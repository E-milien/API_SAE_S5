# Sensor Monitoring API

Une API Flask pour surveiller et analyser les données des capteurs environnementaux stockées dans InfluxDB.

## Lancement du server

```shell 
flask --app main run --host=0.0.0.0
```

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
- `range` (optionnel) : Plage de temps (défaut 30 jours : '-30d')

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
- `range` (optionnel) : Plage de temps (défaut 30 jours : '-30d')

**Réponse** :
```json
["d251", "d351"...]
```

### GET /getData/{sensor_id}
Récupère les données d'un capteur spécifique.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut 30 jours : '-30d')
- `measure` (optionnel) : Type de mesure :
    - '%' (défault)
    - 'binary'
    - 'ppm'
    - '°C'
    - 'lx'
    - 'dBA'
    - 'UV%20index' (UV index)
    - '%C2%B5g%2Fm%C2%B3' (µg/m³)

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
- `range` (optionnel) : Plage de temps (défaut 30 jours : '-30d')

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
- `range` (optionnel) : Plage de temps (défaut 30 jours : '-30d')

**Réponse** :
```json
["d351_1_multisensor_humidity", "d251_1_co2_carbon_dioxide_co2_level"]
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
GET /getData/d251?range=-24h&measure=°C

# Lister tous les capteurs d'une pièce
GET /getSensors/d351_1_multisensor_humidity
```
