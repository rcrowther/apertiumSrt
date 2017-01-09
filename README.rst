apertiumSrt
=========
Python3 script to convert an .srt subtitle file for translation by Apertium


Why?
~~~~~
You want your film subtitles in Gaelic, Maltese, or...

Use
~~~
Convert an .srt subtitle file for translation by Apertium

Works for SubRip stock format, and a (ripped?) dialect found on the web
e.g. '00:01:00.18,00:01:02.26'

Run the file through the converter::

    srtConv -c='latin-1' en-es gone_with_the_wind.srt

It will output a superblanked file called 'gone_with_the_wind_lang1.apy'.
This can be input to Apertium::

    apertium -un en-es gone_with_the_wind_lang1.apy gone_with_the_wind_lang2.apy
  
Then remove blanks from 'gone_with_the_wind_lang2.apy' (a text editor 
can do this) for the final translated subtitle file.

If a pair is given, the script will attempt to invoke Apertium from
a subcomand::

    srtConv -c='latin-1' en-es gone_with_the_wind.srt
  
If this succeeds, the result is a translated file in the same directory
called 'gone_with_the_wind-es.srt'

Requires
~~~~~~~~
Python3. If Apertium is installed, the script can use the installation to convert the file directly.

