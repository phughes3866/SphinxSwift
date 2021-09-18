import ast, _ast
import os, sys, re, zlib
import sublime, sublime_plugin

sphinx_swift_settings_file_variables = ["command_path", "extra_sphinx_conf_files", "intersphinx_map_file", "bib_ref_file"]

#*************************************************
#
# file manipulation utilities
#
#*************************************************

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath: # program's location has been specified
        if is_exe(program):
            return program
    else: # program's location not given
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def to_abs_path(rootdir, relative_stub):
    # add trailing slash to rootdir if not already there
    absrootdir = os.path.join(rootdir, '')
    return os.path.abspath(absrootdir+relative_stub)

def safe_eval_var_from_file(mod_path, variable, default=None, *, raise_exception=False):
    # PH - not currently using this
    # Had some success with it for reading single python variables from long python files
    ModuleType = type(ast)
    with open(mod_path, "r", encoding='UTF-8') as file_mod:
        data = file_mod.read()

    try:
        ast_data = ast.parse(data, filename=mod_path)
    except:
        if raise_exception:
            raise
        print("Syntax error 'ast.parse' can't read %r" % mod_path)
        import traceback
        traceback.print_exc()
        ast_data = None

    if ast_data:
        for body in ast_data.body:
            if body.__class__ == ast.Assign:
                if len(body.targets) == 1:
                    if getattr(body.targets[0], "id", "") == variable:
                        try:
                            return ast.literal_eval(body.value)
                        except:
                            if raise_exception:
                                raise
                            print("AST error parsing %r for %r" % (variable, mod_path))
                            import traceback
                            traceback.print_exc()
    return default


# Example use, read from ourself :)
# that_variable = safe_eval_var_from_file(__file__, "this_variable")
# this_variable = {"Hello": 1.5, b'World': [1, 2, 3], "this is": {'a set'}}
# assert(this_variable == that_variable)

#*************************************************
#
# sublime text interaction utilities
#
#*************************************************

class InsertMyText(sublime_plugin.TextCommand):
    def run(self, edit, args):
        # inserts args['text'] at current cursor position
        # https://forum.sublimetext.com/t/chage-hello-world-to-insert-at-cursor-position/9270/1
        self.view.insert(edit, self.view.sel()[0].begin(), args['text'])

#*************************************************
#
# Utilities for project and plugin settings loading
#
#*************************************************

def get_project_settings(for_this_plugin):
    proj_data = sublime.active_window().project_data()
    if not proj_data:
        return {}
    try:
        proj_setts = proj_data['settings'][for_this_plugin]
        return proj_setts
    except KeyError:
        return {}

def get_plugin_settings(this_plugin_settings_file, these_settings, loc_proj_overrides=False):
    """
    Return a dictionary of settings from the .sublime-settings filename passed in this_plugin_settings_file
    The settings returned are those that match the 'these_settings' list of varnames
    If loc_proj_overrides is True then a subsequent check for matching varname settings is done in the active sublime project file
    The section of the sublime project file consulted is ["settings"]["plugin_name"] where plugin_name is this_plugin_settings_file minus the .sublime-settings extension
    """
    end_dict = {}
    settings = sublime.load_settings(this_plugin_settings_file)
    for varname in these_settings:
        end_dict[varname] = settings.get(varname)
    if loc_proj_overrides:
        plugin_name = this_plugin_settings_file[0:this_plugin_settings_file.find('.')]
        proj_settings = get_project_settings(plugin_name)
        if proj_settings:
            for proj_varname in these_settings:
                proj_varvalue = proj_settings.get(proj_varname, None) 
                if not proj_varvalue is None:
                    # print("updating {}".format(proj_varname))
                    end_dict[varname] = proj_varvalue
    return end_dict


#*******************************************************************
#
# Various reST parsing utilities
#
#*******************************************************************

def get_refs_from_file(filename):
    # opens file with std rst refs and parses it into a dict of 2 part dicts (cit / ref)
    # pattern for matching in target filename is ".. [author_yr] Author, 1966 Great Book"
    pattern = re.compile(r"""
        ^\.\.\s+\[
        (?P<cit>.*?)\]\s+
        (?P<ref>.*)$
        """, re.VERBOSE | re.MULTILINE)
    with open(filename, 'r') as reffile:
        # Read file object to string
        text = reffile.read()
    # for match in pattern.finditer(text):
    #     return match.group(1)
    found = re.findall(pattern, text)
    if found:
        return dict(found)
    return None

