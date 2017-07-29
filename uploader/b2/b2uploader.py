#!/usr/bin/env python

import argparse
import hashlib
import subprocess

def computeSHA1(filename, blocksize=None):
    sha1 = hashlib.sha1()

    if blocksize is None:
        blocksize = sha1.block_size

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), ''):
           sha1.update(chunk)
    return sha1.hexdigest()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Hash-upload files to B2.')
    parser.add_argument('file', nargs='+', help='files to upload')

    bucket = "myPublic1"
    hashDir = "hash"
    infoFile = "info.txt"
    tmpDir = "/tmp"

    args = parser.parse_args()
    print(args) # ToDo: remove

    for filepath in args.file:
        try:
            print("processing {}...".format(filepath))
            sha1 = computeSHA1(filepath)
            print("sha1: {}".format(sha1))
        
            # check if file is already there (download the link)
            b2Filename = "{hashDir}/{sha1}/{infoFile}".format(**dict(globals(), **locals()))
            localFilename = tmpDir + "/" + sha1
            print("Attempting to download '{}'".format(b2Filename))
            res = subprocess.call(['b2', 'download-file-by-name', bucket, b2Filename, localFilename])
            print("return code: {}, file: {}".format(res, localFilename))
            if res == 0:
                # ToDo: check the file contents...
                print("File already uploaded")
            else:
                print("Attempting to upload file")
                res = subprocess.call(['b2', 'upload-file',  bucket, filepath, b2Filename])        
                if res <> 0:
                    print("Upload failed")
                

            
        except IOError, e:
            print(e)

        

