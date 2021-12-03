# import ast
# import _ast
# import re
# import os
# import sublime, sublime_plugin




# def get_variables(node):
#     variables = set()
#     var_dict = {}
#     if hasattr(node, 'body'):
#         for subnode in node.body:
#             variables |= get_variables(subnode)
#     elif isinstance(node, _ast.Assign):
#         for name in node.targets:
#             if isinstance(name, _ast.Name):
#                 variables.add(name.id)
#     return variables

# def get_rst_epilog(filename):
#         # \s*rst_epilog\s+=\s+\"\"\"     # rst_epilog var start
#         # (?P<stuff>.*)                  # contents
#         # \"\"\"                         # end of docstring var
#     pattern = re.compile(r"""
#         ^rst_epilog\s+[\+=]+\s+\"\"\"     # rst_epilog var start
#         (?P<stuff>.*?)\"\"\"
#         """, re.VERBOSE | re.MULTILINE | re.DOTALL)
#     with open(filename, 'r') as ifile:
#         # Read file object to string
#         text = ifile.read()
#     # for match in pattern.finditer(text):
#     #     return match.group(1)
#     found = re.search(pattern, text)
#     if found:
#         return found.group('stuff')
#     return None

# def get_rst_replace_dict(parsestr):
#     pattern_repl = re.compile(r"""
#         ^\.\.\s+
#         \|(?P<short>.*)\|
#         \s+replace::\s+
#         (?P<long>.*)$
#         """, re.VERBOSE | re.MULTILINE)
#     # r = re.compile(r'\.\.\s+\|(?P<short>.*)\|\s+replace::\s+(?P<long>.*)$', re.Multiline)
#     # found = [m.groupdict() for m in r.finditer(parsestr)]
#     # found = [m.groupdict() for m in r.finditer(parsestr)]
#     return dict(re.findall(pattern_repl, parsestr))

# def get_rst_link_dict(parsestr):
#     pattern_link = re.compile(r"""
#         ^\.\.\s+
#         \_(?P<linktext>.*?):
#         \s+(?P<link>.*)$
#         """, re.VERBOSE | re.MULTILINE)
#     # r = re.compile(r'\.\.\s+\|(?P<short>.*)\|\s+replace::\s+(?P<long>.*)$', re.Multiline)
#     # found = [m.groupdict() for m in r.finditer(parsestr)]
#     # found = [m.groupdict() for m in r.finditer(parsestr)]
#     return dict(re.findall(pattern_link, parsestr))




