import tarfile
from database import Database
from imagebuilder import ImageBuilder
from util import create_folder
import re
import shutil
import urllib.request
import tempfile
import logging
import hashlib
import os
import os.path
import subprocess

#logging.basicConfig(filename="output.log")
logging.basicConfig(level=logging.DEBUG)


class Image():
    # distro
    # version
    # target
    # subtarget
    # profile
    # packages
    def __init__(self):
        pass

    def _set_path(self):
        self.pkgHash = self.getPkgHash()

        # using lede naming convention
        path_array = [self.distro, self.version, self.pkgHash, self.target, self.subtarget]

        if self.target != "x86":
            path_array.append(self.profile)
       #     path_array.append("sysupgrade.bin")
       # else:
       #     path_array.append("sysupgrade.img")

        self.name = "-".join(path_array)
        self.path = os.path.join("download", self.distro, self.version, self.target, self.subtarget, self.name)

    def request_variables(self, distro, version, target, subtarget, profile, packages):
        self.distro = distro.lower()
        self.version = version
        self.target = target
        self.subtarget = subtarget
        self.profile = profile
        self.packages = packages
        self._set_path()
   
    def request_params(self, params):
        self.distro = params["distro"].lower()
        self.version = params["version"]
        self.target = params["target"]
        self.subtarget = params["subtarget"]
        self.profile = params["profile"]
        self.packages = params["packages"]
        self._set_path()

    # returns the path of the created image
    def get(self):
        if not self.created():
            logging.info("start build")	
            self.build() 
        else:
            print("Heureka!")
        return (self.path + "-sysupgrade.img")

    # generate a hash of the installed packages
    def getPkgHash(self):
        packagesSorted = sorted(self.packages)
        h = hashlib.sha256()
        h.update(bytes(" ".join(packagesSorted), 'utf-8'))

        return h.hexdigest()[:12]

    # builds the image with the specific packages at output path
    def build(self):
        # create image path
        ibPath = os.path.abspath(os.path.join("imagebuilder", self.distro, self.target, self.subtarget))
        imagebuilder = ImageBuilder(self.distro, self.version, self.target, self.subtarget)

        logging.info("use imagebuilder at %s", imagebuilder.path)

        buildPath = os.path.dirname(self.path)
        with tempfile.TemporaryDirectory() as buildPath:
    #        print(buildPath)

            create_folder(os.path.dirname(self.path))

            cmdline = ['make', 'image']
            if self.target != "x86":
                cmdline.append('PROFILE=%s' % self.profile)
            cmdline.append('PACKAGES=%s' % ' '.join(self.packages))
            cmdline.append('BIN_DIR=%s' % buildPath)
            cmdline.append('EXTRA_IMAGE_NAME=%s' % self.pkgHash)

            logging.info("start build: %s", " ".join(cmdline))

            proc = subprocess.Popen(
                cmdline,
                cwd=imagebuilder.path,
                stdout=subprocess.PIPE,
                shell=False,
                stderr=subprocess.STDOUT
            )

            output, erros = proc.communicate()
            returnCode = proc.returncode
            if returnCode == 0:
                for sysupgrade in os.listdir(buildPath):
                    if sysupgrade.endswith("combined-squashfs.img") or sysupgrade.endswith("sysupgrade.bin"):
                        logging.info("move %s to %s", sysupgrade, (self.path + "-sysupgrade.bin"))
                        shutil.move(os.path.join(buildPath, sysupgrade), (self.path + "-sysupgrade.bin"))

                    if sysupgrade.endswith("factory.bin"):
                        logging.info("move %s to %s", sysupgrade, (self.path + "-factory.bin"))
                        shutil.move(os.path.join(buildPath, sysupgrade), (self.path + "-factory.bin"))

                logging.info("build successfull")
            else:
                print(output.decode('utf-8'))
                logging.info("build failed")

    # check if image exists
    def created(self):
        # created images will be stored in downloads.lede-project.org like paths
        # the package should always be a sysupgrade
        logging.info("check path %s", self.path + "-sysupgrade.bin")
        return os.path.exists(self.path + "-sysupgrade.bin")

# todo move stuff to tmp and only move sysupgrade file
# usign für python ansehen

if __name__ == "__main__":
    database = Database()

    # with some usefull tools"
    packages =  ["vim", "attended-sysupgrade", "luci", "luci2-io-helper"]
    packages =  ["vim", "luci", "iperf", "wavemon", "syslog-ng"]

    # builds libremesh
    #packages =  ["vim", "tmux", "screen", "attended-sysupgrade", "luci", "lime-full", "-ppp", "-dnsmasq", "-ppp-mod-pppoe", "-6relayd", "-odhcp6c", "-odhcpd", "-firewall"]

    logging.info("started logger")


    image_ar71 = Image()
    image_ar71.request_variables("lede", "17.01.1", "ar71xx", "generic", "ubnt-loco-m-xw", packages)
    image_ar71.get()
    image_x86 = Image()
    image_x86.request_variables("lede", "17.01.1", "x86", "64", "", packages)
#    image_x86.request_variables("lede", "17.01.0", "ar71xx", "generic", "", packages)
#    image_ar71.get()
#    image_x86.get()
#    imagebuilder_old = ImageBuilder("lede", "17.01.0", "ar71xx", "generic")
#    imagebuilder_x86 = ImageBuilder("lede", "17.01.1", "x86", "64")
#    profiles_data = imagebuilder_x86.parse_profiles()
#    packages = imagebuilder_x86.parse_packages()
#    print("found %i profiles " % len(profiles_data[1]))
#    print("found %i packages " % len(packages))
#    database.insert_profiles(imagebuilder_x86.target, imagebuilder_x86.subtarget, profiles_data)
#    database.insert_packages(imagebuilder_x86.target, imagebuilder_x86.subtarget, packages)
#
#    profiles_data = imagebuilder_old.parse_profiles()
#    packages = imagebuilder_old.parse_packages()
#    print("found %i profiles " % len(profiles_data[1]))
#    print("found %i packages " % len(packages))
#
#    database.insert_profiles(imagebuilder_old.target, imagebuilder_old.subtarget, profiles_data)
#    database.insert_packages(imagebuilder_old.target, imagebuilder_old.subtarget, packages)
#
