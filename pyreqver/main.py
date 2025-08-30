import requests
import re
import argparse
import os
from packaging.requirements import Requirement
from packaging.version import Version
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple, Optional


class PythonVersionFinder:
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def get_package_versions(self, package_name: str) -> Dict[str, List[str]]:
        if package_name in self.cache:
            return self.cache[package_name]

        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            versions = {}
            for version_str, release_info in data.get("releases", {}).items():
                if not release_info: 
                    continue        
                python_versions = set()
                requires_python = release_info[0].get("requires_python")
                if requires_python:
                    python_versions.update(self._parse_python_version_specifiers(requires_python))
                classifiers = release_info[0].get("classifiers", [])
                for classifier in classifiers:
                    if classifier.startswith("Programming Language :: Python ::") and \
                       not classifier.endswith(":: Implementation"):
                        version = classifier.split(":: ")[-1].strip()
                        if version and version != "3": 
                            python_versions.add(version)
                
                if python_versions:
                    versions[version_str] = list(python_versions)
            
            self.cache[package_name] = versions
            return versions
            
        except Exception as e:
            print(f"获取包 {package_name} 信息时出错: {e}")
            self.cache[package_name] = {}
            return {}

    def _parse_python_version_specifiers(self, specifiers: str) -> List[str]:
        if not specifiers:
            return []
        try:
            req = Requirement(f"python{specifiers}")
            common_versions = [
                "3.13", "3.12", "3.11", "3.10", "3.9", "3.8", "3.7", "3.6", "3.5", "2.7"
            ]
            
            supported_versions = []
            for version in common_versions:
                try:
                    if Version(version) in req.specifier:
                        supported_versions.append(version)
                except Exception:
                    continue
                    
            return supported_versions
        except Exception:
            return []

    def find_compatible_python_versions(self, requirements_file: str) -> Tuple[Dict[str, List[str]], Set[str]]:
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"错误: 未找到文件 {requirements_file}")
            return {}, set()
        except Exception as e:
            print(f"读取文件 {requirements_file} 时出错: {e}")
            return {}, set()

        packages = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.match(r'^([a-zA-Z0-9\-_.]+)', line)
            if match:
                packages.append(match.group(1))

        if not packages:
            print("警告: 在 requirements.txt 中未找到有效的包")
            return {}, set()

        package_versions = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_package = {
                executor.submit(self.get_package_versions, package): package 
                for package in packages
            }
            
            for future in as_completed(future_to_package):
                package = future_to_package[future]
                try:
                    versions = future.result()
                    package_versions[package] = versions
                except Exception as e:
                    print(f"处理包 {package} 时出错: {e}")
                    package_versions[package] = {}

        common_python_versions = None
        for package, versions in package_versions.items():
            if not versions:
                print(f"警告: 无法获取包 {package} 的版本信息")
                continue
                
            supported_by_package = set()
            for pkg_version, python_versions in versions.items():
                supported_by_package.update(python_versions)
            
            if not supported_by_package:
                print(f"警告: 包 {package} 没有明确的 Python 版本支持信息")
                continue
                
            if common_python_versions is None:
                common_python_versions = supported_by_package
            else:
                common_python_versions &= supported_by_package
                
            sorted_versions = sorted(supported_by_package, key=lambda x: tuple(map(int, x.split('.'))), reverse=True)
            print(f"{package} 可用版本: {sorted_versions}")

        try:
            terminal_width = os.get_terminal_size().columns
            print("-" * terminal_width)
        except:
            print("-" * 80)

        if common_python_versions is None:
            print("错误: 无法确定任何通用的 Python 版本")
            return package_versions, set()
            
        if not common_python_versions:
            print("警告: 未找到支持所有包的 Python 版本")
            return package_versions, set()
            
        return package_versions, common_python_versions


def main():
    parser = argparse.ArgumentParser(description="查找支持 requirements.txt 中所有库的 Python 版本")
    parser.add_argument("requirements", help="requirements.txt 文件的路径")
    args = parser.parse_args()
    
    finder = PythonVersionFinder()
    package_versions, common_versions = finder.find_compatible_python_versions(args.requirements)
    
    if common_versions:
        sorted_versions = sorted(common_versions, key=lambda x: tuple(map(int, x.split('.'))), reverse=True)
        print(f"所有库支持的 Python 版本: {sorted_versions}")
    else:
        print("未找到支持所有库的 Python 版本")


if __name__ == '__main__':
    main()