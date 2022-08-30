from setuptools import setup, find_packages


setup(
    name='cldcatplot',
    version='0.1',
    license='MIT',
    author="Dominik Both",
    author_email='py@dboth.de',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/dboth/cldcatplot',
    keywords='seaborn compactletter',
    install_requires=[
          'seaborn','pandas','matplotlib','statsmodels'
      ],

)