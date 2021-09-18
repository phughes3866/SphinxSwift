# # Utils to parse a sphinx objects.inv file (at html build root) and place its values in a dictionary
# # import time
# import zlib
# # import codecs
# import re
# import sublime, sublime_plugin

# def read_inventory_v2(f, section_name="", is_prefix="", for_cur_project=False, bufsize=16*1024):
#     invdata = {}
#     datalist = []
#     displaylist = []
#     line = f.readline()
#     projname = line.rstrip()[11:].decode('utf-8')
#     line = f.readline()
#     version = line.rstrip()[11:].decode('utf-8')
#     line = f.readline().decode('utf-8')
#     if 'zlib' not in line:
#         sublime.error_message("Badly formatted objects.inv - no zlib line")

#     def read_chunks():
#         decompressor = zlib.decompressobj()
#         for chunk in iter(lambda: f.read(bufsize), b''):
#             yield decompressor.decompress(chunk)
#         yield decompressor.flush()

#     def split_lines(iter):
#         buf = b''
#         for chunk in iter:
#             buf += chunk
#             lineend = buf.find(b'\n')
#             while lineend != -1:
#                 yield buf[:lineend].decode('utf-8')
#                 buf = buf[lineend+1:]
#                 lineend = buf.find(b'\n')
#         assert not buf

#     # main
#     is_prefix_plus_colon = is_prefix + ":"
#     if is_prefix or for_cur_project: # we're collecting label and doc entries for cross project references
#         section_name = ""
#         if for_cur_project:
#             is_prefix_plus_colon = ""

#     for line in split_lines(read_chunks()):
#         # be careful to handle names with embedded spaces correctly
#         m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(\S+)\s+(\S+)\s+(.*)',
#                      line.rstrip())
#         if not m:
#             continue
#         name, type, prio, location, dispname = m.groups()
#         if type == 'py:module' and type in invdata and \
#             name in invdata[type]:  # due to a bug in 1.1 and below,
#                                     # two inventory entries are created
#                                     # for Python modules, and the first
#                                     # one is correct
#             continue
            
#         # adjust any shorthand entries
#         if location.endswith(u'$'):
#             location = location[:-1] + name
#         # location = join(uri, location)
#         if dispname == "-":
#             dispname = name

#         invdata.setdefault(type, {})[name] = (projname, version,
#                                               location, dispname)
#         if section_name: # a section_name has been supplied for a local proj. search
#             if type == "std:{}".format(section_name):
#                 if section_name == "label":
#                     datalist.append(":ref:`${{1:{}}}` ".format(name))
#                     displaylist.append("ref: {} ({})".format(dispname, name))
#                 elif section_name == "doc":
#                     datalist.append(":doc:`${{1:{}}}` ".format(name))
#                     displaylist.append("doc: {} ({})".format(dispname, name))
#                 elif section_name == "term":
#                     datalist.append(":term:`${{1:{}}}` ".format(name))
#                     displaylist.append("term: {} ({})".format(dispname, name))
#         else: # this is part of a project group scan (intersphinx based), collect label(ref) and doc references
#             bare_type = type[4:] # strip 'std:'
#             if bare_type == "label":
#                 datalist += [":ref:`${{1:{}{}}}` ".format(is_prefix_plus_colon, name)]
#                 displaylist += ["{}ref: {} ({})".format(is_prefix_plus_colon, dispname, name)]
#             if bare_type == "doc":
#                 datalist += [":doc:`${{1:{}{}}}` ".format(is_prefix_plus_colon, name)]
#                 displaylist += ["{}doc: {} ({})".format(is_prefix_plus_colon, dispname, name)]


#     # return invdata
#     return datalist, displaylist

# def fetch_inv_lists(invloc, section_name="", is_prefix="", for_cur_project=False):
#     """
#     Parse a sphinx objects.inv file on the local filesystem at invloc
#     return 2 x lists with data/display entries for the identified section of objects.inv
#     return empty lists if there are errors processing the objects.inv file
#     """
#     try:
#         f = open(invloc, 'rb')
#     except Exception as err:
#         return [], []
#     try:
#         line = f.readline().rstrip().decode('utf-8')
#         try:
#             # if line == '# Sphinx inventory version 1':
#             #     invdata = read_inventory_v1(f, uri, join)
#             if line == '# Sphinx inventory version 2':
#                 datalist, displaylist = read_inventory_v2(f, section_name, is_prefix, for_cur_project)
#             else:
#                 raise ValueError
#             f.close()
#         except ValueError:
#             f.close()
#             raise ValueError('unknown or unsupported inventory version')
#     except Exception as err:
#         sublime.message_dialog("Unable to parse intersphinx inventory [{}] due to {}: {}".format(invloc, err.__class__.__name__, err))
#         return [], []
#     else:
#         return datalist, displaylist