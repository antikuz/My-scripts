#!/usr/bin/env python3

import argparse
from re import match
import logging
from pathlib import Path

logging.basicConfig(level=logging.ERROR)


def rename_wildcard(pathes, rename_pattern):
    for path in pathes:
        newname = rename_pattern.replace('*', path.stem)
        path_new = Path(path.parent).joinpath(newname)
        
        try:
            Path(path).rename(path_new)
        except PermissionError as err:
            logging.error(str(err))

        logging.info(f'Rename: {str(path)} -----> {newname}')


def main(args):
    logging.info(f'Получены аргументы {args}')

    if args.r:
        try:
            paths = Path().rglob(args.path)
        except OSError as err:
            logging.error(str(err))
    else:
        paths = Path().glob(args.path)
    
    if args.v:
        paths = [path for path in paths if path.is_file()]
        root_path = ''
        for path in paths:
            if str(path.parent) != root_path:
                root_path = str(path.parent)
                logging.info(f'{root_path}:')
            logging.info(' '*(len(root_path)+1) + path.name)

    # Если в паттерне присутствует * и расширение файла то, меняем расширения
    if match(r'.*?\*\.\S+', args.pattern):
        rename_wildcard(paths, args.pattern)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Description argumentparser')
    parser.add_argument(
        'path', 
        action='store', 
        help='Path to directory with files to rename'
    )
    parser.add_argument(
        'pattern', 
        action='store', 
        help='Pattern to rename files or new file name'
    )
    parser.add_argument(
        '-r', 
        action='store_true', 
        default=False, 
        help='Recurse into subdirectories'
    )
    parser.add_argument(
        '-v', 
        action='store_true', 
        default=False, 
        help='Verbose'
    )
    args = parser.parse_args()
    if args.v:
        logging.getLogger().setLevel(logging.INFO)
    main(args)