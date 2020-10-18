#!/usr/bin/env python3

import argparse
from re import match
import logging
from pathlib import Path
from datetime import datetime as dt
from os import chdir

logging.basicConfig(format='%(message)s', level=logging.ERROR)

def set_relative_path(args):
    """Convert absolute path to relative. If the root folder in the current 
    working directory is different from the root folder in the patch, then 
    change the current working directory to root folder in the patch. Otherwise 
    Path.relative_to method will raise ValueError."""
    try:
        relative_path = Path(args.source).relative_to(Path.cwd())
    except ValueError as err:
        logging.error(str(err))
        chdir(Path(args.source).anchor)
    relative_path = Path(args.source).relative_to(Path.cwd())
    args.source = str(relative_path)


def get_ctime(file, format='%y%m%d%H%M%S'):
    # Get create file time
    format = '%m%d_%H%M%S'
    filetime = file.stat().st_ctime
    datetimetime = dt.fromtimestamp(filetime)
    ctime = datetimetime.strftime(format)
    return ctime


def get_mtime(file, format='%y%m%d%H%M%S'):
    # Get modified file time
    format = '%m%d_%H%M%S'
    filetime = file.stat().st_mtime
    datetimetime = dt.fromtimestamp(filetime)
    mtime = datetimetime.strftime(format)
    return mtime


def rename_wildcard(pathes, args):
    logging.info(f'\nRename:')
    root_path = ''
    for path in pathes:
        if str(path.parent) != root_path:
            root_path = str(path.parent)
            logging.info(f'       {root_path}\\')
        newname = args.destination.replace('*', path.stem)
        path_new = Path(path.parent).joinpath(newname)
        
        if not args.debug:
            try:
                Path(path).rename(path_new)
            except PermissionError as err:
                logging.error(str(err))
        
        logging.info(' '*(len(root_path)+8) + f'{path.name} -----> {newname}')


def main(args):
    logging.info(f'Arguments received: {args}')
    
    # If path absolute glob will raise error, so convert abs path to relative
    if Path(args.source).anchor:
        set_relative_path(args)

    if args.recurse:
        try:
            if '**' not in args.source:
                parts = Path(args.source).parts
                args.source = '\\'.join((*parts[:-1], '**', parts[-1]))
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
        rename_wildcard(paths, args)

    logging.info(f'\nRenamed {len(paths)} files')


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
    parser.add_argument(
        '-d', 
        action='store_true',
        dest='debug',
        default=False, 
        help='debug'
    )
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    main(args)