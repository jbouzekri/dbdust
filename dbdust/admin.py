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
import datetime
import shutil
import subprocess

import configparser
import importlib
import logging
import os
import sys
import tempfile

import dbdust.dumper

logger = logging.getLogger('dbdust')
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
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
    now = datetime.datetime.utcnow()

    logger.info('start')

    try:
        dump_type = conf.get('general', 'database')
        if dump_type not in dbdust.dumper.dumper_config:
            raise Exception('{} database not supported'.format(dump_type))

        dump_conf = dict(conf.items(dump_type))

        dumper_config = dbdust.dumper.dumper_config.get(dump_type)
        dumper_bin_name = dumper_config.get('bin_name')
        dumper_file_ext = dumper_config.get('file_ext')
        dumper_cli_func = dumper_config.get('cli_builder')

        dump_bin_path = shutil.which(dumper_bin_name)
        if dump_bin_path is None:
            current_dir_bin_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', dumper_bin_name)
            dump_bin_path = current_dir_bin_path if os.path.exists(current_dir_bin_path) else None
        if dump_bin_path is None:
            raise Exception('{} not found on the system'.format(dumper_bin_name))
        logger.debug('{} found at {}'.format(dumper_bin_name, dump_bin_path))

        tmp_dir = conf.get('general', 'tmp_dir', fallback=tempfile.gettempdir())
        file_prefix = conf.get('general', 'file_prefix', fallback="backup-")
        file_name = "{}{}".format(file_prefix, now.strftime("%Y%m%d%H%M%S"))

        with tempfile.TemporaryDirectory(None, 'dbdust-', tmp_dir) as tmpdir_name:
            tmp_file = os.path.join(tmpdir_name, "{}.{}".format(file_name, dumper_file_ext))
            logger.debug('backup will be temporary stored at {}'.format(tmp_file))

            dump_cli = dumper_cli_func(dump_bin_path, tmp_file, **dump_conf)
            logger.debug('command : {}'.format(' '.join(dump_cli)))

            dump_result = subprocess.run(dump_cli, stdin=sys.stdin, stdout=sys.stdout)
            if dump_result.returncode != 0:
                raise Exception('dump command exited with error code {}'.format(dump_result.returncode))

            logger.debug('dump command executed successfully')
            logger.debug('dump file size is {} Bytes'.format(os.path.getsize(tmp_file)))

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

    logger.info('end')

    sys.exit(exit_code)
