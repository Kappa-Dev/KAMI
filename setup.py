"""Setup of KAMI."""

from setuptools import setup, find_packages
setup(name='kami',
      version='0.1',
      description='Knowledge Aggregator and Model Instantiator',
      author='...',
      license='MIT License',
      packages=['kami',
                'kami.data_structures',
                'kami.exporters',
                'kami.client',
                'kami.importers',
                'kami.resolvers',
                'kami.resources',
                'kami.server',
                'kami.utils',
                'kami.server.kami',
                'kami.server.base',
                'kami.server.mu_calculus',
                'anatomizer'],
      package_dir={'kami.server': 'kami/server'},
      package_data={
          'kami.server': ['iRegraph_api.yaml'],
          'anatomizer': ['resources/*']
      },
      include_package_data=True,
      zip_safe=False)
