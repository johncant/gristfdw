from setuptools import setup, find_packages, Extension

setup(
  name='gristfdw',
  version='0.0.1',
  author='John Cant',
  license='Postgresql',
  packages=['gristfdw'],
  install_requires=["grist_api@git+https://github.com/johncant/py_grist_api@jc_add_list_tables_columns#egg=grist_api-0.1.0"],
  extras_require={
      "test": ["pytest", "psycopg2", "tox", "tox-docker", "requests"]
  }
)

