import yaml
from yaml.loader import SafeLoader
import os

def charger_config(chemin="config.yaml"):
    try:
        with open(chemin) as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier de configuration {chemin} est introuvable.")
    except yaml.YAMLError as e:
        raise ValueError(f"Erreur de format dans {chemin} : {str(e)}")


def sauvegarder_config(config, chemin="config.yaml"):
    chemin_temporaire = chemin + ".tmp"
    with open(chemin_temporaire, "w") as file:
        yaml.dump(config, file, default_flow_style=False)
    os.replace(chemin_temporaire, chemin)