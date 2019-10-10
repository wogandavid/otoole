"""Creates a datapackage from a collection of CSV files of OSeMOSYS input data

- Uses Frictionless Data datapackage concept to build a JSON schema of the dataset
- Enforces relations between sets and indices in parameter files
"""

import logging
import os
import sys

from datapackage import Package

from otoole.preprocess.excel_to_osemosys import read_config
from otoole.preprocess.longify_data import main as longify

logger = logging.getLogger()


def generate_package(path_to_package):
    """Creates a datapackage in folder ``path_to_package``

    [{'fields': 'REGION', 'reference': {'resource': 'REGION', 'fields': 'VALUE'}}]
    """

    datapath = os.path.join(path_to_package)
    package = Package(base_path=datapath)

    package.infer('data/*.csv')

    package.descriptor['licenses'] = [{"name": "CC-BY-4.0",
                                       "path": "https://creativecommons.org/licenses/by/4.0/",
                                       "title": "Creative Commons Attribution 4.0"}]

    package.descriptor['title'] = 'The OSeMOSYS Simplicity Example Model'

    package.descriptor['name'] = 'osemosys_model_simplicity'

    package.descriptor['contributors'] = [{"title": "Will Usher",
                                           "email": "wusher@kth.se",
                                           "path": "http://www.kth.se/wusher",
                                           "role": "author"
                                           }]

    package.commit()

    config = read_config()

    new_resources = []
    for resource in package.resources:

        descriptor = resource.descriptor

        name = resource.name
        if config[name]['type'] == 'param':

            indices = config[name]['indices']
            logger.debug("Indices of %s are %s", name, indices)

            foreign_keys = []
            for index in indices:
                key = {'fields': index, 'reference': {'resource': index, 'fields': 'VALUE'}}
                foreign_keys.append(key)

            descriptor['schema']['foreignKeys'] = foreign_keys
            descriptor['schema']['primaryKey'] = indices
            descriptor['schema']['missingValues'] = [str(config[name]['default'])]

        new_resources.append(descriptor)

    package.descriptor['resources'] = new_resources
    package.commit()

    filepath = os.path.join(path_to_package, 'datapackage.json')
    package.save(filepath)


def validate_contents(path_to_package):

    filepath = os.path.join(path_to_package)
    package = Package(filepath)

    for resource in package.resources:
        try:
            if resource.check_relations():
                logger.info("%s is valid", resource.name)
        except KeyError as ex:
            logger.warning("Validation error in %s: %s", resource.name, str(ex))


def main(wide_folder, narrow_folder):
    longify(wide_folder, narrow_folder)
    generate_package(narrow_folder)
    absolute_path = os.path.join(narrow_folder, 'datapackage.json')
    validate_contents(absolute_path)


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    wide_folder = sys.argv[1]
    narrow_folder = sys.argv[2]
    main(wide_folder, narrow_folder)
