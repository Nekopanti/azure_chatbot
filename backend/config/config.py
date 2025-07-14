import yaml
import os

config = None

path = os.path.dirname(__file__)


with open(f"{path}/configuration.yaml", "rb") as stream:
    config = yaml.safe_load(stream)


def get_parameter(property_path: str):
    path_arr = property_path.split(".")
    value = config
    for name in path_arr:
        value = value[name]
    return value
