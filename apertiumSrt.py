#!/usr/bin/python3

import os.path
import os
import re
import argparse
import sys
import subprocess



'''
Convert an .srt subtitle file for translation by Apertium

Works for SubRip stock format, and a (ripped?) dialect found on the web
e.g. '00:01:00.18,00:01:02.26'

Run the file through the converter. 

  srtConv -c='latin-1' en-es gone_with_the_wind.srt

It will output a superblanked file called 'gone_with_the_wind_lang1.apy'.
This can be input to Apertium,

  apertium -un en-es gone_with_the_wind_lang1.apy gone_with_the_wind_lang2.apy
  
Then remove blanks from 'gone_with_the_wind_lang2.apy' (a text editor 
can do this) for the final translated subtitle file.

If a pair is given, the script will attempt to invoke Apertium from
a subcomand.

  srtConv -c='latin-1' en-es gone_with_the_wind.srt
  
if this succeeds, the result is a translated file in the same directory
called 'gone_with_the_wind-es.srt'
'''
## TODO: Stash a whole stanza, check for errors
# path on cl
# encoding on cl
# decoding option
# default optput -lang2.apy



    
def _apertiumExecute(srcPath, dstPath, langPair):
    success = False
    # -u dont show missing matrks
    # -n don't guess at full-stops
    cmd = ['apertium', '-un', langPair, srcPath, dstPath]
    printMessage('translate command: ' + ' '.join(cmd))
    try:
        subprocess.call(cmd)
        success = True
    except Exception as e:
        print(e)
    return success

def printMessage(msg):
    print(msg)

def printInfo(msg):
    print('[info] {0}'.format(msg))

def printError(msg):
    print('[error] {0}'.format(msg))    
    
class SRTParser():
    '''
    SRT parser with callbacks.
    Like the Python HTML parrer, etc.
    Not the last word, will not catch a malformed file.
    Will handle initial text processing attributes, comma 
    time-bound lines (not '-->'), and missing stanza numbers
    Callbacks return formally correct data i.e. 
    no intro texts,
    sequential numbering,
     '-->' separator,
    single linend finish to text.
    '''
    def __init__(self):
        self.reset()

    def feed(self, text):
        self.inBuf = text.split('\n')
        self._dispatch()

    def close(self):
        # dispatch remaining stanza
        self._dispatchAndReset()
        pass

    def reset(self):
        self.lineNum = 1
        self.stanzaNum = 0
        self.stanzaTime = ('','')
        self.stanzaTextBuf = []
        self.readingTextEntry = False
        self.inBuf = []
        self.errors = []
        
    def getLineNum(self):
        return self.lineNum

    def getStanzaNum(self):
        return self.stanzaNum

    def _dispatchAndReset(self):
        if (self.stanzaNum == 0):
            self.stanzaNum += 1
            # may need clearing - initial text formatting info etc.
            self.stanzaTextBuf = []
        else:            
            # stanza count
            self.handleCount(self.stanzaNum)
            self.stanzaNum += 1
    
            # time attribute 
            sTime, eTime = self.stanzaTime
            self.handleTimes(sTime, eTime)
            self.stanzaTime = ('','')
            
            # text
            txt = '\n'.join(self.stanzaTextBuf)
            self.handleText(txt)
            self.stanzaTextBuf = []
    
                  
    def _dispatch(self):
        for line in self.inBuf:
            self.lineNum += 1

            l = line.strip()
            
            if(l.isnumeric() or not l):
              # must be a count line
              # ignore?
              pass

            elif '-->' in l:
                self._dispatchAndReset()
                sTime, eTime = l.split('-->')
                self.stanzaTime = (sTime.rstrip(), eTime.lstrip())
            elif (l[0].isnumeric() and ',' in l):
                # found on the web
                # '00:01:00.18,00:01:02.26'
                # looks americanized, and a DVD rip? Needs microseconds 
                # boosting to three, periods to commas, comma to '-->'
                # and stanzaNum inserting (stanzaNum is automatic in 
                # this script)
                # TODO: test weird markup bracket syntax e.g.
                # me Confío en.[br] He sido haciendo él para nueve años
                self._dispatchAndReset()
                sTime, eTime = l.split(',')
                startTime = sTime.rstrip().replace('.', ',') + '0'
                endTime = eTime.lstrip().replace('.', ',') + '0'
                self.stanzaTime = (startTime, endTime)

              # now we are doing this
              #self.readingTextEntry = True
            else:
              # only gather line if not empty
              #if l:
              self.stanzaTextBuf.append(l)

    def handleCount(self, num):
        '''
        type is integer
        '''
        pass
 
    def handleTimes(self, startTimeStr, endTimeStr):
        '''
        types are strings
        '''
        pass

    def handleText(self, text):
        '''
        type is one string with single line ending. 
        Other line endings may be inserted if the stanza text was split 
        into lines.
        '''
        pass


