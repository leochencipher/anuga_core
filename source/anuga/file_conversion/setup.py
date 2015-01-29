from __future__ import division, print_function

import os
import sys

from os.path import join

def configuration(parent_package='',top_path=None):
    
    from numpy.distutils.misc_util import Configuration
    from numpy.distutils.system_info import get_info
    
    config = Configuration('file_conversion', parent_package, top_path)

    config.add_data_dir('test')
    config.add_data_dir(join('test','data'))

    if parent_package is '':
        anuga_dir = '..'
    else:
        anuga_dir = '.'

    util_dir = join(anuga_dir,'utilities')
    
    config.add_extension('calc_grid_values_ext',
                         sources=['calc_grid_values_ext.c'],
                         include_dirs=[util_dir])
    

    return config
    
if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)