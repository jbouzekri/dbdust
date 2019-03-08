# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

import datetime
import os

from typing import Type

class StorageHandler(object):
    def __init__(self, storage_impl, file_prefix, date_format, daily_retain,
                 weekly_retain, monthly_retain, max_per_day):
        self.storage_impl = storage_impl
        self.file_prefix = file_prefix
        self.date_format = date_format
        self.max_per_day = max_per_day
        self.days_to_keep = self._build_day_to_keep(daily_retain, weekly_retain, monthly_retain)

    @staticmethod
    def _build_day_to_keep(daily, weekly, monthly):
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

    def save(self, file_path):
        return self.storage_impl.save(file_path)

    def rotate(self):
        backup_list = self.storage_impl.list()
        for item in backup_list:
            item.update({'date': self.extract_date_from_file_name(item['file_name'])})
        backup_list.sort(key=lambda r: r['date'], reverse=True)
        for item in backup_list:
            item_date = item['date'].date()
            self.days_to_keep[item_date] += 1
            if self.days_to_keep[item_date] > self.max_per_day:
                self.storage_impl.delete(item['id'])

    def extract_date_from_file_name(self, file_name):
        file_name = file_name[len(self.file_prefix):].split('.', 1)[0]
        return datetime.datetime.strptime(file_name, self.date_format)


class DbDustStorageException(Exception):
    pass


class BaseStorage(object):
    storage_type = None

    def __getattr__(self, name):
        raise DbDustStorageException('{} storage : {} not implemented'.format(self.storage_type, name))


class StorageFactory(type):
    storage_list = {}

    def __new__(mcs: Type[BaseStorage], cls_name, superclasses, attribute_dict):
        cls_obj = type.__new__(mcs, cls_name, superclasses, attribute_dict)
        mcs.storage_list[cls_obj.storage_type] = cls_obj
        return cls_obj

    @staticmethod
    def create(logger, storage_type, *args, **kwargs):
        return StorageFactory.storage_list[storage_type](logger, *args, **kwargs)


class AzureBlocStorage(BaseStorage, metaclass=StorageFactory):
    storage_type = 'azure_blob'


class LocalStorage(BaseStorage, metaclass=StorageFactory):
    storage_type = 'local'

    def __init__(self, logger, path, *args, **kwargs):
        if not os.path.isdir(path):
            raise DbDustStorageException('{} folder does not exist'.format(path))
        if not os.access(path, os.W_OK | os.X_OK):
            raise DbDustStorageException('{} folder is not writable'.format(path))
        self.local_path = os.path.abspath(path)
        logger.debug('local storage : backup will be stored at {}'.format(self.local_path))
        self.logger = logger

    def save(self, file_path):
        dest_path = os.path.join(self.local_path, os.path.basename(file_path))
        os.replace(file_path, dest_path)
        self.logger.debug('local storage : backup stored to {}'.format(dest_path))

    def list(self):
        return [{'id': item, 'file_name': item,
                 'path': os.path.join(self.local_path, item)} for item in os.listdir(self.local_path)]

    def delete(self, item_id):
        file_path = os.path.join(self.local_path, item_id)
        os.remove(file_path)
        self.logger.debug('local storage : removed {}'.format(file_path))