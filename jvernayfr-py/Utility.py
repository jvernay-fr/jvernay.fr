# SPDX-FileCopyrightText: 2022 Julien Vernay <contact@jvernay.fr>
# SPDX-License-Identifier: GPL-3.0-or-later
# Part of jvernay.fr build scripts.

import requests, tarfile, os, shutil, logging, subprocess
from pathlib import Path

def Download(url: str, filepath: str):
    logging.info("Downloading {url} into {filepath}")
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"Download(): could not download {url}")
    with open(filepath, "wb") as f:
        f.write(r.content)

def Untar(archivepath: str, folderpath: str):
    folderpath = str(folderpath)
    logging.info(f"Decompressing {archivepath} to {folderpath}/")
    tar = tarfile.open(archivepath)
    fileinfo = tar.next()
    tar.extractall(folderpath)
    tar.close()
    output = Path(folderpath)/fileinfo.name
    os.rename(output, folderpath+"-tmp")
    shutil.rmtree(folderpath)
    os.rename(folderpath+"-tmp", folderpath)

def EnsureEmptyDir(path: str):
    if Path(path).exists():
        shutil.rmtree(path)
    Path(path).mkdir(parents=True)

def ResolvePath(path: str):
    return str(Path(path).resolve())