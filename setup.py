#!/usr/bin/env python
import os.path
from distutils.core import setup

try:
    from subprocess import check_output
except ImportError:
    check_output = None


def version_from_git():
    try:
        version = check_output(
            "test -d .git && git fetch --tags && "
            "git describe --tags --dirty | "
            "sed -e 's/-/+/;s/[^A-Za-z0-9.+]/./g'",
            shell=True)
    except:  # (AttributeError, CalledProcessError)
        return None

    version = version.decode('ascii', 'replace')
    if not version.startswith('v'):
        return None

    return version[1:].rstrip()


def version_from_changelog(changelog):
    versions = changelog.split('\nv')[1:]
    incomplete = False

    for line in versions:
        assert line and line[0].isdigit(), line
        line = line.split(' ', 1)[0]
        if all(i.isdigit() for i in line.split('.')):
            version = line  # last "complete version"
            break
        incomplete = True
    else:
        return '0+1.or.more'  # undefined version

    if incomplete:
        version += '+1.or.more'
    return version


if __name__ == '__main__':
    here = os.path.dirname(__file__)
    os.chdir(here or '.')

    with open('README.rst') as fp:
        readme = fp.read()
    with open('CHANGES.rst') as fp:
        changes = fp.read()

    version = (
        version_from_git() or
        version_from_changelog(changes))

    setup(
        name='kleides_dssoclient',
        version=version,
        data_files=[
            ('share/doc/kleides_dssoclient', [
                'LICENSE', 'README.rst', 'CHANGES.rst']),
        ],
        packages=['kleides_dssoclient'],
        package_data={},
        description='Kleides Discourse SSO client for Django',
        long_description=('\n\n\n'.join([readme, changes])),
        author='Walter Doekes, OSSO B.V.',
        author_email='wjdoekes+kleides@osso.nl',
        url='https://github.com/ossobv/kleides-dssoclient',
        license='GPLv3+',
        platforms=['linux'],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Framework :: Django',
            'Framework :: Django :: 2.1',
            'Intended Audience :: System Administrators',
            ('License :: OSI Approved :: GNU General Public License v3 '
             'or later (GPLv3+)'),
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            ('Topic :: System :: Systems Administration :: '
             'Authentication/Directory'),
        ],
        install_requires=[
            # 'Django>=2.1',  # undefined versions..
        ],
    )

# vim: set ts=8 sw=4 sts=4 et ai tw=79:
