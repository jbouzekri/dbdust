# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

""" Module like call entry point of the dbdust application """

import dbdust.admin as admin

if __name__ == "__main__":
    # execute only if run as a script
    admin.run()