#subprocess
class ToApertiumParser(SRTParser):
    def __init__(self):
        SRTParser.__init__(self)
        self.b = []

    def result(self):
        return "".join(self.b)

    def handleCount(self, num):
        self.b.append('[\n')
        self.b.append(str(num))
        self.b.append('\n')

    def handleTimes(self, startTime, endTime):
        self.b.append(startTime)
        self.b.append(' --> ')
        self.b.append(endTime)
        #self.b.append('\n')
        self.b.append('\n]\n')

    def handleText(self, text):
        self.b.append(text)
        self.b.append('\n\n')
       

'''
After this, run
cat dstPath | apertium -un lang_pair > emma-eng_lanc.apy

-u don't display unknown
-n don't insert periods (by guessing)
'''
def mkLang1Apy(args, srcApyPath):
    srcAsLines = None
    
    with open(args.infile, 'r', encoding=args.codec) as f:
        srcAsLines = "\n".join(f.readlines())
    
    parser = ToApertiumParser()
    parser.feed(srcAsLines)
    parser.close()

    with open(srcApyPath, 'w', encoding=args.codec) as f:
        f.write(parser.result())


def mkLang2Apy(args, srcApyPath, dstSrtPath):
    # this is a tmp file for further processing
    dstApyPath = os.path.join(args.workingDir, '{0}_lang2_srt.apy'.format(args.baseName))

    # translate
    printMessage('translating... langPair:{0}'.format(args.pair))
    success = _apertiumExecute(srcApyPath, dstApyPath, args.pair)
    if (not success):
        self.printError('Apertium autorun failed. A file contains the superblanked srt text.\npath:{}'.format(srcApyPath))
        sys.exit(1)
    os.remove(srcApyPath) 
    
    # import translated text
    printMessage('deformatting...')
    translatedText = ''
    # TODO: catch exceptions?
    with open(dstApyPath, 'r', encoding=args.codec) as f:
        translatedText = "".join(f.readlines())
        
    # strip superblanks
    stripRE = re.compile('(\n\[)|(\n\])')
    startSlicedText = translatedText[1:] if (translatedText[0] == '[') else translatedText
    superblankStripped = stripRE.sub('', startSlicedText)
    
    # output to file
    # TODO: catch exceptions?
    with open(dstSrtPath, 'w', encoding=args.codec) as f:
        f.write(superblankStripped)
    os.remove(dstApyPath) 
    

def reformat():
    pass
    
def main(argv):
    parser = argparse.ArgumentParser(
        #epilog= "NB: keynames in the internal 'stanza' variable must be adjusted to match input files"
        )


    parser.add_argument("-c", "--codec",
        default='UTF-8',
        help="encoding of source file."
        )
        
    parser.add_argument("-p", "--pair", 
        default=None,
        help="a pair to use for translation. Will assume Apertium is installed on the system"
        )
        
    parser.add_argument("-o", "--outfile", 
        default='',
        help="file path for output"
        )
        
    parser.add_argument("infile", 
        default='in.srt',
        help="file for input"
        )
                
    args = parser.parse_args()

    # assert infile as absolute path
    args.infile = os.path.abspath(args.infile)

    f = args.infile
    if (not os.path.exists(f)):
        printError('Path not exists path: {0}'.format(f))
        return 1
        
    if (os.path.isdir(f)):
        printError('Path is dir path: {0}'.format(f))
        return 1

    # set output directory to inFile directory            
    (args.workingDir, name) = os.path.split(args.infile)
    
    # baseName is everything to the dot separator for extension, if it exists
    idx = name.find('.')
    args.baseName = name if(idx == -1) else name[0:idx]
 

    if (args.pair):
        (args.srcLanguage, args.dstLanguage) = args.pair.split('-')

    print ('infile:' + str(args.infile))
    print ('workingDir:' + str(args.workingDir))
    print ('baseName:' + str(args.baseName))
    print ('codec:' + str(args.codec))
    print ('outfile:' + str(args.outfile))
    if (args.pair):
        print ('srcLanguage:' + str(args.srcLanguage))
        print ('dstLanguage:' + str(args.dstLanguage))
    print ('\n')
    
    
    
    #try:


    if (not args.pair):
        if (args.outfile):
            srcApyPath = args.outfile
        else:
            srcApyPath = os.path.join(args.workingDir, '{0}_lang1_srt.apy'.format(args.baseName))     
        mkLang1Apy(args, srcApyPath)

        printInfo('written file for Apertium input: path: {0}'.format(srcApyPath))
    else:
        # this is a tmp file for further processing
        srcApyPath = os.path.join(args.workingDir, "{0}-{1}_srt.apy".format(args.baseName, args.dstLanguage))
        mkLang1Apy(args, srcApyPath)

        if (args.outfile):
            dstSrtPath = args.outfile
        else:
            dstSrtPath = os.path.join(args.workingDir, '{0}-{1}.srt'.format(args.baseName, args.dstLanguage))
        mkLang2Apy(args, srcApyPath, dstSrtPath)
        
        printInfo("written final 'srt' file: path: {0}".format(dstSrtPath))

    #except Exception as e:
     #   print('Error: most errors are caused by wrong format for source. Other errors from malformed files?\n{0}'.format(e))
        
        
if __name__ == "__main__":
    main(sys.argv[1:])
