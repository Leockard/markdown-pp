# Copyright 2015 John Reese
# Licensed under the MIT license

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import re
from os import path

from MarkdownPP.Module import Module
from MarkdownPP.Transform import Transform


class Include(Module):
    """
    Module for recursively including the contents of other files into the
    current document using a command like `!INCLUDE "path/to/filename"`.
    Target paths can be absolute or relative to the file containing the command
    """

    includere = re.compile(r"^!INCLUDE\s+(?:\"([^\"]+)\"|'([^']+)')\s+({(.*?)})?$")

    # includes should happen before anything else
    priority = 0

    def transform(self, data):
        transforms = []

        linenum = 0
        for line in data:
            match = self.includere.search(line)
            if match:
                includedata = self.include(match)

                transform = Transform(linenum=linenum, oper="swap",
                                      data=includedata)
                transforms.append(transform)

            linenum += 1

        return transforms

    def _process_args(self, args):
        """Extract keyword: value template arguments from match group."""
        arg_list = args.split(",")
        arg_tuples = [[s.strip() for s in arg.split(":")] for arg in arg_list]
        return dict(arg_tuples)

    def include(self, match, pwd=""):
        if match.group(1) is None:
            filename = match.group(2)
        else:
            filename = match.group(1)

        if not path.isabs(filename):
            filename = path.join(pwd, filename)

        # if path.isfile(filename):
        try:
            f = open(filename, "r")
            data = f.readlines()
            f.close()

            # recursively include file data
            linenum = 0
            for line in data:
                recmatch = self.includere.search(line)
                if recmatch:
                    dirname = path.dirname(filename)
                    data[linenum:linenum+1] = self.include(recmatch, dirname)

                linenum += 1

            # replace template keyword arguments
            if match.group(4) is None:
                args = {}
            else:
                args = self._process_args(match.group(4))

            for arg_name, arg_val in args.items():
                for linenum in range(len(data)):
                    argre = re.compile(r"{{\s*%s\s*}}" % arg_name)
                    data[linenum] = re.sub(argre, arg_val, data[linenum])

            return data

        except FileNotFoundError as exc:
            print(exc)

        return []
