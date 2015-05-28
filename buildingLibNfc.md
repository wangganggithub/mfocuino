We just need to build lib nfc configured with the uart driver.
But you need to apply patch to make it work.

# Patch #

The patch is in the svn source tree :
https://code.google.com/p/mfocuino/source/browse/trunk/nfcreader/libnfc.uart.patch

```
patch -p0 < libnfc.uart.patch
```

What does the patch do :
  * it just configure the uart default speed to 921600. You can change this value but you need to configure the same speed on the arduino driver.
  * it add a delay in the pn53x\_check\_communication otherwise the arduino does not have the time to respond and the reader will not be recognize by libnfc.

# Build #

Build the libnfc with the uart driver :
use --enable-debug if you want the debug trace

```
./configure --with-drivers=pn532_uart --enable-serial-autoprobe (--enable-debug)
```