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
import traceback
import collections
import configparser
import datetime
import logging
import os
import shutil
import subprocess
import sys
import tempfile

import dbdust.dumper
import dbdust.storage

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

    @staticmethod
    def _get_default_from_env():
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


def get_dump_config(dump_type, dbdust_conf):
    """ Get all settings for the dump operation

    :param dump_type: dump command type
    :rtype: str
    :param dbdust_conf: config references for current dbdust process
    :type dbdust_conf: dbdust.admin.DbDustConfig
    :return: a named tuple of all settings for the dump operation
    :rtype: collections.namedtuple
    """
    DumpConfig = collections.namedtuple('DumpConfig', 'type bin_path file_ext cli_func cli_conf zip_path')

    dumper_config = dbdust.dumper.dumper_config.get(dump_type)

    bin_name = dumper_config.get('bin_name')
    file_ext = dumper_config.get('file_ext')
    zip_name = dumper_config.get('zip_name')
    cli_func = dumper_config.get('cli_builder')
    cli_conf = dict(dbdust_conf.items(dump_type))

    bin_path = shutil.which(bin_name)
    if bin_path is None:
        current_dir_bin_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', bin_name)
        bin_path = current_dir_bin_path if os.path.exists(current_dir_bin_path) else None
    if bin_path is None:
        raise Exception('{} not found on the system'.format(bin_name))
    logger.debug('{} found at {}'.format(bin_name, bin_path))

    zip_path = None
    if zip_name is not None:
        zip_path = shutil.which(zip_name)
        if zip_path is None:
            raise Exception('{} not found on the system'.format(zip_name))

    return DumpConfig(type=dump_type, bin_path=bin_path, file_ext=file_ext, cli_func=cli_func,
                      cli_conf=cli_conf, zip_path=zip_path)


def get_storage_config(storage_type, dbdust_conf):
    """ Get all settings for the storage operation

    :param storage_type: storage command type
    :rtype: str
    :param dbdust_conf: config references for current dbdust process
    :type dbdust_conf: dbdust.admin.DbDustConfig
    :return: a named tuple of all settings for the storage operation
    :rtype: collections.namedtuple
    """
    StorageConfig = collections.namedtuple('StorageConfig', 'type file_prefix date_format retain_conf impl_conf')

    file_prefix = dbdust_conf.get('general', 'file_prefix', fallback="backup-")
    date_format = dbdust_conf.get('general', 'date_format', fallback="%Y%m%d%H%M%S")
    daily_retain = int(dbdust_conf.get('general', 'daily', fallback=7))
    weekly_retain = int(dbdust_conf.get('general', 'weekly', fallback=4))
    monthly_retain = int(dbdust_conf.get('general', 'monthly', fallback=2))
    max_per_day = int(dbdust_conf.get('general', 'max', fallback=1))
    impl_conf = dict(dbdust_conf.items(storage_type))

    return StorageConfig(type=storage_type, file_prefix=file_prefix, date_format=date_format, impl_conf=impl_conf,
                         retain_conf={'daily_retain': daily_retain, 'weekly_retain': weekly_retain,
                                      'monthly_retain': monthly_retain, 'max_per_day': max_per_day})


class DbDustBackupHandler(object):
    """ Backup handler :
    - execute backup cli and store result in tmp folder
    - save the new backup in storage
    - cleanup storage by rotating old backups

    :param logger_: main program logger
    :type logger_: logging.Logger
    :param dump_conf : a named tuple of all settings for the dump operation
    :type dump_conf: collections.namedtuple
    :param storage_conf : a named tuple of all settings for the storage operation
    :type storage_conf: collections.namedtuple
    """
    def __init__(self, logger_, dump_conf, storage_conf):
        self.logger = logger_
        self.dump_conf = dump_conf
        self.storage_conf = storage_conf

        storage_impl = dbdust.storage.StorageFactory.create(logger, storage_conf.type, **storage_conf.impl_conf)
        self.storage_handler = dbdust.storage.StorageHandler(storage_impl, storage_conf.file_prefix,
                                                             storage_conf.date_format, **storage_conf.retain_conf)

        now = datetime.datetime.utcnow()
        self.file_name = "{}{}.{}".format(self.storage_conf.file_prefix,
                                          now.strftime(self.storage_conf.date_format),
                                          self.dump_conf.file_ext)

    def process(self, tmp_dir):
        """ Execute the backup and store tasks

        :param tmp_dir: the directory where the temporary dump will be stored
        :type tmp_dir: str
        """

        with tempfile.TemporaryDirectory(None, 'dbdust-', tmp_dir) as tmpdir_name:
            tmp_file = os.path.join(tmpdir_name, self.file_name)
            self.logger.info('backup temporary stored at {}'.format(tmp_file))

            self._dump(tmp_file)
            self._save(tmp_file)

    def _dump(self, tmp_file):
        """ Execute the dump/backup task in the temporary file

        .. note:: the dump task must return a single file

        :param tmp_file: temp file absolute path
        :type tmp_file: str
        """
        dump_cli = self.dump_conf.cli_func(self.dump_conf.bin_path, self.dump_conf.zip_path, tmp_file,
                                           **self.dump_conf.cli_conf)
        dump_cmd = ' '.join(dump_cli)
        self.logger.debug('command : {}'.format(dump_cmd))

        start_date = datetime.datetime.utcnow()
        dump_result = subprocess.run(dump_cmd, stdin=sys.stdin, stdout=sys.stdout, shell=True)
        if dump_result.returncode != 0:
            raise Exception('dump command exited with error code {}'.format(dump_result.returncode))
        end_date = datetime.datetime.utcnow()

        self.logger.info('dump command executed successfully')
        self.logger.debug('dump file size is {} bytes'.format(os.path.getsize(tmp_file)))
        self.logger.debug('dump executed in {} seconds'.format((end_date - start_date).total_seconds()))

    def _save(self, tmp_file):
        """ Execute the storage task (store and rotate)

        :param tmp_file: temp file absolute path
        :type tmp_file: str
        """
        self.storage_handler.save(tmp_file)
        self.logger.info('file {} saved to storage successfully'.format(self.file_name))
        self.storage_handler.rotate()
        self.logger.info('rotation done successfully')


def run(*args, **kwargs):
    """ Called by console_scripts `dbdust` to launch the workers

    Usage : `dbdust -c config.cfg`
    """
    args = create_cmd_line_parser().parse_args()
    conf = DbDustConfig(args.config_file)
    exit_code = 0

    logger.info('start')

    try:

        dump_type = conf.get('general', 'database')
        if dump_type not in dbdust.dumper.dumper_config:
            raise Exception('{} database not supported'.format(dump_type))

        storage_type = conf.get('general', 'storage')
        if storage_type not in dbdust.storage.StorageFactory.storage_list:
            raise Exception('{} storage not supported'.format(storage_type))

        dump_conf = get_dump_config(dump_type, conf)
        storage_conf = get_storage_config(storage_type, conf)
        tmp_dir = conf.get('general', 'tmp_dir', fallback=tempfile.gettempdir())

        backup_handler = DbDustBackupHandler(logger, dump_conf, storage_conf)
        backup_handler.process(tmp_dir)

    except configparser.Error as e:
        logger.error("configuration error : {}".format(str(e)))
        exit_code = 2
    except Exception as e:
        logger.error(str(e))
        traceback.print_exc()
        exit_code = 1

    logger.info('end')

    sys.exit(exit_code)