def get_variables(node):
    variables = set()
    var_dict = {}
    if hasattr(node, 'body'):
        for subnode in node.body:
            variables |= get_variables(subnode)
    elif isinstance(node, _ast.Assign):
        for name in node.targets:
            if isinstance(name, _ast.Name):
                variables.add(name.id)
    return variables

def get_rst_epilog(filename):
        # \s*rst_epilog\s+=\s+\"\"\"     # rst_epilog var start
        # (?P<stuff>.*)                  # contents
        # \"\"\"                         # end of docstring var
    pattern = re.compile(r"""
        ^rst_epilog\s+[\+=]+\s+\"\"\"     # rst_epilog var start
        (?P<stuff>.*?)\"\"\"
        """, re.VERBOSE | re.MULTILINE | re.DOTALL)
    with open(filename, 'r') as ifile:
        # Read file object to string
        text = ifile.read()
    # for match in pattern.finditer(text):
    #     return match.group(1)
    found = re.search(pattern, text)
    if found:
        return found.group('stuff')
    return None

def get_rst_replace_dict(parsestr):
    pattern_repl = re.compile(r"""
        ^\.\.\s+
        \|(?P<short>.*)\|
        \s+replace::\s+
        (?P<long>.*)$
        """, re.VERBOSE | re.MULTILINE)
    # r = re.compile(r'\.\.\s+\|(?P<short>.*)\|\s+replace::\s+(?P<long>.*)$', re.Multiline)
    # found = [m.groupdict() for m in r.finditer(parsestr)]
    # found = [m.groupdict() for m in r.finditer(parsestr)]
    return dict(re.findall(pattern_repl, parsestr))

# PH: Jun 2020 - Don't need this as the link entries in rst_epilog are all pointed to by the replace entries (and are not replacements themselves)
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

#****************************************************************************
#
# The following utilities perform queries / manipulation on the intersphinx_mapping dictionary
#
#****************************************************************************

def get_intersphinx_mapping():
    """
    Finds the file in which intersphinx_mapping is defined (same one as used by intersphinx itself)
    imports this file as a module and then returns the resultant intersphinx_mapping dictionary
    """
    settings = get_plugin_settings("sphinx-swift.sublime-settings", sphinx_swift_settings_file_variables, True)
    print(settings)
    inv_map_source = settings.get("intersphinx_map_file", "")
    if not inv_map_source:
        sublime.error_message("Unable to find [intersphinx_map_file] setting in sphinx-swift.sublime-settings")
        return
    the_path, the_file = os.path.split(inv_map_source)
    sys.path.append(the_path)
    # import the file without the .py extension name according to import syntax
    mapmod = __import__(os.path.splitext(the_file)[0])
    return mapmod.intersphinx_mapping

def get_intersphinx_label(is_map, cur_project_dir):
    """
    The top set of keys in the intersphinx map are shortname labels that intersphinx uses to identify different projects
    A sub-tuple in the dict (here invdata[1]) is a list of possible locations for the project's objects.inv file 
    This utility checks all the locations (only filepath ones) to see if the current project dir name is in the filepath
    If a match is found this immediately returns the shortname label, which can be used to locate current project data in the intersphinx map
    This is a 'good guess' to determine which intersphinx entry relates to the current project
    """
    for shortname, invdata in is_map.items():
        for invpath in invdata[1]:
            if invpath and not invpath.startswith("http"):
                if cur_project_dir in invpath:
                    return shortname
    return None

def get_objinv_from_intersphinx_map(the_map, the_key, normalising_path):
    """
    Return a fully qualified filename string for the first existing filename found in the_key section of the_map (intersphinx_mapping)
    Return None if no existing files are found 
    """
    for filestr in the_map[the_key][1]:
        # print("filestr: {}".format(filestr))
        objects_inv_fileloc = os.path.normpath(os.path.join(normalising_path, filestr))
        if os.path.exists(objects_inv_fileloc):
            return objects_inv_fileloc
    return None  


