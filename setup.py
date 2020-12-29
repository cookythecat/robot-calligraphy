from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='robot_calligraphy',
    version='0.1.0',
    description='robot calligrapht application',
    long_description=readme,
    author='cookythecat',
    author_email='hqy407115847@gmail,com',
    url='https://github.com/cookythecat/robot-calligraphy',
    license=license,
    packages=find_packages(exclude=('docs'))
)