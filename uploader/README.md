Auto Uploader
====


Why?
---

I enjoy taking photos with a real camera (i.e. not a cellphone).  However, after having kids it became harder to find time to sit down at a computer to upload (and to adjust) photos. This is why I have made a little photo upload station using Raspberry Pi. The goal here is to have a hassle-free way to save photos and videos in original qualty in a way that allows easy access and sharing later.

What? 
---
This directory contains instructions, configs files, and
scripts that I used to turn my Raspberry Pi into a photo
upload station. If you follow these instructions, your RaspberryPi
uploader will automatically upload all photos from an
SD/Flash card to your Amazon Cloud Drive account. All you
need to do is to walk to up the uploader, plugin the SD/flash
card and walk away. If you have two SD/flash cards, you can
simply swap cards and continue taking photos with a new one.

If you use (free) Amazon Photos app, you'll see new JPEG photos
uploaded to your account seconds after you plug your storage
media into the uploader.
 

Setup instructions
===

Hardware that you will need:
- RaspberryPi 2 + WiFi card (or some other internet
  connection) OR RaspberryPi 3 (which includes a Wifi chip)
- SD/Flash reader (which one you get depends on your camera,
  if your camera is new, you probably just want an SD
    reader)
 
Accounts:
- Amazon Cloud Drive account (this comes free with Amazon Prime
  or a seprate service as Amazon Photos)

Software setup:
- [Configure networking for RaspberryPi](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-3-network-setup/overview)
- Configure mounting of your media:
  - enable support for large SD/Flash cards that use Extended FAT filesystem
  ~~~
  sudo apt-get install exfat-fuse exfat-utils
  ~~~
  - [install udisk-glue from source](http://angryelectron.com/udisks-glue-on-ubuntu-14-04/) (note: installing binaries does not work for me on RPI2)
- Setup ACD_CLI ( https://github.com/yadayada/acd_cli.git ):
  ~~~
  # install Python 3 pip
  sudo apt-get install python3-pip

  # install ACD_CLI
  sudo pip3 install --upgrade git+https://github.com/yadayada/acd_cli.git

  # configure acd_cli to your user Amazon account
  acd_cli sync
  # this will display a URL that you should psate into a browser
  # after you enter your password oauth_data file will be downloaded 
  # copy the contents of this file to your RaspberryPi
  # to /home/pi/.cache/acd_cli/oauth_data
  ~~~ 
- Update your configs and setup the auto-upload script
  ~~~
  git clone https://github.com/vbychkovsky/shared.git
  # setup the upload script
  cp shared/uploader/onmount.sh /home/pi/

  # this script needs to run as root
  sudo chmod u+s /home/pi/onmount.sh

  # update udisk-glue config
  sudo cp shared/uploader/udisks-glue.conf /etc/
  ~~~

- Profit!
At this point you should have a working uploader.


Notes
===
 
Related work 
---

At the time I've created this setup for myself there were no
other RaspberryPi-based photo uploaders. However, the recent
publication of [Flickrup by Eduardo
Balsa](https://github.com/drcursor/flickrup) inspired me to
publish the details of my setup. Flickrup setup is simpler
than mine (so I encourge you to try it if the above seems
too complicated). The major difference (aside from using
Flickr) is that usbmount script is used for triggering
uploads. In my limited expereince this usbmount seems to
hang if the SD card is removed during upload, while
udisks-glue seem with the above configuration is very robust
in my experience. However, your milage may vary.


Why Amazon Photos (and not Flickr/Google/etc)?  
--- 

As of 2015, Amazon Photos is the cheapest photo/video
storage service that enables storage of original photos
(JPEG and raw) and videos. It also has website that allows
you to download and manage your photos as well as a mobile
app.  This app automatically syncs photos and videos I take
with my cellphone. The key point is that I get all my media
backed up in one place without any loss of quality (aka
compression).

Flickr does not support raw photo storage and does not allow
movie uploads at all. With Google photos you either pay a
lot more per GB of storage of original photos or store only
JPEGs. There may be a way to user Google Photos for JPEGs
only, but this complicates the setup a bit.

Backblaze becomes cheaper per GB than Amazon Photos after you have
 \>1TB of storage. The downside is that I'd have to write my
own app to allow for access. Also, Amazon Photos handles
video re-encoding so that your videos can be viewed on
different platforms (iOS/Android/Web).


ToDo / wishlist
---
- add video/photos of what the results looks like
- is it possible to avoid having the script run as root?
- modularize the script to allow for different backends,
  like Google Photos, Flickr, and/or Backblaze.
- do cron-based retries if Amazon's throttling


P.S. Your suggestions/corrections/ideas for any of the above are
welcome. E-mail me at vladb at csail.mit.edu or just create
a pull-request.


