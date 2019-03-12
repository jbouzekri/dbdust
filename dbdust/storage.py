# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

""" Storage handler and implementation to send backup to supported destination and rotate old backup """

import datetime
import os


class StorageHandler(object):
    """ Implements the logic of storage rotation

    :param storage_impl: the storage protocol implementation
    :type storage_impl: dbdust.storage.BaseStorage
    :param file_prefix: prefix in the generated file name
    :type file_prefix: str
    :param date_format: python datetime format to append current date to storage name
    :type date_format: str
    :param daily_retain: number of files to keep for the past X days
    :type daily_retain: int
    :param weekly_retain: number of files to keep for the past X weeks
    :type weekly_retain: int
    :param monthly_retain: number of files to keep for the past X months
    :type monthly_retain: int
    :param max_per_day: number of files to keep max each days
    :type max_per_day: int
    """

    def __init__(self, storage_impl, file_prefix, date_format, daily_retain,
                 weekly_retain, monthly_retain, max_per_day):
        self.storage_impl = storage_impl
        self.file_prefix = file_prefix
        self.date_format = date_format
        self.max_per_day = max_per_day
        self.days_to_keep = self._build_day_to_keep(daily_retain, weekly_retain, monthly_retain)

    @staticmethod
    def _build_day_to_keep(daily, weekly, monthly):
        """ Build a dict with keys equals to day where we want to keep a backup
        based on configuration and values equals to 0 (it will be incremented
        each time we find a file for this day)

        :param daily: number of files to keep for the past X days
        :type daily: int
        :param weekly: number of files to keep for the past X weeks
        :type weekly: int
        :param monthly: number of files to keep for the past X months
        :type monthly: int
        """
        days_to_keep = {}
        today = datetime.datetime.today().date()
        first_day_week = today - datetime.timedelta(days=today.weekday())
        first_day_month = today.replace(day=1)
        for i in range(0, daily):
            days_to_keep[today - datetime.timedelta(days=i)] = 0
        for i in range(0, weekly):
            days_to_keep[first_day_week - datetime.timedelta(days=i*7)] = 0
        for i in range(0, monthly):
            month_nb = ((first_day_month.month - i) + 12) % 12 or 12
            days_to_keep[first_day_month.replace(month=month_nb)] = 0
        return days_to_keep

    def _get_sorted_backup_files_list(self):
        """ Get a list of all files available in the storage and store it per date

        :return: sorted (datetime in file name desc) list of items of dict type.
            Each item is a file in the storage
        :rtype: list
        """
        backup_list = self.storage_impl.list()
        for item in backup_list:
            item.update({'date': self.extract_date_from_file_name(item['file_name'])})
        backup_list.sort(key=lambda r: r['date'], reverse=True)
        return backup_list

    def save(self, file_path):
        """ Wrapper around the store implementation for the storage """
        return self.storage_impl.store(file_path)

    def rotate(self):
        """ Rotate the file kept in storage (remove old files) """
        backup_list = self._get_sorted_backup_files_list()
        for item in backup_list:
            item_date = item['date'].date()
            self.days_to_keep[item_date] += 1
            if self.days_to_keep[item_date] > self.max_per_day:
                self.storage_impl.delete(item['id'])

    def extract_date_from_file_name(self, file_name):
        """ Extract a python datetime based on the value in the name of a stored file

        :return: datetime
        :rtype: datetime.datetime
        """
        file_name = file_name[len(self.file_prefix):].split('.', 1)[0]
        return datetime.datetime.strptime(file_name, self.date_format)


class StorageFactory(type):
    """ metaclass for all storage implementation used as a registry """
    storage_list = {}

    def __new__(mcs, cls_name, superclasses, attribute_dict):
        cls_obj = type.__new__(mcs, cls_name, superclasses, attribute_dict)
        mcs.storage_list[cls_obj.storage_type] = cls_obj
        return cls_obj

    @staticmethod
    def create(logger, storage_type, *args, **kwargs):
        """ Instantiate the implementation of a storage """
        return StorageFactory.storage_list[storage_type](logger, *args, **kwargs)


class DbDustStorageException(Exception):
    """ Base exception for all storage exception """
    pass


class BaseStorage(object):
    """ Base class that all storage implementation extends """
    storage_type = None

    def __getattr__(self, name):
        """ catch all getter magic method to raise an exception if method is not found

        :raise dbdust.storage.DbDustStorageException: if a method not implemented is called
        """
        raise DbDustStorageException('{} storage : {} not implemented'.format(self.storage_type, name))


class AzureBlocStorage(BaseStorage, metaclass=StorageFactory):
    storage_type = 'azure_blob'


class LocalStorage(BaseStorage, metaclass=StorageFactory):
    """ Local filesystem storage implementation

    :param logger: logger to be used
    :type logger: logging.Logger
    :param path: local folder in filesystem to store files
    :type path: str
    """
    storage_type = 'local'

    def __init__(self, logger, path, *args, **kwargs):
        if not os.path.isdir(path):
            raise DbDustStorageException('{} folder does not exist'.format(path))
        if not os.access(path, os.W_OK | os.X_OK):
            raise DbDustStorageException('{} folder is not writable'.format(path))
        self.local_path = os.path.abspath(path)
        logger.debug('local storage : backup will be stored at {}'.format(self.local_path))
        self.logger = logger

    def store(self, file_path):
        """ Move local temp file to local storage

        :param file_path: file to move
        :type file_path: str
        """
        dest_path = os.path.join(self.local_path, os.path.basename(file_path))
        os.replace(file_path, dest_path)
        self.logger.debug('local storage : backup stored to {}'.format(dest_path))

    def list(self):
        """ List all files available in local storage

        :return: list of dict. Each dict has an id (used to reference the file later), a file_name, a file path
        :type: dict[]
        """
        return [{'id': item, 'file_name': item,
                 'path': os.path.join(self.local_path, item)} for item in os.listdir(self.local_path)]

    def delete(self, item_id):
        """ Delete a file by its id in this storage

        :param item_id: in case of the local storage, it is the file name
        :type item_id: str
        """
        file_path = os.path.join(self.local_path, item_id)
        os.remove(file_path)
        self.logger.debug('local storage : removed {}'.format(file_path))