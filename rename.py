#!/usr/bin/env python3

import argparse
from re import match
import logging
from pathlib import Path

logging.basicConfig(format='%(message)s', level=logging.ERROR)


def rename_wildcard(pathes, rename_pattern):
    logging.info(f'\nChange:')
    root_path = ''
    for path in pathes:
        if str(path.parent) != root_path:
            root_path = str(path.parent)
            logging.info(f'       {root_path}\\')
        newname = rename_pattern.replace('*', path.stem)
        path_new = Path(path.parent).joinpath(newname)
        
        try:
            Path(path).rename(path_new)
        except PermissionError as err:
            logging.error(str(err))
        
        logging.info(' '*(len(root_path)+8) + f'{path.name} -----> {newname}')


def main(args):
    logging.info(f'Arguments received: {args}')

    if args.recurse:
        try:
            paths = Path().rglob(args.source)
        except OSError as err:
            logging.error(str(err))
    else:
        paths = Path().glob(args.source)
        
    paths = [path for path in paths if path.is_file()]
    
    # If verbose - output found files
    if args.verbose:
        root_path = ''
        logging.info('Find:')
        for path in paths:
            if str(path.parent) != root_path:
                root_path = str(path.parent)
                logging.info(f'     {root_path}\\')
            logging.info(' '*(len(root_path)+6) + path.name)

    # If the pattern contains * and the file ext, then change the ext
    if match(r'.*?\*.*?\.\S+', args.destination):
        rename_wildcard(paths, args.destination)

    logging.info(f'\nChanged {len(paths)} files')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Description argumentparser')
    parser.add_argument(
        'source', 
        action='store', 
        help='Path to the directory with files to change'
    )
    parser.add_argument(
        'destination', 
        action='store', 
        help='Pattern for changing files'
    )
    parser.add_argument(
        '-r', 
        action='store_true', 
        default=False, 
        dest='recurse',
        help='Recurse into subdirectories'
    )
    parser.add_argument(
        '-v', 
        action='store_true',
        dest='verbose',
        default=False, 
        help='Verbose'
    )
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    main(args)