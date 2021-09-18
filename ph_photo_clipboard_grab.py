import sublime, sublime_plugin, re, os, sys, string
import subprocess, shlex
from . import ph_plugin_utils as ph_utils

site_paths=['/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
for this_path in site_paths:
    if this_path not in sys.path:
        sys.path.append(this_path)

class PasteThisImageType(sublime_plugin.TextCommand):

    def on_filename_given(self, user_input):
        # callback for sublime input panel
        # user has given us the filename for our clipboard img in 'user_input'
        # the picture directory has been set (see run) now make it if reqd.
        try:
            os.makedirs(self.picdir)
        except FileExistsError:
            # directory already exists
            pass
        writeit = True
        rel_picfile = "_data_local/" + user_input + "." + self.paste_as
        abs_picfile = os.path.join(self.picdir, user_input + "." + self.paste_as)
        xclipcmd = "xclip -sel clipboard -o -t {}".format(self.mime)
        xclipcmd_tokens = shlex.split(xclipcmd)
        if os.path.isfile(abs_picfile):
            if not sublime.ok_cancel_dialog("Overwrite existing file\n" + abs_picfile):
                writeit = False
        if writeit:
            with open(abs_picfile, 'wb') as f:
                subprocess.call(xclipcmd_tokens, stdout=f)
            if self.paste_as in ['jpeg', 'jpg', 'tiff', 'tif', 'bmp']:
                if ph_utils.which("mogrify"):
                    sublime.status_message("Optimising {} image with 'mogrify'".format(self.paste_as))
                    mogcmd = "mogrify -resize '>600x' " + abs_picfile
                    mogcmd_tokens = shlex.split(mogcmd)
                    subprocess.call(mogcmd_tokens)
                else:
                    sublime.status_message("'mogrify' not installed: {} image not optimised.".format(self.paste_as))
            if self.paste_as == 'png':
                if ph_utils.which("optipng"):
                    sublime.status_message("Optimising png image with 'optipng'")
                    opticmd = "optipng " + abs_picfile
                    opticmd_tokens = shlex.split(opticmd)
                    subprocess.call(opticmd_tokens)
                else:
                    sublime.status_message("'optipng' not installed: png image not optimised.")
        self.view.run_command(
                    "insert_my_text", {"args":
                    {'text': rel_picfile}})

    def run(self, edit, args):
        self.paste_as = args['img_type']

        if self.paste_as: # if we have an image mime type we can deal with...
            self.mime = "image/" + self.paste_as # build the proper mime-type string
            variables = self.view.window().extract_variables ()
            self.picdir = os.path.join(variables["file_path"], "_data_local/")
            prompt = "Save clipboard image as: ./_data_local/FILENAME.{}".format(self.paste_as)
            placeholder = "FILENAME"
            # prompt user to input filename for image (async call-back via self.on_filename_given)
            self.view.window().show_input_panel(prompt, placeholder, self.on_filename_given, None, None)
        else:
            sublime.status_message("NOTHING TO PASTE: clipboard does not contain an image")

class GrabClipboardPhotoCommand(sublime_plugin.TextCommand):
    """
    When the clipboard contains an image this utility can save it and paste the name of the saved file into the text at the cursorpos.
    1. First check clipboard contains image
    2. If img is available in multiple mime formats e.g. bmp, png - prompt user to choose file type
    3. Prompt user for FILENAME. The file will be saved with location/name = ./_data_local/FILENAME.<file-type>
    4. The save location will be written into the current open document at the cursor
    """
    def on_img_type_select(self, index):
        """
        Call-back function for quick-panel that displays img type choices
        """
        if index >= 0: # selection was made (-1 indicates no choice, i.e. user pressed <esc>)
            self.view.run_command(
                        "paste_this_image_type", {"args":
                        {'img_type': self.img_list[index]}})

    def run(self, edit):
        self.the_stdout = ""
        self.paste_as = ""
        self.img_list = []
        sel = self.view.sel()[0]
        if not sublime.get_clipboard():
            # This kludge works as sublime text's internal clipboard shows empty
            # if there are only images (mime types) available on the clipboard.
            # this check is also useful as the xclip TARGETS command crashes when sublime's own data is on the clipboard
            # however this is not ideal as it means that when images AND text are available the image will get missed
            checkclip_str = "xclip -sel clipboard -o -t TARGETS"
            try: # run extenal xclip process to get mime types of current clipboard
                self.the_stdout = subprocess.check_output(checkclip_str, stderr=subprocess.STDOUT, shell=True, timeout=3, universal_newlines=True)
            except subprocess.CalledProcessError as exc:
                sublime.message_dialog("xclip failure code: {} {}".format(exc.returncode, exc.output))
                self.the_stdout = ""
            if self.the_stdout:
                # img mime types reported as being on clipboard
                # filter this output via regex to get file extensions
                pattern_imgmime = re.compile(r"""
                    ^image\/
                    (?P<imgtype>.*?)\s*$
                    """, re.VERBOSE | re.MULTILINE)
                found_list = re.findall(pattern_imgmime, self.the_stdout)
                # filter again (via set intersection) to leave only the images we support
                supported_imgs = ['gif', 'png', 'jpeg', 'jpg', 'tiff', 'tif', 'bmp']
                self.img_list = list(set(found_list) & set(supported_imgs))
                # sublime.message_dialog("img mime types found: {}".format(self.img_list)
                if len(self.img_list) > 0: # we have at least one img type
                    if len(self.img_list) > 1: # we have multiple image types
                        # prompt user to select the save-type
                        sublime.active_window().show_quick_panel(
                            self.img_list, 
                            self.on_img_type_select
                        ) # Note: quick_panel is async call - doesn't return
                    else:
                        self.paste_as = self.img_list[0]
                        self.view.run_command(
                                    "paste_this_image_type", {"args":
                                    {'img_type': self.paste_as}})
            else:
                sublime.status_message("Clipboard is empty.")
        else:
            sublime.status_message("Clipboard is textual - not an image.")
    

