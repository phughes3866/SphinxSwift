import re, os
import sublime, sublime_plugin
from . import ph_plugin_utils as ph_utils

# PH: Not using this code anymore
# It worked well but I found there were too many dependencies and it was all a bit clunky
# On the zotero side this code needs the 'Better Bibtex' plugin to open up a query port on localhost:23119
# On the Sphinx side the sphinxcontrib-bibtex extension was needed for the cite and bibliography directives
# As of Apr 2020 I'm now using CiteFromReferenceFileCommand (see below)
# This relies purely on rst citations.
# _ST3 = sublime.version() >= "3000"

# url = "http://localhost:23119/better-bibtex/cayw"

# if _ST3:
#     from urllib import request

#     def request_key():
#         try:
#             res = request.urlopen(url)
#         except:
#             sublime.status_message("Zotero Bibtex Plugin Not Responding. Is Zotero open?")
#             return ""
#         rtncode = res.getcode()
#         # if not rtncode == 200
#         return res.read().decode()
# else:
#     import urllib2
#     req = urllib2.Request(url)

#     def request_key():
#         return urllib2.urlopen(req).read()

# class InsertZoteroCitationCommand(sublime_plugin.TextCommand):
#     def run(self, edit):
#         # invoke the url and get a response
#         # extract citation from response
#         cite_key = request_key()
#         if cite_key:
#             cite_key = ":cite:`{}` ".format(cite_key)
#             self.view.insert(edit, self.view.sel()[0].b, cite_key)



class CiteFromReferenceFileCommand(sublime_plugin.TextCommand):
    # """
    # Parses a file containing the sphinx projects bibliographic ref list
    # This can only be one file so only a single bibliography is supported
    # The name of the file must be set in sphinx-swift settings as "bibliography_rst_file"
    # The utility then constructs a dictionary of cit / ref pairs from the parsed bibliography
    # Presents to user (in sublime's quick panel) a list of references
    # If the user selects one the citation is put in at the cursor position
    # """
    def on_done(self, index):
        if index == -1:
            # noop; nothing was selected 
            # e.g. the user pressed escape
            return 

        # sublime.message_dialog(selected_value)
        self.view.run_command(
                    "insert_my_text", {"args":
                    {'text': self.insert_list[index]}})

    def run(self, edit):
        # reads file bib_references.rst from root of project
        # presents a list of references from that file
        # inserts citation for selected reference
        #
        # Old - no longer get bib file from plugin settings, but from project-settings - more tailorable
        # settings = sublime.load_settings("sphinx-swift.sublime-settings")
        # bib_rst = settings.get("bibliography_rst_file", "")
        self.insert_list = []
        self.display_list = []
        variables = self.view.window().extract_variables ()
        proj_name = variables.get("project_name", "oh-dear-no-project-name-defined")
        # print(variables)
        # Get sphinx-swift specifig project settings from active sublime project file
        ss_proj_data = ph_utils.get_project_settings("sphinx-swift")
        # print(ss_proj_data)
        if ss_proj_data:
            ref_file = ss_proj_data.get("bib_ref_file")
            if not ref_file:
                sublime.error_message("No bibliography file referenced in sphinx-swift section of settings file {}. Cannot locate bibliography file.".format(proj_name))
                return
        else:
            sublime.error_message("Cannot find settings/sphinx-swift section in project file {}. Impossible to locate bibliography file.".format(proj_name))
            return
        # now we know we have a reference file name to work with
        fq_ref_file = ph_utils.to_abs_path(variables["folder"], ref_file)
        if not os.path.isfile(fq_ref_file):
            sublime.error_message("Missing sphinx-swift bibliography file: {}".format(fq_ref_file))
        else:
            parse_result = ph_utils.get_refs_from_file(fq_ref_file)
            if not parse_result:
                sublime.error_message("No references found in {}".format(fq_ref_file))
            else:
                for cit, ref in parse_result.items():
                    self.insert_list.append("[{}]_ ".format(cit))
                    self.display_list.append("[{}] = {}".format(cit, ref))
                sublime.status_message("{} references found".format(len(parse_result)))
                sublime.active_window().show_quick_panel(
                    self.display_list, 
                    self.on_done
                )

class InsertSphinxSubstitutionCommand(sublime_plugin.TextCommand):
    """
    Present user with a list of sphinx reST |substitutions| which are valid in the current sphinx project. Insert the chosen one at current cursor pos
    1. compile list of substitutions - some standard ones, plus we must parse conf.py and extract those in the rst_epilog variable
    2. parse any other files that contain rst_epilog additions that are used by the project (these files are in a list in the sphinx-swift settings)
    2. show the |substitutions| plus their expanded text to the user in a quick panel
    3. insert the chosen |substitution| at the current cursor position
    """
    def on_done(self, index):
        if index == -1:
            # noop; nothing was selected 
            # e.g. the user pressed escape
            return 

        # sublime.message_dialog(selected_value)
        self.view.run_command(
                    "insert_my_text", {"args":
                    {'text': self.insert_list[index]}})

    def run(self, edit):
        settings = sublime.load_settings("sphinx-swift.sublime-settings")
        extra_sources = settings.get("extra_sphinx_conf_files", [])
        # First define some standard Sphinx replacements
        # Note: 'insert_list' is the simple |substitution| to insert
        #       'display_list' contains |substitution| plus expanded text, this is for the quick_panel
        self.insert_list = ["|release| ",
                            "|version| ",
                            "|today| "]
        self.display_list = ["|release| STD conf.py: full version str e.g. 2.5.2b3",
                            "|version| STD conf.py: major + minor versions e.g. 2.5",
                            "|today| STD conf.py: today or fixed date"]
        repl_dict = {}
        # link_dict = {}
        variables = self.view.window().extract_variables () # load sublime's current path / file variables

        sphinx_rst_epilog_files = []
        sphinx_rst_epilog_files.append(os.path.join(variables["folder"],'conf.py'))
        for stub in extra_sources:
            sphinx_rst_epilog_files.append(ph_utils.to_abs_path(variables["folder"], stub))


        for rst_epilog_file in sphinx_rst_epilog_files:
            if not os.path.isfile(rst_epilog_file):
                sublime.error_message("No sphinx config file at project root.\n Missing: " + rst_epilog_file)
            else: # parse the 'rst_epilog' var in 'conf.py' for |substitutions|
                rst_epilog = ph_utils.get_rst_epilog(rst_epilog_file)
                if not rst_epilog:
                    sublime.status_message("No rst_epilog in {}".format(rst_epilog_file))
                else:
                    repl_dict = ph_utils.get_rst_replace_dict(rst_epilog)
                    if repl_dict:
                        for shorty, longy in repl_dict.items():
                            self.insert_list.append("|{}| ".format(shorty))
                            self.display_list.append("|{}| = {}".format(shorty, longy))
                    # link_dict = ph_utils.get_rst_link_dict(rst_epilog)
                    # if link_dict:
                    #     for name, link in link_dict.items():
                    #         if name in repl_dict:
                    #             self.insert_list.append("|{}|_ ".format(name))
                    #             self.display_list.append("|{}|_ named link for {}".format(name, link))
                    #         else:
                    #             self.insert_list.append("`{}`_ ".format(name))
                    #             self.display_list.append("{} - linked to {}".format(name, link))
        sublime.status_message("{} replacements loaded from {} rst_epilog locations".format(len(self.display_list) - 3, len(sphinx_rst_epilog_files)))
        # There will always be something to display as this routine inserts several of sphinx's own standard replacements
        sublime.active_window().show_quick_panel(
            self.display_list, 
            self.on_done
        )

