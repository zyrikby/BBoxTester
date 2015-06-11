'''
Created on Oct 13, 2014

@author: Yury Zhauniarovich <y.zhalnerovich{at}gmail.com>
'''
import os
from zipfile import ZipFile, ZIP_DEFLATED


def zipdir(basedir, archivename):
    assert os.path.isdir(basedir)
    with ZipFile(archivename, "a", ZIP_DEFLATED) as z:
        for root, _, files in os.walk(basedir):
            #NOTE: ignore empty directories
            #print root
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
                z.write(absfn, zfn)