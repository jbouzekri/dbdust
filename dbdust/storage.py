# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

import ntpath
import os


class StorageHandler(object):
    def __init__(self, storage_impl):
        self.storage_impl = storage_impl

    def save(self, file_path):
        return self.storage_impl.save(file_path)


class DbDustStorageException(Exception):
    pass


class StorageFactory(type):
    storage_list = {}

    def __new__(cls, cls_name, superclasses, attribute_dict):
        cls_obj = type.__new__(cls, cls_name, superclasses, attribute_dict)
        cls.storage_list[cls_obj.storage_type] = cls_obj
        return cls_obj

    @staticmethod
    def create(logger, storage_type, *args, **kwargs):
        return StorageFactory.storage_list[storage_type](logger, *args, **kwargs)


class AzureBlocStorage(object, metaclass=StorageFactory):
    storage_type = 'azure_blob'


class LocalStorage(object, metaclass=StorageFactory):
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
        os.replace(file_path, os.path.join(self.local_path, os.path.basename(file_path)))
        return True


