# Stereoscopic Video using OpenCV and the Oculus Rift

### [Video demonstration](https://www.youtube.com/watch?v=aUCI2U5E2-8)

## Setup

This system relies on two USB video sources for video input. If two such
cameras are not connected, the program will exit noting that. Any regular USB
webcam should do, I suppose, though I'm using analog [video capture
devices][diamond].

### OS-level prerequisites

This code was developed and tested only on **Kubuntu 14.10** using **OpenCV
2.4.9**; I welcome pull requests if you find changes needed to support Windows
or other platforms. Getting Python-OpenCV set up properly on a new machine is
quite non-trivial. The best stand-alone reference I've found so far is
Sebastian Montabone's [blog post on the topic][samontab]. You should certainly
install `ffmpeg` from source. Note that on Ubuntu 14.10, you can use `libtiff5`
rather than `libtiff4`.

You'll need `python-qt4`, since `PyQt4` is strangely [not installable via
pip][pip-pyqt], despite [being on PyPI][pypi-pyqt].

### Hardware setup

To access the Oculus hardware's device in user-space, you should
download the [Oculus SDK for Linux][sdk_download] and run the
`ConfigureDebian.sh` script.

### Python libraries

We don't directly depend on the Oculus SDK, but rather use the `python-ovrsdk`
package (which is on [PyPI][pip-ovrsdk] and [github][git-ovrsdk]). I looked
around a fair bit for Python bindings that expose the Oculus SDK's image
distortion caclulations. I have yet to find those, so instead implement the
barrel distortion directly. This implementation is based directly off of the
[Argon Design blog post][argon] on this topic (I do not use the `GLUT` logic,
though pretty neat, since it introduces a lot of computational overhead).

Some dependencies are not available via `pip`, so you'll need various system
packages. I've tried to document this as I go, but it can be hard to separate
out from other, unrelated installs. Again, I welcome pull requests (or issues)
if you find mistakes.

By far the trickiest part of set up is OpenCV. I found it's possible to
successfully build OpenCV via `cmake`/`make`, and yet not have some of the
components needed for this program to run (e.g. `cv2.waitKey`). If in doubt,
step through the first part of Sebastian's blog post and pay particular
attention to the checks he details regarding `cmake`'s output.

    mkvirtualenv --system-site-packages oculus-opencv

    http://ffmpeg.org/releases/
    ./configure --enable-gpl --enable-version3 --enable-nonfree\
      --enable-postproc --enable-libfaac --enable-libopencore-amrnb\
      --enable-libopencore-amrwb --enable-libtheora\
      --enable-libvorbis --enable-libxvid --enable-x11grab\
      --enable-swscale --enable-shared
    make
    sudo make install

    wget http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.9/opencv-2.4.10.zip
    unzip opencv-2.4.10.zip
    cd ../opencv-2.4.10/
    cd build/
    cmake -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_V4L=ON\
      -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON \
      -D BUILD_EXAMPLES=ON -D WITH_QT=ON -D WITH_OPENGL=ON \
      -D WITH_VTK=ON ..
    make -j8
    sudo make install

## Usage

My video capture cards are identified as PAL format when first plugged in. To
remedy this, I set them to NTSC via a simple shell script:

```sh
./util/set-ntsc.sh 0 1
```

By default, it will try `0 1` as the video devices. Supply arguments if you
need to skip over a built-in webcam, say. The `v4l2-ctl` utility lives in the
`v4l-utils` package:

```sh
$ apt-cache search v4l2-ctl
v4l-utils - Collection of command line video4linux utilities
```

The program `qv4l2`, in the package of the same name, can be useful
for debugging the video capture devices.

The main entry-point is the `src/oculus_stream.py` file. It uses
`argparse`, so you can get basic help by running:

```sh
python src/oculus_stream.py --help
```

A few useful parameters are:

