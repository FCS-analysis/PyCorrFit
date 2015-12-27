#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Download experimental data files from https://github.com/FCS-analysis/FCSdata

This module establishes
"""
from __future__ import division, print_function

import os
from os.path import abspath, dirname, join, exists

import simplejson as json
import urllib3

# Download path root
raw_origin = "https://github.com/FCS-analysis/FCSdata/raw/master/"
# GitHub API root
api_origin = "https://api.github.com/repos/FCS-analysis/FCSdata/git/"
# Download directory
dldir = join(dirname(abspath(__file__)), "data")
# Pool Manager handles all requests
pool_manager = urllib3.PoolManager()

_fcs_data_tree = None

def dl_file(url, dest, chunk_size=6553,
            http=pool_manager):
    """
    Download `url` to `dest`.
    
    Parameters
    ----------
    url : str
        Full download URL
    dest : str
        Full download path. Directory will be created if non-existent.
    chunk_size : int
        Chunk size of download (download buffer size).
    http : instance of `urllib3.PoolManager`
        Manages all connections. Must implement the
        `request` method.
    """
    if not exists(dirname(dest)):
        os.makedirs(dirname(dest))
    r = http.request('GET', url, preload_content=False)
    with open(dest, 'wb') as out:
        while True:
            data = r.read(chunk_size)
            if data is None or len(data)==0:
                break
            out.write(data)


def get_data_files_ext(extension, dldir=dldir, pool_manager=pool_manager,
                      api_origin=api_origin, raw_origin=raw_origin):
    """
    Get all files in the repository `origin` that are
    in the folder `extension` and have a file-ending
    that matches `extension` (case-insensitive).
    
    The files are downloaded and local paths in the
    `dldir` directory are returned.
    
    Parameters
    ----------
    extension : str
        A file extension such as `fcs` or `sin`.
    dldir : str
        Path to download directory.
    http : instance of `urllib3.PoolManager`
        Manages all connections. Must implement the
        `request` method.
    raw_origin : str
        Web root for downloads, e.g.
        "https://raw.github.com/FCS-analysis/FCSdata"
    api_origin : str
        GitHub api URL, e.g.
        "https://api.github.com/repos/FCS-analysis/FCSdata/git/"

    
    Notes
    -----
    The files in the remote location must be sorted according to
    file extionsion. E.g. all `*.sin` files must be located in a
    folder in the root directory named `sin`.
    """
    files = get_fcs_data_tree(pool_manager=pool_manager, api_origin=api_origin)
    
    ext = extension.lower()
    extfiles = [ f for f in files if f.lower().startswith(ext+"/") and f.lower().endswith("."+ext)]
    
    dl_files = []
    
    for f in extfiles:
        dest = join(dldir, f)
        if not exists(dest):
            dl_file(join(raw_origin, f), dest)
        dl_files.append(dest)
    
    return dl_files


def get_fcs_data_tree(pool_manager=pool_manager, api_origin=api_origin):
    """
    Returns FCSdata repository tree.
    The tree is saved in the global variable `_fcs_data_tree` to reduce
    number of GitHub API requests.
    """
    global _fcs_data_tree
    if _fcs_data_tree is None:
        url = api_origin+"trees/master?recursive=1"
        # headers
        headers = {'User-Agent': __file__}
        # GitHub API token to prevent rate-limits
        # Key is generated with
        #
        #    gem install travis
        #    travis encrypt GH_READ_API_TOKEN=secret-token
        #    
        # Add the result to env in travis.yml.
        if "GH_READ_API_TOKEN" in os.environ:
            headers["Authorization"] = "token {}".format(os.environ["GH_READ_API_TOKEN"])
        r = pool_manager.request("GET", url, headers=headers)
        jd = json.loads(r.data)
        tree = jd["tree"]
        _fcs_data_tree = [ t["path"] for t in tree ]
    return _fcs_data_tree