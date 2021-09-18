"""
A sublime text plugin for converting plain restructured text into an underscore separated reference anchor:
---------------------------------------------------------------
If no text is selected select cursor line.
With selected text: Strip punctuation, convert to lower case, replace space/tab with underscore and set as a restructured text reference anchor directive.
"""
# import sublime, sublime_plugin, re, os, sys, string

# site_paths=['/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
# for this_path in site_paths:
#     if this_path not in sys.path:
#         sys.path.append(this_path)

# class CreateRstRefFromTitleCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         def str_from_title(title):
#             translator = str.maketrans('', '', string.punctuation)
#             barestr = title.translate(translator).strip().lower()
#             return ".. _{}:\n\n".format(re.sub(r"\s+", '_', barestr))

#         # Main:
#         # Get selection(s)
#         sel = self.view.sel();
#         for s in sel:       
#             if s.empty(): # expand to full line a cursor with no selection
#                 s = self.view.full_line(s)
#             seltext = self.view.substr(s)
#             new_ref_anchor = str_from_title(seltext)
#             if new_ref_anchor:
#                 self.view.replace(edit, s, new_ref_anchor)


