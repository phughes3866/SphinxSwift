import sublime, sublime_plugin, os
from . import ph_plugin_utils as ph_utils

class OpenHtmlPageCommand(sublime_plugin.TextCommand):
    """
    When editing an rst page this command will open a browser and set it to view the associated
    html file in the build directory. This command takes 1 param (testbuild_not_live)
    if 'testbuild_not_live' equates to false (the default) the 'live' '_build' directory will be the target
    if 'testbuild_not_live' equates to true then the '_testbuild' directory will be the target
    """
    def run(self, edit, testbuild_not_live=False):
        args = {}
        variables = self.view.window().extract_variables()
        # Get sphinx-swift specifig project settings from active sublime project file
        ss_proj_data = ph_utils.get_project_settings("sphinx-swift")
        # print(ss_proj_data)
        base_url = ""
        if ss_proj_data: # There are sphinx-swift settings in the current project file, try to extract our base_url value from them
            if testbuild_not_live:
                base_url = ss_proj_data.get("testhtml_baseurl")
            else:
                base_url = ss_proj_data.get("livehtml_baseurl")
        if not base_url: # values not set by project, set to the default
            if testbuild_not_live:
                base_url = os.path.join(variables["folder"], "_testbuild/html")
            else:
                base_url = os.path.join(variables["folder"], "_build/html")

        dir_stub = os.path.relpath(variables["file_path"], variables["folder"])
        if dir_stub == '.':
            dir_stub = ''
        htmlfile_rootrel = os.path.join(dir_stub, variables["file_base_name"] + '.html')
        htmlfile_abs = os.path.join(base_url, htmlfile_rootrel)
        args["shell_cmd"] = "{} {} \"{}\"".format ("chromium",
                                                    "--incognito -open",
                                                   htmlfile_abs)
        self.view.window().run_command ("exec", args)
