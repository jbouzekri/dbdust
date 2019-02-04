# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

""" Entry point of the dbdust application """

import argparse
import configparser
import importlib
import logging
import os
import sys
import tempfile

logger = logging.getLogger('dbdust')
formatter = logging.Formatter(fmt="%(levelname)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def validate_config_file(config_file):
    """ Validate that a file exists

    :raise: :class:`argparse.ArgumentTypeError` if file not found
    :return: the file path
    :rtype: str
    """
    if not os.path.isfile(config_file):
        raise argparse.ArgumentTypeError('Invalid config file {}'.format(config_file))
    return config_file


def create_cmd_line_parser():
    """ Create the command line parser for cli

    :return: a parser object
    :rtype: :class:`argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(description='trigger the backup of the database, store the '
                                                 'backup and clean old ones')
    parser.add_argument('-c', '--config', type=validate_config_file, dest='config_file',
                        help='config file, if not read config from environment')
    return parser


class DbDustConfig(configparser.ConfigParser):
    """ Handle configuration from environment variables or from a file

    :param str configfile_path: path to the configfile or None
    """
    def __init__(self, configfile_path=None):
        super(DbDustConfig, self).__init__()
        self.read_dict(self._get_default_from_env())
        if configfile_path:
            self.read(configfile_path)

    def _get_default_from_env(self):
        """ Create a 2 levels dict from environment variables starting with `DBDUST___`
        Used to setup default value in parser

        `DBDUST___GENERAL__MY_VAR='value'` becomes `{'general': {'my_var': 'value'}}`

        :return: dict built from environment variable
        :type: dict
        """
        env = {k[9:]: v for (k, v) in os.environ.items() if k.startswith('DBDUST___')}
        conf_from_env = {}
        for k, v in env.items():
            splited_key = k.split('__')
            level1_key = splited_key[0].lower()
            level2_key = splited_key[1].lower()
            if level1_key not in conf_from_env:
                conf_from_env[level1_key] = {}
            conf_from_env[level1_key][level2_key] = v
        return conf_from_env

    def to_dict(self):
        """ Helper to transform object to dict

        :return: a dict version of the configparser
        :rtype: dict
        """
        return {s: dict(self.items(s)) for s in self.sections()}


def run(*args, **kwargs):
    """ Called by console_scripts `dbdust` to launch the workers

    Usage : `dbdust -c config.cfg`
    """
    args = create_cmd_line_parser().parse_args()
    conf = DbDustConfig(args.config_file)
    exit_code = 0

    try:
        tmp_dir = conf.get('general', 'tmp_dir', fallback=tempfile.gettempdir())
        dump_type = conf.get('general', 'database')
        dump_module = importlib.import_module('dbdust.database.{}'.format(dump_type))
        dump_handler = getattr(dump_module, '{}Handler'.format(dump_type.capitalize()))()

        with tempfile.TemporaryDirectory(None, 'dbdust-', tmp_dir) as tmpdirname:
            print(tmpdirname)
            with dump_handler:
                dump_handler.dump()

    except ImportError as e:
        print(str(e))
        logger.error("No handler to export database {}".format(dump_type))
        exit_code = 2
    except configparser.Error as e:
        logger.error("configuration error : {}".format(str(e)))
        exit_code = 2
    except Exception as e:
        print(type(e))
        logger.error(str(e))
        exit_code = 1

    sys.exit(exit_code)
