import sublime, sublime_plugin, re, os, sys, string
# from . import ph_parse_obj_inv as invparser

site_paths=['/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
for this_path in site_paths:
    if this_path not in sys.path:
        sys.path.append(this_path)

class WrapSelectionAsRoleCommand(sublime_plugin.TextCommand):
    def on_done(self, index):
        if index == -1:
            # noop; nothing was selected 
            # e.g. the user pressed escape
            return 

        # sublime.message_dialog(selected_value)
        args = {}
        args['contents'] = self.insert_list[index]
        self.view.run_command('insert_snippet', args)

    
    def run(self, edit):
        def lbuild(display="", insertion=""):
            self.display_list.append(display)
            self.insert_list.append(insertion)

        # Main:
        self.insert_list = []
        self.display_list = []
        # term, ref, download, file, command, kbd, 
        lbuild(":abbr: on abbreviation", ":abbr:`$SELECTION (${1:Abbr Decode})`")
        lbuild(":command: a command", ":command:`$SELECTION$1`")
        lbuild(":file: a filename", ":file:`$SELECTION$1`")
        lbuild(":menuselection: e.g. Start --> Programs", ":menuselection:`$SELECTION${1: like:Start --> Programs}`")
        lbuild(":guilabel: e.g. &Cancel", ":guilabel:`$SELECTION${1: like:&Cancel}`")
        lbuild(":kbd: (keep keys separate)", ":kbd:`$SELECTION${1: like:Return}`")
        lbuild(":download: on filename itself", ":download:`$SELECTION$1`")
        lbuild(":download: on download desc", ":download:`$SELECTION <$1>`")
        lbuild(":rfc: request for comments", ":rfc:`$SELECTION$1`")
        lbuild(":term: on term itself", ":term:`$SELECTION$1`")
        lbuild(":term: on term desc", ":term:`$SELECTION <$1>`")
        lbuild(":ref: on ref", ":ref:`$SELECTION$1`")
        lbuild(":ref: on ref desc.", ":ref:`$SELECTION <$1>`")
        lbuild(":doc: on doc itself (shows title)", ":doc:`$SELECTION$1`")
        lbuild(":doc: on doc desc", ":doc:`$SELECTION <$1>`")
        sublime.active_window().show_quick_panel(
            self.display_list, 
            self.on_done
        )

class ConvertTextToRefLabelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        def str_from_title(title):
            translator = str.maketrans('', '', string.punctuation)
            barestr = title.translate(translator).strip().lower()
            return ".. _{}:\n\n".format(re.sub(r"\s+", '_', barestr))

        # Main:
        # Get selection(s)
        sel = self.view.sel();
        for s in sel:       
            if s.empty(): # expand to full line a cursor with no selection
                s = self.view.full_line(s)
            seltext = self.view.substr(s)
            new_ref_anchor = str_from_title(seltext)
            if new_ref_anchor:
                self.view.replace(edit, s, new_ref_anchor)      

    
# def get_intersphinx_mapping():
#     settings = sublime.load_settings("sphinx-swift.sublime-settings")
#     inv_map_source = settings.get("intersphinx_map_file", "")
#     if not inv_map_source:
#         sublime.error_message("Unable to find [intersphinx_map_file] setting in sphinx-swift.sublime-settings")
#         return
#     the_path, the_file = os.path.split(inv_map_source)
#     sys.path.append(the_path)
#     # import the file without the .py extension name according to import syntax
#     mapmod = __import__(os.path.splitext(the_file)[0])
#     return mapmod.intersphinx_mapping

# def get_intersphinx_label(is_map, cur_project_dir):
#     """
#     The top set of keys in the intersphinx map are shortname labels that intersphinx uses to identify different projects
#     A sub-tuple in the dict (here invdata[1]) is a list of possible locations for the project's objects.inv file 
#     This utility checks all the locations (only filepath ones) to see if the current project dir name is in the filepath
#     If a match is found this immediately returns the shortname label, which can be used to locate current project data in the intersphinx map
#     """
#     for shortname, invdata in is_map.items():
#         for invpath in invdata[1]:
#             if invpath and not invpath.startswith("http"):
#                 if cur_project_dir in invpath:
#                     return shortname
#     return None

# def get_objinv_from_intersphinx_map(the_map, the_key, normalising_path):
#     for filestr in the_map[the_key][1]:
#         print("filestr: {}".format(filestr))
#         objects_inv_fileloc = os.path.normpath(os.path.join(normalising_path, filestr))
#         if os.path.exists(objects_inv_fileloc):
#             return objects_inv_fileloc
#     return None    
    
    
# class GetObjInvCommand(sublime_plugin.TextCommand):
#     def on_done(self, index):
#         if index == -1:
#             # noop; nothing was selected 
#             # e.g. the user pressed escape
#             return 

#         # sublime.message_dialog(selected_value)
#         args = {}
#         args['contents'] = self.datalist[index]
#         self.view.run_command('insert_snippet', args)

#     def run(self, edit, invtype=None):
#         kosher_inv_file = ""
#         if invtype:
#             variables = self.view.window().extract_variables ()
#             cur_project_dir = os.path.basename(os.path.normpath(variables["folder"]))
#             intersphinx_map = get_intersphinx_mapping()
#             cur_project_intersphinx_label = get_intersphinx_label(intersphinx_map, cur_project_dir)
#             kosher_inv_file = get_objinv_from_intersphinx_map(intersphinx_map, cur_project_intersphinx_label, variables["folder"])
#             if kosher_inv_file:
#                 sublime.status_message("Parsing {}".format(kosher_inv_file))
#                 self.datalist, self.displaylist = invparser.fetch_inv_lists(kosher_inv_file, invtype)
#                 if len(self.datalist) == len(self.displaylist):
#                     sublime.active_window().show_quick_panel(
#                         self.displaylist, 
#                         self.on_done
#                     )
#             else:
#                 sublime.error_message("sphinx-swift is unable to locate an objects.inv file for the {} project".format(cur_project_dir))
#         else:
#             sublime.error_message("Oops. Programming error. No invtype var provided")





                    
        
