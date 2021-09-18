import sublime, sublime_plugin, re, os, sys
from datetime import datetime

site_paths=['/usr/lib/python3.5', '/usr/local/lib/python3.7/dist-packages', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
# site_paths=['/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/home/key/.local/lib/python3.5/site-packages', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']
for this_path in site_paths:
    if this_path not in sys.path:
        sys.path.append(this_path)

from dateutil.parser import parse 

# print("PH Plugin insert_datetime is loading")

class InsertDatetimeCommand(sublime_plugin.TextCommand):
    """
    A sublime text plugin for inputting / converting dates / times:
    ---------------------------------------------------------------
    If no text is selected:
        Inserts today's unix timestamp and date/time at cursor.
    If text is selected:
        Attempts to convert selection to a datetime object. The selection can be a unix timestamp or a date like string. Inserts timestamp and datetime for the info selected.
    Plugin should be activated via an entry in the key binding file e.g.:
    { "keys": ["f5"], "command": "insert_datetime"}
    """
    def run(self, edit):
        def str_from_date(cur):
            stamp = int(cur.timestamp()) # no millisecs
            return "{} = {}".format(stamp, cur.strftime("%a %b %d %Y, %H:%M:%S"))
        def str_from_unkn(sel):
            if re.findall('^[\\d]{10}', sel):
                try:
                    no_millisecs = int(float(sel))
                    dt = datetime.fromtimestamp(no_millisecs)
                    return str_from_date(dt)
                except:
                    return None
            else:
                try:
                    dt = parse(sel) # 
                    return str_from_date(dt)
                except:
                    return None
        # Main:
        # Get selection(s)
        sel = self.view.sel();
        for s in sel:       
            if s.empty(): # insert today's datestamp at cursor
                todays_stamp = str_from_date(datetime.today())
                self.view.insert(edit, s.a, todays_stamp)
            else: # decode a date from the selection
                seltext = self.view.substr(s)
                date_calc = str_from_unkn(seltext)
                if not date_calc:
                    date_calc = seltext + ' : Undecodable Date/Time'
                self.view.replace(edit, s, date_calc)
