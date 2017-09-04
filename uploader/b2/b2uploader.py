#!/usr/bin/env python

# ToDo:
# - upload a date link file
# - (opt) refactor B2 commands
# -- maybe replace B2 shell call with python?
# - (opt) factor out naming converntions
# - improve error chechking
# - switch to a more robust temp file method

import argparse
import hashlib
import subprocess
import os
import json
import itertools
import logging

def computeSHA1(filename, blocksize=None):
    sha1 = hashlib.sha1()

    if blocksize is None:
        blocksize = sha1.block_size

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), ''):
           sha1.update(chunk)
    return sha1.hexdigest()



def uploadFileToB2(
            filepath,
            bucket = "myPublic1",
            hashDir = "hash",
            infoExt = ".stats"):

        tmpDir = "/tmp"
        try:
            logging.info("processing {}...".format(filepath))

            # get filesystem stats
            stats = os.stat(filepath)

            sha1 = computeSHA1(filepath)

            basename = os.path.basename(filepath)
            b2Filename = "{hashDir}/{sha1}_{basename}".format(**dict(globals(), **locals()))

            localFileStats = {
                'filename': os.path.basename(filepath),
                'size': stats.st_size,
                'b2link': b2Filename,
            }


            # check if file is already there (download the link)
            b2StatsName = "{hashDir}/{sha1}{infoExt}".format(**dict(globals(), **locals()))
            localStatsName = tmpDir + "/" + sha1 + ".stats_remote" # replace with temp file
            try:
                output = subprocess.check_output(['b2', 'download-file-by-name', bucket, b2StatsName, localStatsName])
                logging.info("Found an existing stats file, checking...")
                remoteStats = json.load(file(localStatsName))

                if cmp(remoteStats, localFileStats) <> 0:
                    logging.error("Stats disagree: {}\n{}\n".format(remoteStats, localFileStats))
                else:
                    logging.info("Stats are exactly the same!")

            except subprocess.CalledProcessError, e:
                output = subprocess.check_output(['b2', 'upload-file',  bucket, filepath, b2Filename])

                jsonString = "".join(itertools.dropwhile(lambda x: x.strip() <> '{', output.splitlines()))
                parsedOutput = json.loads(jsonString)
                logging.debug(parsedOutput)

                # copy some fields into the output
                for field in ['fileId', 'uploadTimestamp']:
                    localFileStats[field] = parsedOutput[field]

                logging.debug(localFileStats)

                jsonFile = tmpDir + "/" + sha1 + ".stats"
                with open(jsonFile, 'wt') as j:
                    json.dump(localFileStats, file(jsonFile, 'wt'))
                # upload it
                output = subprocess.check_output(['b2', 'upload-file', bucket, jsonFile, b2StatsName])


        except OSError, e:
            logging.error(e)
            return False

        return True



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Hash-upload files to B2.')
    parser.add_argument('file', nargs='+', help='files to upload')
    parser.add_argument('--loglevel', default='INFO')

    args = parser.parse_args()

    logLevel = getattr(logging, args.loglevel.upper(), None)
    if logLevel is not None:
        logging.basicConfig(loglevel=logLevel)

    logging.debug(args)



    for filepath in args.file:
        uploadFileToB2(filepath)
