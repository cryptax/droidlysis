# -*- coding: utf-8 -*-

# A script to search suspicious malicious funtions by Droidlysis
# Author: d3xter
#?shortcut=
import os
import re
import json
from com.pnfsoftware.jeb.client.api import IScript
from com.pnfsoftware.jeb.core.units.code.android import IDexUnit

class DroidlysisSearch(IScript):
    BMKEY = 'DLYSISMARKS'
    
    def run(self, ctx):
        prj = ctx.getMainProject()
        assert prj, 'Need a project'
        
        bmstr = prj.getData(DroidlysisSearch.BMKEY)
        if not bmstr:
            print(u'😵‍💫 Droidlysis mapping ...')

            path = ctx.displayFileOpenSelector('Select a file')
            assert path, 'Need a valid file path'

            with open(path, 'r') as f:
                file_contents = f.readlines()

            bm = {}
            bm['outputfile'] = path
            current_key = None

            pattern_key = r'^##\s+(.*?)$'
            pattern_data = r'^- path=(.*?)\s+file=(.*?)\s+no=\s*(\d+)\s+line=(.*?)$'

            for line in file_contents:
                key_match = re.match(pattern_key, line)
                data_match = re.match(pattern_data, line)
                
                if key_match:
                    current_key = key_match.group(1)
                    bm[current_key] = []
                elif current_key and data_match:
                    path = data_match.group(1)
                    file = data_match.group(2)
                    no = data_match.group(3)
                    line = data_match.group(4).strip()[2:-3].strip()
                    bm[current_key].append([path, line])

            prj.setData(DroidlysisSearch.BMKEY, json.dumps(bm), True)

        bmstr = prj.getData(DroidlysisSearch.BMKEY)
        bm = json.loads(bmstr)
        if not os.path.exists(bm['outputfile']):
            print(u'🤗 Droidlysis goodbye ...')
            prj.clearAllData(DroidlysisSearch.BMKEY)
            return
        
        print(u'😄 Droidlysis searching ...')
        headers = ['Match', 'Path', 'Code']
        rows = []
        for mm, info in bm.items():
            if not mm == 'outputfile':
                for ii in info:
                    rows.append([mm, ii[0], ii[1]])

        index = ctx.displayList('Droidlysis Search', 'List of suspicious functions identified by Droidlysis', headers, rows)
        if index < 0:
            return
        
        sel = rows[index]
        dex = prj.findUnit(IDexUnit)
        assert dex, 'Need a dex file'

        f = ctx.findFragment(dex, 'Disassembly', True)
        if f:
            f.setActiveAddress(sel[1])
