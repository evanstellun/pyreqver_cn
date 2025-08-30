#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 注意：要使用此文件的'upload'功能，您必须：
#   $ pipenv install twine --dev

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# 包元数据。
NAME = 'pyreqver_cn'
DESCRIPTION = ' 一个命令行工具，帮助您找到支持您 requirements.txt 文件中所有库的 Python 版本'
URL = 'https://github.com/evanstellun/pyreqver_cn'
EMAIL = 'niweilun@outlook.com'
AUTHOR = 'Evanstellun'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = '0.1.0'

# 执行此模块需要哪些包？
REQUIRED = [
     'requests',
     'packaging',
]

# 哪些包是可选的？
EXTRAS = {
    # 'fancy feature': ['django'],
}

# 其余部分您不需要过多修改 :)
# ------------------------------------------------
# 除了许可证和 Trove 分类器！
# 如果您确实更改了许可证，请记住更改相应的 Trove 分类器！

here = os.path.abspath(os.path.dirname(__file__))

# 导入 README 并将其用作长描述。
# 注意：这仅在您的 MANIFEST.in 文件中存在 'README.md' 时才有效！
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# 将包的 __version__.py 模块作为字典加载。
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


class UploadCommand(Command):
    """支持 setup.py 上传。"""

    description = '构建并发布包。'
    user_options = []

    @staticmethod
    def status(s):
        """以粗体打印内容。"""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('删除之前的构建…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('构建源代码和 Wheel（通用）分发…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('通过 Twine 上传包到 PyPI…')
        os.system('twine upload dist/*')

        self.status('推送 git 标签…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


# 魔法发生的地方：
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    # 如果您的包是单个模块，请使用此代替 'packages'：
    # py_modules=['mypackage'],

    entry_points={
        'console_scripts': ['pyreqver=pyreqver.main:main'],
    },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove 分类器
        # 完整列表：https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    # $ setup.py publish 支持。
    cmdclass={
        'upload': UploadCommand,
    },
)