from distutils.core import setup

from byteBuggy.config import Configuration

setup(
    name='byteBuggy',
    version=Configuration.version,
    author='RcAttack',
    author_email='hbrito@leomail.tamuc.edu',
    url='https://github.com/derv82/byteBuggy2',
    packages=[
        'byteBuggy',
        'byteBuggy/attack',
        'byteBuggy/model',
        'byteBuggy/tools',
        'byteBuggy/util',
    ],
    data_files=[
        ('share/dict', ['wordlist-top4800-probable.txt'])
    ],
    entry_points={
        'console_scripts': [
            'byteBuggy = byteBuggy.byteBuggy:entry_point'
        ]
    },
    license='GNU GPLv2',
    scripts=['bin/byteBuggy'],
    description='Wireless Network Auditor for Linux',
    #long_description=open('README.md').read(),
    long_description='''Wireless Network Auditor for Linux.

    Cracks WEP, WPA, and WPS encrypted networks.

    Depends on Aircrack-ng Suite, Tshark (from Wireshark), and various other external tools.''',
    classifiers = [
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3"
    ]
)
