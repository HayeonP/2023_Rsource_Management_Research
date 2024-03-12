import glob
import re
import os

# s = str(input('Input Searching Text: '))
s = 'ClguardExperiment'
p = re.compile(s)

files = glob.glob('/home/hayeonp/experience/recovery_temp/*')
files_txt = [f for f in files if f.endswith('.txt')]
print(files_txt)

for i in files_txt:
    with open(i, 'r') as f:
        for x,y in enumerate(f.readlines(), 1):
            m = p.findall(y)
            if m:
                print('File %s [ %d ] Line Searching: %s' %(i,x,m))
                print('Full Line Text: %s' %y)
        print()

