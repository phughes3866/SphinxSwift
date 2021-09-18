import sublime, sublime_plugin, re, os, sys, string
# from . import ph_parse_obj_inv as invparser
from . import ph_plugin_utils as ph_utils

site_paths=['/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
for this_path in site_paths:
    if this_path not in sys.path:
        sys.path.append(this_path)

class InsertLocProjectLinks(sublime_plugin.TextCommand):
    """
    Builds a list of labels, docs, OR glossary terms from the current project by scanning sphinx's compiled objects.inv file
    Settings-wise this utility piggy-backs off the intersphinx plugin settings by reading the intersphinx_mapping dictionary to get a list of possible objects.inv locations on the local filesystem
    The links that are found are presented to the user in a quick panel where one can be selected to insert
    """
    def on_done(self, index):
        # callback function following quickpanel execution
        if index == -1:
            # noop; nothing was selected 
            # e.g. the user pressed escape
            return 
        args = {}
        args['contents'] = self.datalist[index]
        self.view.run_command('insert_snippet', args)

    def run(self, edit, invtype=None):
        kosher_inv_file = ""
        if invtype: # invtype should be 'label', 'doc', or 'term'. this identifies the section of the objects.inv file to crawl for links
            variables = self.view.window().extract_variables ()
            cur_project_dir = os.path.basename(os.path.normpath(variables["folder"]))
            intersphinx_map = ph_utils.get_intersphinx_mapping()
            cur_project_intersphinx_label = ph_utils.get_intersphinx_label(intersphinx_map, cur_project_dir)
            kosher_inv_file = ph_utils.get_objinv_from_intersphinx_map(intersphinx_map, cur_project_intersphinx_label, variables["folder"])
            if kosher_inv_file:
                sublime.status_message("Parsing {}".format(kosher_inv_file))
                self.datalist, self.displaylist = ph_utils.fetch_inv_lists(kosher_inv_file, invtype)
                if len(self.datalist) == len(self.displaylist):
                    sublime.active_window().show_quick_panel(
                        self.displaylist, 
                        self.on_done
                    )
            else:
                sublime.error_message("sphinx-swift is unable to locate an objects.inv file for the {} project".format(cur_project_dir))
        else:
            sublime.error_message("Oops. Programming error. No invtype var provided")


class InsertCrossProjectLinksCommand(sublime_plugin.TextCommand):
    """
    Builds a list of labels, docs, AND glossary terms from all projectes identified by intersphinx (via the intersphinx_mapping dictionary)
    Settings-wise this utility piggy-backs off the intersphinx plugin settings by reading the intersphinx_mapping dictionary to get a list of possible objects.inv locations on the local filesystem
    The links that are found are presented to the user in a quick panel where one can be selected to insert
    Local project links are placed at the end of the list as the user will probably have used the local link version of this util for local project links
    Note: Links are inserted into the rst in intersphinx style, so intersphinx will need to be active at build time
    """
    def on_done(self, index):
        if index == -1:
            # noop; nothing was selected 
            # e.g. the user pressed escape
            return 

        # sublime.message_dialog(selected_value)
        args = {}
        args['contents'] = self.datalist[index]
        self.view.run_command('insert_snippet', args)

    def run(self, edit):
        # initialise lists for construction of quickpanel display
        self.datalist = []
        self.displaylist = []
        localdatal = []
        localdispl = []
        variables = self.view.window().extract_variables ()
        cur_project_dir = os.path.basename(os.path.normpath(variables["folder"]))
        intersphinx_map = ph_utils.get_intersphinx_mapping()
        cur_project_intersphinx_label = ph_utils.get_intersphinx_label(intersphinx_map, cur_project_dir)
        # print("cur proj label: {}".format(cur_project_intersphinx_label))
        for shortname, data in intersphinx_map.items():
            # print("shortname: {}".format(shortname))
            kosher_inv_file = ph_utils.get_objinv_from_intersphinx_map(intersphinx_map, shortname, variables["folder"])
            if kosher_inv_file:
                if shortname == cur_project_intersphinx_label:
                    localdatal, localdispl = ph_utils.fetch_inv_lists(kosher_inv_file, for_cur_project=True)
                else:
                    datal, displ = ph_utils.fetch_inv_lists(kosher_inv_file, is_prefix=shortname)
                    self.datalist += datal
                    self.displaylist += displ
            else:
                sublime.error_message("Cannot locate inventory file for intersphinx [{}] items".format(shortname))
        # add our local data to the end of the list as this is probably less important under the current project-suite lookup 
        self.datalist += localdatal
        self.displaylist += localdispl
        sublime.active_window().show_quick_panel(
            self.displaylist, 
            self.on_done
        )
