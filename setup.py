"""Setup of KAMI."""

from setuptools import setup
setup(name='kami',
      version='0.1',
      description='Knowledge Aggregator and Model Instantiator',
      author='Russ Harmer, Sebastien Legare, Eugenia Oshurko',
      license='MIT License',
      packages=['kami',
                'kami.exporters',
                'kami.importers',
                'kami.resolvers',
                'kami.resources',
                'kami.utils',
                'anatomizer'],
      package_data={
          'anatomizer': ['resources/*'],
      },
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "indra",
          "flask",
          "flex",
          "lxml",
          "jpype1"
      ])
