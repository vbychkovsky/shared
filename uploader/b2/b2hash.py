#!/usr/bin/env python

# ToDo:
# - implement re-indexing functionality
# - index based on EXIF data
# - skip duplicate uploads (for actual files only)
# -- download transactions are 10x cheaper than listing transactions, assuming no cost for header downloads
# -- upload transactions are completely free
# -- so it would make sense to not worry about small uploads, but maybe resume large uploads.
# - add listing datafile
# - add downloading
# - upload a date link file
# - (opt) refactor B2 commands
# -- maybe replace B2 shell call with python?
# - better error checking - can uploads fail silently?

import argparse
import hashlib
import subprocess
import os
import json
import itertools
import logging
import tempfile
import time

try:
    import exiftool
except:
    exiftool = None

def computeSHA1(filename, blocksize=None):
    sha1 = hashlib.sha1()

    if blocksize is None:
        blocksize = sha1.block_size

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), ''):
           sha1.update(chunk)
    return sha1.hexdigest()


def loadRemoteJSON(bucket, filename):
    try:
        with tempfile.NamedTemporaryFile() as f:
            output = subprocess.check_output(['b2', 'download-file-by-name', '--noProgress', bucket, filename, f.name])
            return json.load(f)
    except subprocess.CalledProcessError, e:
        return None


def rawUploadFileToB2(bucket, b2Filepath, localFilepath):
    try:
        output = subprocess.check_output(['b2', 'upload-file', bucket, localFilepath, b2Filepath])
        # ToDo: can the above upload fail without giving a bad return code?
        jsonString = "".join(itertools.dropwhile(lambda x: x.strip() <> '{', output.splitlines()))
        parsedOutput = json.loads(jsonString)
        return parsedOutput
    except subprocess.CalledProcessError, e:
        logging.error("Raw upload failed for {}:{}".format(b2Filepath, e))
        return None


def uploadFileToB2(
            filepath,
            bucket = "myPublic1",
            hashDir = "hash",
            infoExt = ".stats"):

        logging.info("processing {}...".format(filepath))

        try:
            # get filesystem stats
            stats = os.stat(filepath)
        except OSError, e:
            logging.error(e)
            return False

        sha1 = computeSHA1(filepath)

        date = time.gmtime(stats.st_mtime)
        dateformat = "%Y/%m/%d/%H-%M-%S"
        datestr = time.strftime(dateformat, date)

        basename = os.path.basename(filepath)
        b2Filename = "{hashDir}/files/{sha1}_{basename}".format(**dict(globals(), **locals()))
        b2StatsName = "{hashDir}/stats/{sha1}.stats".format(**dict(globals(), **locals()))
        b2MetadataName = "{hashDir}/metadata/{sha1}.json".format(**dict(globals(), **locals()))
        b2ctimeName = "{hashDir}/ctime/{datestr}/{sha1}.stats".format(**dict(globals(), **locals()))

        localFileStats = {
            'filename': os.path.basename(filepath),
            'size': stats.st_size,
            'mtime': stats.st_mtime,
            'b2link': b2Filename,
        }


        # check if file is already there (download the link)
        remoteStats = loadRemoteJSON(bucket, b2StatsName)
        if remoteStats is not None and 'filename' in remoteStats:
            if remoteStats['filename'] != localFileStats['filename']:
                logging.error("Stats disagree:\n{}\n{}\n".format(remoteStats, localFileStats))
                return False
            else:
                logging.info("Stats match")
                return True

        else:
            # ToDo: could I check if this file is already uploaded and skip uploads?
            # could I do for this for every file
            output = rawUploadFileToB2(bucket, b2Filename, filepath)
            if output is None:
                return False

            logging.debug(output)

            # copy some fields into the output
            for field in ['fileId', 'uploadTimestamp']:
                localFileStats[field] = output[field]

            logging.debug(output['uploadTimestamp'])
            logging.debug(localFileStats)

            date = time.gmtime(output['uploadTimestamp']/1000)
            datestr = time.strftime(dateformat, date)
            b2uploadTimeName = "{hashDir}/uploadtime/{datestr}/{sha1}.stats".format(**dict(globals(), **locals()))
            logging.debug("Using {} as the name".format(b2uploadTimeName))

            date_time_original = None
            if exiftool is not None:
                with exiftool.ExifTool() as et:
                    exif = et.get_metadata(filepath)
                    date_time_original = exif.get("EXIF:DateTimeOriginal", None)
                    with tempfile.NamedTemporaryFile() as f:
                        json.dump(exif, f)
                        f.flush()
                        rawUploadFileToB2(bucket, b2MetadataName, f.name)


            with tempfile.NamedTemporaryFile() as f:
                json.dump(localFileStats, f)
                # make sure that the data is in the OS buffers for later reading
                f.flush()

                # upload all stat files
                output = []
                for b2Name in [b2ctimeName, b2uploadTimeName, b2StatsName]:
                    output = rawUploadFileToB2(bucket, b2Name, f.name)

                # make sure that the final stat file got uploaded
                if output is not None:
                    return True


        return False


def uploadCommand(args):
    for filepath in args.file:
        uploadFileToB2(filepath)


def b2listFiles(bucket = 'myPublic1', startFile = ""):
    try:
        output = subprocess.check_output(['b2', 'list-file-names', bucket, startFile])
        return json.loads(output)
    except subprocess.CalledProcessError, e:
        logging.error(e)
        return None


def listCommand(args):
    bucket = 'myPublic1'
    # ToDo turn the following command into an iterator
    result = b2listFiles(bucket, args.prefix)
    for f in result['files']:
        filename = f["fileName"]
        if filename.startswith(args.prefix) and filename.endswith(".stats"):
            info = loadRemoteJSON(bucket, filename)
            print("{}, {}, {}".format(info['filename'], info["size"], filename))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Hash-based file handling for B2.')
    parser.add_argument('--loglevel', default='INFO')

    subparsers = parser.add_subparsers(help='<still need to write this up>')

    uploadcmd = subparsers.add_parser('upload', help='hash-upload files to b2')
    uploadcmd.add_argument('file', nargs='+', help='files to upload')
    uploadcmd.set_defaults(func=uploadCommand)

    listcmd = subparsers.add_parser('list', help='read metadata for hash-uploads')
    listcmd.add_argument('--prefix', default="hash/stats/", help='filename prefix to search')
    listcmd.set_defaults(func=listCommand)

    args = parser.parse_args()

    logLevel = getattr(logging, args.loglevel.upper(), None)
    if logLevel is not None:
        logging.basicConfig(level=logLevel)

    logging.debug(args)

    args.func(args)
