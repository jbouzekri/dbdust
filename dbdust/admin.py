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
import os


def validate_config_file(config_file):
    if not os.path.isfile(config_file):
        raise argparse.ArgumentTypeError('Invalid config file {}'.format(config_file))
    return config_file


def create_cmd_line_parser():
    parser = argparse.ArgumentParser(description='trigger the backup of the database, store the '
                                                 'backup and clean old ones')
    parser.add_argument('-c', '--config', type=validate_config_file, dest='config_file',
                        help='config file, if not read config from environment')
    return parser


def run(*args, **kwargs):
    """ Called by console_scripts `dbdust` to launch the workers

    Usage : `dbdust -c config.cfg`
    """
    args = create_cmd_line_parser().parse_args()

    print('dbdust running ...', args)
