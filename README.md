# Sensor Monitoring API SAE 5 

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

### GET /api/sensors
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

### GET /api/rooms
Liste toutes les pièces disponibles.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
[
    {
        "name": "d251"
    },
    {
        "name": "d351"
    }
]
```

### GET /api/sensor/{sensor_id}
Récupère les données d'un capteur spécifique.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
{
    "measurement": "string",
    "discomfort": {
        "status": boolean,
        "causes": "string"
    },
    "x": [timestamps],
    "y": [values]
}
```

### GET /api/room/{room}/sensors
Récupère les données de tous les capteurs d'une pièce, organisées par type.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
{
    "sensor_type": {
        "x": [timestamps],
        "y": [values],
        "discomfort": {
            "status": boolean,
            "causes": "string"
        }
    }
}
```

### GET /api/room/{room}/sensor-list
Liste tous les capteurs d'une pièce spécifique.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-30d')

**Réponse** :
```json
[
    "d351_1_multisensor_humidity",
    "d251_1_co2_carbon_dioxide_co2_level"
]
```

### GET /api/room/{room}/occupancy
Vérifie si une pièce est occupée.

**Paramètres** :
- `range` (optionnel) : Plage de temps (défaut : '-7d')

**Réponse** :
```json
{
    "isOccuped": boolean
}
```

## Gestion des erreurs

L'API renvoie des codes d'erreur HTTP appropriés :
- 200 : Succès
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
# Récupérer les données d'un capteur sur les dernières 24h
GET /api/sensor/d251_1_multisensor_temperature?range=-24h

# Lister tous les capteurs d'une pièce
GET /api/room/d251/sensor-list

# Vérifier l'occupation d'une pièce
GET /api/room/d251/occupancy
```

## Note sur l'agrégation des données

- Les données de capteurs individuels sont agrégées toutes les 10 minutes
- Les données par type de capteur sont agrégées toutes les 60 minutes
- Pour la détection d'occupation, les données sont agrégées toutes les minutes
- Pour la détection d'inconfort, seule la dernière heure est analysée