# SPDX-FileCopyrightText: 2022 Julien Vernay <contact@jvernay.fr>
# SPDX-License-Identifier: GPL-3.0-or-later
# Part of jvernay.fr build scripts.

"""We build nginx from sources as we want to specify a custom configuration."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple
from enum import Enum
from .Utility import *
from .Certbot import Certbot

NGINX_PREFIX = Path("./nginx").absolute()
NGINX_SRC = NGINX_PREFIX / "src"
NGINX_EXE = NGINX_PREFIX / "sbin" / "nginx"
NGINX_CERTBOT_CHALLENGES = NGINX_PREFIX / "certbot_challenges"

SOURCE_CODE_LOCATIONS = {
    "nginx": "https://nginx.org/download/nginx-1.21.6.tar.gz",
    "pcre2": "https://github.com/PhilipHazel/pcre2/releases/download/pcre2-10.39/pcre2-10.39.tar.gz",
    "zlib": "https://zlib.net/zlib-1.2.12.tar.gz",
}

NGINX_CONFIGURE_OPTIONS = [
    "--prefix=" + str(NGINX_PREFIX),
    "--with-pcre=" + str(NGINX_SRC / "pcre2"),
    "--with-zlib=" + str(NGINX_SRC / "zlib"),
    "--with-http_ssl_module",
    "--with-http_v2_module",
    "--with-http_addition_module",
]

class Protocol(Enum):
    HTTP = 1
    ONLY_HTTPS = 2

@dataclass
class Service:
    server_names: List[str]
    local_port: int
    protocol: Protocol
    directives: List[str]

class Nginx:
    class Config:
        GLOBAL = [ "worker_processes auto" ]
        EVENTS = []
        HTTP = [
            "include mime.types",
            "default_type application/octet-stream",
        ]
      
    @staticmethod
    def _build():
        EnsureEmptyDir(NGINX_PREFIX)

        logging.info("Downloading sources...")
        EnsureEmptyDir(NGINX_SRC)
        for name, url in SOURCE_CODE_LOCATIONS.items():
            tarpath = (NGINX_SRC / name).with_suffix(".tar.gz")
            Download(url, tarpath)
            Untar(tarpath, NGINX_SRC / name)
        
        logging.info("Building nginx...")
        WORK_DIR = NGINX_SRC / "nginx"
        subprocess.run(["./configure"] + NGINX_CONFIGURE_OPTIONS, cwd=WORK_DIR)
        subprocess.run(["make", "install", "-j"], cwd = WORK_DIR)

        EnsureEmptyDir(NGINX_CERTBOT_CHALLENGES)
        Path(NGINX_CERTBOT_CHALLENGES / "THIS_FOLDER_IS_PUBLIC.txt").touch()

    def __init__(self, force_rebuild = False):
        if force_rebuild or not NGINX_PREFIX.exists():
            logging.info("Building nginx from sources:")
            Nginx._build()
    
    def config(self, services: List[Service], *,
            with_server_names = False, with_https: None|Tuple[str,str] = None,
            with_certbot_config=True):
        """Generates the nginx configuration path.
        
        services: list of services that should be accessible.
        with_server_names: whether to bind port 80 and use HTTP host to distinguish between services.
        with_https: if not None, must be a pair ("path/to/cert", "path/to/privkey")"""

        logging.info("Generating nginx configuration file:")
        if with_https and not with_server_names:
            raise ValueError("'with_https' requires 'with_server_name' too.")

        config = f"# Generated by jvernayfr-py/Nginx.py ({datetime.now()})\n\n"

        for line in Nginx.Config.GLOBAL:
            config += f"{line};\n"
        
        config += "\nevents {\n"
        for line in Nginx.Config.EVENTS:
            config += f"\t{line};\n"
        config += "}\n"
        
        config += "\nhttp {\n"
        if with_https:
            cert_path, key_path = with_https
            config += f"\tssl_certificate {cert_path};\n"
            config += f"\tssl_certificate_key {key_path};\n\n"
        for line in Nginx.Config.HTTP:
            config += f"\t{line};\n"
        
        http_filter = lambda s: s.protocol in [Protocol.HTTP, Protocol.ONLY_HTTPS]
        for service in filter(http_filter, services):
            config += f"\n\t### {' '.join(service.server_names)} ###\n\n"
            if with_server_names:
                # Configuration for outside world.

                # First the unsecured part.
                config += "\tserver {\n"
                config += f"\t\tserver_name {' '.join(service.server_names)};\n"
                config += "\t\tlisten 80;\n"
                if with_certbot_config:
                    config += f"\t\tlocation {Certbot.CHALLENGE_URI} {{\n"
                    config += f"\t\t\troot {NGINX_CERTBOT_CHALLENGES};\n"
                    config += "\t\t}\n"
                
                if service.protocol == Protocol.ONLY_HTTPS:
                    # redirection to HTTPS
                    config += f"\t\treturn 302 https://{service.server_names[0]}$request_uri;\n"
                else:
                    for directive in service.directives:
                        config += f"\t\t{directive}\n"
                config += "\t}\n"

                # Then the secured part
                if with_https:
                    config += "\tserver {\n"
                    config += f"\t\tserver_name {' '.join(service.server_names)};\n"
                    config += "\t\tlisten 443 ssl;\n\n"
                    for directive in service.directives:
                        config += f"\t\t{directive}\n"
                    config += "\t}\n"
                
            # Finally, the localhost part
            config += "\tserver {\n"
            config += f"\t\tlisten localhost:{service.local_port};\n"
            for directive in service.directives:
                config += f"\t\t{directive}\n"
            config += "\t}\n"
                
        config += "}\n" # closing "http {"

        with open(NGINX_PREFIX / "conf" / "nginx.conf", "w") as f:
            f.write(config)
        
        # Checking if nginx see any problem
        result = subprocess.run([NGINX_EXE, "-t"])
        if result.returncode:
            raise RuntimeError("Nginx cannot parse the generated configuration...")

    def run(self):
        if Path(NGINX_PREFIX / "logs" / "nginx.pid").exists():
            result = subprocess.run([NGINX_EXE, "-s", "reload"])
            if result.returncode:
                # The nginx.pid exists if nginx was interrupted by OS.
                # In these cases, nginx will emit an error, because it
                # is not currently running. Instead, run it normally.
                subprocess.run([NGINX_EXE])
            logging.info("Nginx reloaded!")
        else:
            subprocess.run([NGINX_EXE])
            logging.info("Nginx started!")