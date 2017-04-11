"""Setup of KAMI."""

from setuptools import setup
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
                'kami.utils'
                ],
      zip_safe=False)