# ************************************************************
#
# The following utils parse sphinx's 'objects.inv' files seeking out different types of link information
# These were borrowed from the intersphinx sphinx plugin, and slightly modified
#
# ************************************************************
def read_inventory_v2(f, section_name="", is_prefix="", for_cur_project=False, bufsize=16*1024):
    invdata = {}
    datalist = []
    displaylist = []
    line = f.readline()
    projname = line.rstrip()[11:].decode('utf-8')
    line = f.readline()
    version = line.rstrip()[11:].decode('utf-8')
    line = f.readline().decode('utf-8')
    if 'zlib' not in line:
        sublime.error_message("Badly formatted objects.inv - no zlib line")

    def read_chunks():
        decompressor = zlib.decompressobj()
        for chunk in iter(lambda: f.read(bufsize), b''):
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def split_lines(iter):
        buf = b''
        for chunk in iter:
            buf += chunk
            lineend = buf.find(b'\n')
            while lineend != -1:
                yield buf[:lineend].decode('utf-8')
                buf = buf[lineend+1:]
                lineend = buf.find(b'\n')
        assert not buf

    # main
    is_prefix_plus_colon = is_prefix + ":"
    if is_prefix or for_cur_project: # we're collecting label and doc entries for cross project references
        section_name = ""
        if for_cur_project:
            is_prefix_plus_colon = ""

    for line in split_lines(read_chunks()):
        # be careful to handle names with embedded spaces correctly
        m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(\S+)\s+(\S+)\s+(.*)',
                     line.rstrip())
        if not m:
            continue
        name, type, prio, location, dispname = m.groups()
        if type == 'py:module' and type in invdata and \
            name in invdata[type]:  # due to a bug in 1.1 and below,
                                    # two inventory entries are created
                                    # for Python modules, and the first
                                    # one is correct
            continue
            
        # adjust any shorthand entries
        if location.endswith(u'$'):
            location = location[:-1] + name
        # location = join(uri, location)
        if dispname == "-":
            dispname = name

        invdata.setdefault(type, {})[name] = (projname, version,
                                              location, dispname)
        if section_name: # a section_name has been supplied for a local proj. search
            if type == "std:{}".format(section_name):
                if section_name == "label":
                    datalist.append(":ref:`${{1:{}}}` ".format(name))
                    displaylist.append("ref: {} ({})".format(dispname, name))
                elif section_name == "doc":
                    datalist.append(":doc:`${{1:{}}}` ".format(name))
                    displaylist.append("doc: {} ({})".format(dispname, name))
                elif section_name == "term":
                    datalist.append(":term:`${{1:{}}}` ".format(name))
                    displaylist.append("term: {} ({})".format(dispname, name))
        else: # this is part of a project group scan (intersphinx based), collect label(ref) and doc references
            bare_type = type[4:] # strip 'std:'
            if bare_type == "label":
                datalist += [":ref:`${{1:{}{}}}` ".format(is_prefix_plus_colon, name)]
                displaylist += ["{}ref: {} ({})".format(is_prefix_plus_colon, dispname, name)]
            if bare_type == "doc":
                datalist += [":doc:`${{1:{}{}}}` ".format(is_prefix_plus_colon, name)]
                displaylist += ["{}doc: {} ({})".format(is_prefix_plus_colon, dispname, name)]


    # return invdata
    return datalist, displaylist

def fetch_inv_lists(invloc, section_name="", is_prefix="", for_cur_project=False):
    """
    Parse a sphinx objects.inv file on the local filesystem at invloc
    return 2 x lists with data/display entries for the identified section of objects.inv
    return empty lists if there are errors processing the objects.inv file
    """
    try:
        f = open(invloc, 'rb')
    except Exception as err:
        return [], []
    try:
        line = f.readline().rstrip().decode('utf-8')
        try:
            # if line == '# Sphinx inventory version 1':
            #     invdata = read_inventory_v1(f, uri, join)
            if line == '# Sphinx inventory version 2':
                datalist, displaylist = read_inventory_v2(f, section_name, is_prefix, for_cur_project)
            else:
                raise ValueError
            f.close()
        except ValueError:
            f.close()
            raise ValueError('unknown or unsupported inventory version')
    except Exception as err:
        sublime.message_dialog("Unable to parse intersphinx inventory [{}] due to {}: {}".format(invloc, err.__class__.__name__, err))
        return [], []
    else:
        return datalist, displaylist