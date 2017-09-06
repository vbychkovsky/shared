#!/usr/bin/env python

# ToDo:
# - implement list/download metadata
# - upload a date link file
# - (opt) refactor B2 commands
# -- maybe replace B2 shell call with python?

import argparse
import hashlib
import subprocess
import os
import json
import itertools
import logging
import tempfile

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
            output = subprocess.check_output(['b2', 'download-file-by-name', bucket, filename, f.name])
            logging.info("Found an existing stats file, checking...")
            return json.load(f)
    except subprocess.CalledProcessError, e:
        return None


def rawUploadFileToB2(bucket, b2Filepath, localFilepath):
    try:
        output = subprocess.check_output(['b2', 'upload-file', bucket, localFilepath, b2Filepath])
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

        basename = os.path.basename(filepath)
        b2Filename = "{hashDir}/{sha1}_{basename}".format(**dict(globals(), **locals()))
        b2StatsName = "{hashDir}/{sha1}{infoExt}".format(**dict(globals(), **locals()))

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
            output = rawUploadFileToB2(bucket, b2Filename, filepath)
            if output is None:
                return False

            logging.debug(output)

            # ToDo: upload date index entry here

            # copy some fields into the output
            for field in ['fileId', 'uploadTimestamp']:
                localFileStats[field] = output[field]

            logging.debug(localFileStats)

            with tempfile.NamedTemporaryFile() as f:
                json.dump(localFileStats, f)
                # make sure that the data is in the OS buffers for later reading
                f.flush()
                # upload it
                output = rawUploadFileToB2(bucket, b2StatsName, f.name)
                if output is not None:
                    return True

        return False

def uploadCommand(args):
    for filepath in args.file:
        uploadFileToB2(filepath)

def listCommand(args):
    logging.error("list command is not yet implemented!")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Hash-based file handling for B2.')
    parser.add_argument('--loglevel', default='INFO')

    subparsers = parser.add_subparsers(help='<still need to write this up>')

    uploadcmd = subparsers.add_parser('upload', help='hash-upload files to b2')
    uploadcmd.add_argument('file', nargs='+', help='files to upload')
    uploadcmd.set_defaults(func=uploadCommand)

    listcmd = subparsers.add_parser('list', help='read metadata for hash-uploads')
    listcmd.set_defaults(func=listCommand)

    args = parser.parse_args()

    logLevel = getattr(logging, args.loglevel.upper(), None)
    if logLevel is not None:
        logging.basicConfig(level=logLevel)

    logging.debug(args)

    args.func(args)
