import argparse
import difflib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def file_mtime(path):
    time = datetime.fromtimestamp(os.stat(path).st_mtime, timezone.utc)
    time = time.strftime("%d.%m.%Y %H:%M:%S")
    return time

def make_html(diff):
    # COLORS
    green = "#deffde"
    red = "#ffdede"

    # HTML
    html_head = """<table style="font-size: 18px; border: 1px solid black;">"""
    html_end = """\n</table>"""
    html_table_row = []

    for line in list(diff):
        if line.startswith(" "):
            html_table_row.append(f'<tr><td><pre>{line}</pre></td><tr>')
        elif line.startswith("-"):
            html_table_row.append(f'<tr><td bgcolor="{red}"><pre>{line}</pre></td><tr>')
        elif line.startswith("+"):
            html_table_row.append(f'<tr><td bgcolor="{green}"><pre>{line}</pre></td><tr>')

    html = html_head + '\n'.join(html_table_row) + html_end
    return html

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--context', action='store_true', default=False,
                        help='Produce a context format diff')
    parser.add_argument('-u', '--unified', action='store_true', default=False,
                        help='Produce a unified format diff (default)')
    parser.add_argument('-m', '--make-html', help='Produce HTML side by side diff '
                        '(can use -c and -l in conjunction)')
    parser.add_argument('-a', '--all', action='store_true', default=False,
                        help='Produce all lines in diff')
    parser.add_argument('-l', '--lines', type=int, default=3,
                        help='Set number of context lines (default 3)')
    parser.add_argument('old_file')
    parser.add_argument('new_file')
    args = parser.parse_args()

    old_file = Path(args.old_file)
    new_file = Path(args.new_file)
    
    context_lines_count = args.lines

    old_file_date = file_mtime(old_file)
    new_file_date = file_mtime(new_file)
    
    with open(new_file) as ff:
        old_file_text = ff.readlines()
    with open(old_file) as tf:
        new_file_text = tf.readlines()

    if args.context:
        diff = difflib.context_diff(old_file_text, new_file_text, old_file.name, new_file.name, old_file_date, new_file_date, n=context_lines_count)
    elif args.all:
        diff = difflib.Differ.compare(old_file_text, new_file_text)
    else:
        diff = difflib.unified_diff(old_file_text, new_file_text, old_file.name, new_file.name, old_file_date, new_file_date, n=context_lines_count)

    if args.make_html:
        # default style
        # diff = difflib.HtmlDiff().make_file(old_file_text,new_file_text,old_file.name,new_file.name,context=options.c,numlines=context_lines_count)
        diff = make_html(diff)
        with open(args.make_html, 'w', encoding='utf8') as fh:
            fh.write(diff)
        return
    
    sys.stdout.writelines(diff)


if __name__ == "__main__":
    main()