- `-O` To run without the Oculus connected, either for testing or to record
  video to a file only (it's a capital letter 'o', as in Oculus...).
- `-w` Write to a file (currently just `output.avi`).
- `-l`, `-r` specify the index of the video devices (e.g. `/dev/video0` is
  `0`). Useful if your laptop has a built-in webcam, which you want to ignore
  (or to flip the two devices left to right).

Note that `-f`, frames per second, should work properly, but in my testing, the
USB cameras are only capable of about 15 FPS. Specifying anything higher and
writing video to file will be under-sampled -- playback will appear sped-up.

I included `util/multi-stream.py`, which I wrote early on, since it's useful to
confirm the basic connectivity of the USB video sources (this is in lieu of
actual unit tests for the hardware, I suppose).

There are also a set of keyboard mappings for changing the distortion
and cropping parameters on the fly. The definitions are in
`src/algos.py` as `Parameters.key_mappings`. I've put a
[video demonstrating this on Youtube](https://www.youtube.com/watch?v=A6IgDqK26a8).

## Testing

We provide unit tests for discrete components of the system. Run the
test suite via:

```sh
python tests.py
```

So far I've mocked out  hardware (VideoCapture, OVR HMD), so that one
can run the tests without hardware connected. But as a result, don't
expect these tests to cover hardware interactions.

## Design and Discussion

The camera readers and video processor are made asynchronous via `gevent`
greenlets. I originally thought the frame rate was limited by the software
pipeline and this was an attempt to address that. It appears that, instead, the
USB capture devices that I use are limited in their framerate, but I don't
think it hurts to retain the asynchronous implementation, so I've left this
as-is.

The main objective of this program is to display the program's output on an
[Oculus Rift][rift]. If you run the program on that monitor (the Rift appears
to the host computer as a second monitor), the distortion effects will cancel
the Pincushion distortion of the Rift's lenses.

# Hardware

Purpose | Name or type | Quantity
--- | --- | ---
Video camera | [CMOS Camera][cmoscam] | 2
Video Capture | [Diamond VC500][diamond] | 2
Video transmit/receive | [5.8 GHz A/V tx/rx set][avtxrx] | 2
Computer processing | Anything with discrete graphics* | 1
Pan/tilt bracket | [Pan/Tilt bracket][sparkfun_pantilt] | 1
Servos | [Micro][sparkfun_micro] or [sub-micro servos][sparkfun_submicro] | 2
Servo Controller | [Pololu micro Maestro][maestro] | 1
Batteries | 1s or 3s [LiPo Batteries][lipo] or [regular AA/AAA][4aa] | 1+

*I initially developed this on a desktop computer with a Radeon
6700-series graphics card. Since I want to take this to the (RC
flying) field eventually, I've begun using a laptop with a GeForce GTX
850m graphic card. The current Oculus documentation seems a bit dated,
recommending only a Macbook Pro with the Nvidia 650M, which I believe
is a few years old. That, though, was my baseline criteria for what to
use.

In developing this, I've found that two USB video streams is quite
taxing on even a powerful computer. Each stream uses most of a USB
bus' bandwidth. Try to isolate the two streams on separate USB/PCI
channels -- that is, try different USB ports on your computer. Adding
the Oculus (another USB device, as well as HDMI) only further stymies
a good machine. Good luck!

# Servo drive

I use a [Pan-and-Tilt][pan_tilt] servo setup, and mount the cameras on
them. The Oculus' orientation data (yaw and pitch, particularly --
roll is not used) are taken as inputs and drive the servos. The servo
control works with Arduino using the [Servo library][servo], and
[Pololu maestro][maestro] (which I prefer since it's smaller). From
there, a simple Python script connects to the servos via
[pySerial][pyserial]. The file `src/servo/oculus-drive.py` demonstrates
this arrangement (two servos, on channels 0 and 1).

* udev rules for serial/tty

For servo control over USB (e.g. wireless serial modem or connecting
to the servo controller directly via the python script), you'll need
to add your user to the `dialout` group:

     sudo usermod -a -G dialout <you>

For connecting to the Oculus' HMD device, you will want to use the
UDEV rules from the OVR SDK:

    cd ~/Downloads/ovr_sdk_linux_0.4.4/
    cp LibOVR/90-oculus.rules /etc/udev/rules.d/
    sudo udevadm control --reload # and log back in

Note that you have to log out of (and back into) the desktop session
for UDEV rules to take effect.


[rift]: https://www.oculus.com/rift/
[sdk_download]: https://developer.oculus.com/downloads/
[diamond]: http://www.amazon.com/dp/B000VM60I8
[avtxrx]: http://www.getfpv.com/5-8ghz-32ch-fpv-av-600mw-transmitter-receiver.html
[cmoscam]: https://www.sparkfun.com/products/11745
[samontab]: http://www.samontab.com/web/2014/06/installing-opencv-2-4-9-in-ubuntu-14-04-lts/
[git-ovrsdk]: https://github.com/wwwtyro/python-ovrsdk
[pip-ovrsdk]: https://pypi.python.org/pypi/python-ovrsdk/0.3.2.2
[argon]: http://www.argondesign.com/news/2014/aug/26/augmented-reality-oculus-rift/
[pypi-pyqt]: https://pypi.python.org/pypi/PyQt4/4.11.3
[pip-pyqt]: http://superuser.com/a/725869
[pan_tilt]: https://www.sparkfun.com/products/10335
[servo]: http://arduino.cc/en/reference/servo
[pyserial]: http://pyserial.sourceforge.net/
[maestro]: https://www.pololu.com/product/1350
[sparkfun_micro]: https://www.sparkfun.com/products/10333
[sparkfun_submicro]: https://www.sparkfun.com/products/9065
[sparkfun_pantilt]: https://www.sparkfun.com/products/10335
[lipo]: http://www.hobbytown.com/Shop/EFLB5001S25-E-Flite-500mAh-1S-3-7V-25C-LiPo-Battery/
[4aa]: http://www.radioshack.com/radioshack-4-aa-battery-holder/2700383.html#.VUa09eRgsUE
