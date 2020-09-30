#!/usr/bin/env python3

import argparse
import os
from re import match
import glob
from collections import namedtuple
import logging

logging.basicConfig(level=logging.ERROR)
PathAndFiles = namedtuple('PathFiles', ['path', 'files_list'])

def parse_arg_path(path):
    # Проверяем абсолютный ли путь, если нет, то делаем абсолютным
    isabs = os.path.isabs(path)
    if isabs:
        logging.info(f'Path ABS: [{path}]')
    else:
        path = os.path.join(os.getcwd(), path)
        logging.info(f'Path NOTABS: [{path}]')
    
    # Проверям содержатся ли в пути wildcard, ** для папок и * для файлов
    if '**' in path:
        path, file = path.split('**')
        path = path.strip(r'\/')
        args.R = True
        args.r = file.strip(r'\/')
    elif '*' in path:
        path, regex = os.path.split(path)
        path = path.strip(r'\/')
        args.r = regex.strip(r'\/')
    
    return path


def recursive_search(path):
    """
    Рекурсивно создаем список папок с файлами в них. Результаты добавляем в 
    список состоящий из именованных списков. 
    namedtuple('PathFiles', ['path', 'files_list'])
    """
    logging.info('Start recursive search:')
    path_and_files_list = []
    for path, dirs, files in os.walk(path):
        path_and_files_list.append(PathAndFiles(path, files))
        logging.info(f'    Path and file list append: {path} {files}')
    if args.v:
        logging.info('Complete recursive search')
    return path_and_files_list


def not_recursive_search(path):
    """
    Ищем все файлы в папке, так как поиск не рекурсивный исключаем 
    из результата папки.
    """
    file_list = []
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            file_list.append(file)
    path_and_files_list = [PathAndFiles(path, file_list),]
    return path_and_files_list


def filter_files_by_regex(path_and_files_list, regex):
    # Фильтрует списки файлов на соотвествие регулярному выражению
    new_list = []
    for path_and_files in path_and_files_list:
        abs_path_list = glob.glob(os.path.join(path_and_files.path, regex))
        match_files_list = [os.path.basename(fh) for fh in abs_path_list]
        new_list.append(PathAndFiles(path_and_files.path, match_files_list))
    
    return new_list


def rename_wildcard(path_and_files_list, rename_pattern):
    for path_and_files in path_and_files_list:
        path = path_and_files.path
        for fh in path_and_files.files_list:
            name = fh.rsplit('.')[0]
            new_name = rename_pattern.replace('*', name)
            abs_path_old = os.path.join(path, fh)
            abs_path_new = os.path.join(path, new_name)
            os.rename(abs_path_old, abs_path_new)
            print(f'Rename [{path}]:')
            print(f'    {fh} -----> {new_name}')


def main(args):
    if args.v:
        logging.getLogger().setLevel(logging.INFO)
    logging.info(f'Получены аргументы {args}')
    path_to_search = parse_arg_path(args.path)
    

    if args.R:
        path_and_files_list = recursive_search(path_to_search)
    else:
        path_and_files_list = not_recursive_search(path_to_search)

    print(path_and_files_list)
    if args.r:
        path_and_files_list = filter_files_by_regex(path_and_files_list, args.r)
        print(f'Take regex {args.r}\nResult: {path_and_files_list}')

    # Если в паттерне присутствует * и расширение файла то, меняем расширения
    # if match('.*?\*\.\S+', args.rename_pattern):
    #     rename_wildcard(path_and_files_list, args.rename_pattern)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Description argumentparser')
    parser.add_argument(
        'path', 
        action='store', 
        help='Path to directory with files to rename'
    )
    parser.add_argument(
        'rename_pattern', 
        action='store', 
        help='Pattern to rename files'
    )
    parser.add_argument(
        '-r', 
        action='store', 
        default=False, 
        help='Pattern to match'
    )
    parser.add_argument(
        '-R', 
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
    main(args)