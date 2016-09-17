#!/bin/bash

# This script uploads photos (and movies) from specified media to Amazon Cloud Drive.
# Original source: https://github.com/vbychkovsky/shared
# License: Affero GNU Public License 3.0 (http://www.gnu.org/licenses/agpl-3.0.txt)
#
# Requirements:
# - acd_cli is installed and configured with access to your Amazon Cloud Drive:
#   https://github.com/yadayada/acd_cli.git
#
# Notes:
# - files that have been uploaded successfuly are deleted from the media (UPLOADFLAGS)
# - failed uploads are retried 5 times (UPLOADFLAGS)
# - if upload does not succeed after 5 retries, the file is left on the media.
# - order of uploads: JPEG, raw (.raw, .nef, cr2), .mov
# - directory structure for uploads:
#   $AMAZON$/Pictures/autouploads/YYYY_MM/DD/ -- root dir with the upload date
#     raw files and movies are upload here
#     jpeg files are upload into subdirector JPEG

MOUNTPOINT=$1
ACD=acd_cli
ACDROOT=/Pictures/autouploads
SUBDIR=`date +%Y_%m/%d`

UPLOADFLAGS='--remove-source-files -r 5'

echo "Started mounted script for [$MOUNTPOINT] to $SUBDIR"

$ACD sync

echo "Uploading JPEG files..."
JPEGS=`find $MOUNTPOINT -iname "*.jp*"`
JPEGDIR=$ACDROOT/$SUBDIR/JPEG
$ACD mkdir --parents $JPEGDIR
$ACD upload $UPLOADFLAGS $JPEGS $JPEGDIR

echo "Uploading RAW files..."
RAW=`find $MOUNTPOINT -iname "*.raf" -iname "*.nef" -iname "*.cr2" -iname "*.cr2"`
RAWDIR=$ACDROOT/$SUBDIR
$ACD upload $UPLOADFLAGS $RAW $RAWDIR


# Uncomment the following lines to enable upload of MOV files
#echo "Uploading MOV files..."
#MOV=`find $MOUNTPOINT -iname "*.mov"`
#MOVDIR=$ACDROOT/$SUBDIR
#$ACD upload $UPLOADFLAGS $MOV $MOVDIR


echo "done uploading, unmounting the disk..."
umount $MOUNTPOINT
echo "done unmounting"

