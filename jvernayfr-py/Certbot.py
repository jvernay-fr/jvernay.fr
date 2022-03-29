# SPDX-FileCopyrightText: 2022 Julien Vernay <contact@jvernay.fr>
# SPDX-License-Identifier: GPL-3.0-or-later
# Part of jvernay.fr build scripts.

from typing import List
from .Utility import *


class Certbot:
    CHALLENGE_URI = ".well-known/acme-challenge"

    def __init__(self):
        self.exe = shutil.which("certbot")
        if not self.exe:
            raise RuntimeError("Could not find 'certbot' on path...")
    
    def certify(self, server_names: List[str], webroot: str):
        """Create certificates for all the given server_names.
        This requires doing an ACME challenge. For this to work,
        the 'webroot' directory must be setup (by you!) such that
        all its files are accessible from the URL:
        http://{server_name}/{Certbot.CHALLENGE_URI}/{filename}"""

        args = [ self.exe, "certonly", "--webroot",
            "--webroot-path", ResolvePath("./nginx/html/.well-known") ]
        for server_name in server_names:
            args += [ "-d", server_name ]
        subprocess.run(args)

    # certbot certonly -n
    # certbot certificates