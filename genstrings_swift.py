import re
import os
import io
import argparse
from collections import namedtuple

OUTPUT_ENCODING = 'utf-16'
OUTPUT_LINE_PATTERN = u'/* {comment} */\n"{key}" = "{value}";\n\n'

string_pattern = re.compile('NSLocalizedString\(\s*(.+)\)', re.MULTILINE)
empty_pattern = re.compile('"([^"]*)"')
key_pattern = re.compile('key:\s*"([^"]*)"')
value_pattern = re.compile('value:\s*"([^"]*)"')
comment_pattern = re.compile('comment:\s*"([^"]*)"')
var_pattern = re.compile('%(.)')
String = namedtuple('String', ['key', 'value', 'comment'])


class GenStrings:

    def __init__(self):
        self.args = self.read_cmd()

    @staticmethod
    def read_cmd():
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--output',
                            help='Command output directory',
                            default='.')
        parser.add_argument('-f', '--filename',
                            help='Command output filename',
                            default='Localizable_swift.strings')
        parser.add_argument('-e', '--emptynote',
                            help='Comment left if none provided in code',
                            default=u'No comment provided by engineer.')
        parser.add_argument('filepaths',
                            help='file(s) to generate strings from',
                            type=argparse.FileType('r'),
                            nargs='+')
        args = parser.parse_args()
        return args

    @staticmethod
    def replace_vars(value):
        var_result = list(var_pattern.finditer(value))
        if len(var_result) > 1:
            for idx, result in enumerate(var_result):
                value = value.replace(result.group(0), '%{}${}'.format(idx + 1, result.group(1)), 1)
        return value

    def generate_string(self, params):
        key = ''
        key_result = key_pattern.search(params)

        if key_result:
            key = key_result.group(1)
        else:
            key_result = empty_pattern.match(params)
            if key_result:
                key = key_result.group(1)
            else:
                print("can't resolve parameters for %s" % key_result.group(0))

        value_result = value_pattern.search(params)
        if value_result:
            value = value_result.group(1)
        else:
            value = key
        value = self.replace_vars(value)

        comment_result = comment_pattern.search(params)
        if comment_result:
            comment = comment_result.group(1) or self.args.emptynote
        else:
            comment = self.args.emptynote

        return String(key, value, comment)

    def grep_file(self):
        strings = []
        for filepath in self.args.filepaths:
            with io.open(filepath.name, encoding='utf-8') as fp:
                content = fp.read()
                for match in string_pattern.finditer(content):
                    params = match.group(1)
                    string = self.generate_string(params)
                    strings.append(string)
        return strings

    def save_strings(self, strings):
        filepath = os.path.join(self.args.output, self.args.filename)
        with io.open(filepath, 'w', encoding=OUTPUT_ENCODING) as fp:
            output_lines = map(lambda s: OUTPUT_LINE_PATTERN.format(**s._asdict()), strings)
            fp.writelines(output_lines)


if __name__ == '__main__':
    gen = GenStrings()
    gen.save_strings(gen.grep_file())
