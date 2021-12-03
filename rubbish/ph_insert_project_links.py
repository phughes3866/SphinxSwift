import sublime, sublime_plugin, re, os, sys, string
# from . import ph_parse_obj_inv as invparser
from . import ph_plugin_utils as ph_utils

site_paths=['/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
for this_path in site_paths:
    if this_path not in sys.path:
        sys.path.append(this_path)

# simple context manager (https://stackoverflow.com/questions/17211078/how-to-temporarily-modify-sys-path-in-python)
class add_sys_path():
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            pass

def borrow_intersphinx_mapping(projdir='/fictitious/placeholder/dir'):
    commondata_dir = os.path.normpath(os.path.join(projdir, '../commondata'))
    with add_sys_path(commondata_dir):
    	try:
    		from intersphinx_map import intersphinx_mapping
    	except:
    		intersphinx_mapping = False
    return intersphinx_mapping

class InsertLocProjectLinksOld(sublime_plugin.TextCommand):
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
        got_objinv_file = ""
        if invtype in ['label', 'doc', 'term']: # These identify the section of the objects.inv file to crawl for links
            variables = self.view.window().extract_variables ()
            cur_project_dir = os.path.normpath(variables["folder"])
            project_dir_basename = os.path.basename(cur_project_dir)
            intersphinx_mapping = borrow_intersphinx_mapping(cur_project_dir)
            if intersphinx_mapping:
	            cur_project_intersphinx_label = ph_utils.get_intersphinx_label(intersphinx_mapping, project_dir_basename)
	            got_objinv_file = ph_utils.get_objinv_from_intersphinx_map(intersphinx_mapping, cur_project_intersphinx_label)
	            if got_objinv_file:
	                sublime.status_message("Parsing {}".format(got_objinv_file))
	                self.datalist, self.displaylist = ph_utils.fetch_inv_lists(got_objinv_file, invtype)
	                if len(self.datalist) == len(self.displaylist):
	                    sublime.active_window().show_quick_panel(
	                        self.displaylist, 
	                        self.on_done
	                    )
	            else:
	                sublime.error_message("sphinx-swift is unable to locate an objects.inv file for the {} project".format(cur_project_dir))
            else:
                sublime.error_message("sphinx-swift: intersphinx_map.py does not exist in the commondata dir")
        else:
            sublime.error_message("Oops. Programming error. No invtype var provided to fn:InsertLocProjectLinks")


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
        cur_project_dir = os.path.normpath(variables["folder"])
        project_dir_basename = os.path.basename(cur_project_dir)
        intersphinx_map = borrow_intersphinx_mapping(cur_project_dir)
        # intersphinx_map = ph_utils.get_intersphinx_mapping()
        cur_project_intersphinx_label = ph_utils.get_intersphinx_label(intersphinx_map, project_dir_basename)
        loc_project = True if cur_project_intersphinx_label.startswith('loc') else False
        # print("cur proj label: {}".format(cur_project_intersphinx_label))
        for shortname, data in intersphinx_map.items():
            # print("shortname: {}".format(shortname))
            proceed = True if loc_project or ( not loc_project and not shortname.startswith('loc')) else False
            if proceed:
                found_inv_file = ph_utils.get_objinv_from_intersphinx_map(intersphinx_map, shortname)
                if found_inv_file:
                    gen_prefix = '(cur)' if shortname == cur_project_intersphinx_label else shortname
                    datal, displ = ph_utils.fetch_inv_lists(found_inv_file, display_prefix=gen_prefix)
                    self.datalist += datal
                    self.displaylist += displ
        # add our local data to the end of the list as this is probably less important under the current project-suite lookup 
        self.datalist += localdatal
        self.displaylist += localdispl
        sublime.active_window().show_quick_panel(
            self.displaylist, 
            self.on_done
        )
