#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# USFMBibleBook.py
#
# Module handling the importation of USFM Bible books
#
# Copyright (C) 2010-2019 Robert Hunt
# Author: Robert Hunt <Freely.Given.org@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module for defining and manipulating USFM Bible books.
"""

from gettext import gettext as _

LastModifiedDate = '2019-12-22' # by RJH
ShortProgName = "USFMBibleBook"
ProgName = "USFM Bible book handler"
ProgVersion = '0.53'
ProgNameVersion = '{} v{}'.format( ShortProgName, ProgVersion )
ProgNameVersionDate = '{} {} {}'.format( ProgNameVersion, _("last modified"), LastModifiedDate )

debuggingThisModule = False


from typing import Dict, List, Tuple, Any, Optional
import os
import logging

if __name__ == '__main__':
    import sys
    sys.path.append( '.' ) # So we can run it from the above folder and still do these imports
import BibleOrgSysGlobals
from InputOutput.USFMFile import USFMFile
from Bible import BibleBook
from Internals.InternalBibleBook import cleanUWalignments


sortedNLMarkers = None



class USFMBibleBook( BibleBook ):
    """
    Class to load and manipulate a single USFM file / book.
    """

    def __init__( self, containerBibleObject, BBB ):
        """
        Create the USFM Bible book object.
        """
        BibleBook.__init__( self, containerBibleObject, BBB ) # Initialise the base class
        self.objectNameString = 'USFM Bible Book object'
        self.objectTypeString = 'USFM'

        global sortedNLMarkers
        if sortedNLMarkers is None:
            sortedNLMarkers = sorted( BibleOrgSysGlobals.USFMMarkers.getNewlineMarkersList('Combined'), key=len, reverse=True )
    # end of USFMBibleBook.__init__


    def load( self, filename:str, folder:Optional[str]=None, encoding:Optional[str]=None ) -> None:
        """
        Load the USFM Bible book from a file.

        Tries to combine physical lines into logical lines,
            i.e., so that all lines begin with a USFM paragraph marker.

        Uses the addLine function of the base class to save the lines.

        Note: the base class later on will try to break apart lines with a paragraph marker in the middle --
                we don't need to worry about that here.
        """
        #print( f"load( filename={filename}, folder={folder}, encoding={encoding} )…" )


        def doaddLine( originalMarker, originalText ):
            """
            Check for newLine markers within the line (if so, break the line) and save the information in our database.

            Also convert ~ to a proper non-break space.
            """
            #print( "doaddLine( {!r}, {!r} )".format( originalMarker, originalText ) )
            marker, text = originalMarker, originalText.replace( '~', ' ' )
            if '\\' in text: # Check markers inside the lines
                markerList = BibleOrgSysGlobals.USFMMarkers.getMarkerListFromText( text )
                ix = 0
                for insideMarker, iMIndex, nextSignificantChar, fullMarker, characterContext, endIndex, markerField in markerList: # check paragraph markers
                    if insideMarker == '\\': # it's a free-standing backspace
                        loadErrors.append( _("{} {}:{} Improper free-standing backspace character within line in \\{}: {!r}").format( self.BBB, C, V, marker, text ) )
                        logging.error( _("Improper free-standing backspace character within line after {} {}:{} in \\{}: {!r}").format( self.BBB, C, V, marker, text ) ) # Only log the first error in the line
                        self.addPriorityError( 100, C, V, _("Improper free-standing backspace character inside a line") )
                    elif BibleOrgSysGlobals.USFMMarkers.isNewlineMarker(insideMarker) \
                    or insideMarker == 'zaln-e': # Need to split the line for everything else to work properly
                        if ix==0:
                            loadErrors.append( _("{} {}:{} NewLine marker {!r} shouldn't appear within line in \\{}: {!r}").format( self.BBB, C, V, insideMarker, marker, text ) )
                            logging.error( _("NewLine marker {!r} shouldn't appear within line after {} {}:{} in \\{}: {!r}").format( insideMarker, self.BBB, C, V, marker, text ) ) # Only log the first error in the line
                            self.addPriorityError( 96, C, V, _("NewLine marker \\{} shouldn't be inside a line").format( insideMarker ) )
                        thisText = text[ix:iMIndex].rstrip()
                        self.addLine( marker, thisText )
                        ix = iMIndex + 1 + len(insideMarker) + len(nextSignificantChar) # Get the start of the next text -- the 1 is for the backslash
                        #print( "Did a split from {}:{!r} to {}:{!r} leaving {}:{!r}".format( originalMarker, originalText, marker, thisText, insideMarker, text[ix:] ) )
                        marker = insideMarker # setup for the next line
                if ix != 0: # We must have separated multiple lines
                    text = text[ix:] # Get the final bit of the line
            self.addLine( marker, text ) # Call the function in the base class to save the line (or the remainder of the line if we split it above)
        # end of doaddLine


        MAX_EXPECTED_NESTING_LEVELS = 20 # Don't allow unlimited nesting

        def handleUWAlignment( marker:str, text:str, variables:Dict[str,Any] ) -> Tuple[str,str]:
            """
            Extracts all of the uW alignment information.

            Alters variables dict as a side-effect.

            Returns a new marker and text with uW alignment markers removed.
            """
            if debuggingThisModule:
                print( f"{self.BBB} {C}:{V}" )
                print( f"handleUWAlignment( {marker}={text!r}\n            lev={variables['level']}, aText='{variables['text']}', aWords='{variables['words']}' )…" )
            if variables['text']:
                assert variables['text'].startswith( 'x-strong="' )
                assert variables['text'].endswith( '"' )
                assert 'zaln' not in variables['text']
            if variables['words']:
                if not BibleOrgSysGlobals.strictCheckingFlag:
                    variables['words'] = variables['words'].rstrip() # Shouldn't really be necessary
                #assert variables['words'].startswith( '\\w ' ) # Not currently true (e.g., might have verse number)
                assert variables['words'].endswith( '"\\w*' ) \
                or (variables['words'][-1] in BibleOrgSysGlobals.TRAILING_WORD_PUNCT_CHARS
                    and variables['words'][-5:-1] == '"\\w*' )
                assert 'zaln' not in variables['words']
            if variables['level'] > MAX_EXPECTED_NESTING_LEVELS: halt


            def findInternalStarts( marker:str, text:str, variables:Dict[str,Any] ) -> Tuple[str,str]:
                """
                Finds self-closed alignment start markers that may occur inside the line.

                Removes the markers, and incrementes variables['level']
                    and appends the enclosed text to the variables['text'] variable
                Thus alters variables dict as a side-effect.

                Returns a new marker and text with uW start alignment markers removed.
                """
                if debuggingThisModule: print( f"  findInternalStarts( {marker!r}, {text!r}, lev={variables['level']}, aText='{variables['text']}', aWords='{variables['words']}' )…" )
                assert marker not in ('zaln-s','zaln-e')

                for numFound in range( 99 ):
                    ixAlignmentStart = text.find( '\\zaln-s | ' )
                    if ixAlignmentStart == -1:
                        if text.find('zaln-s') > 0:
                            logging.error( f"Found unexpected 'zaln-s' without backslash in {self.BBB} {C}:{V} {marker}='{text}'" )
                        break # Didn't find it
                    #else: # Found start marker
                    lookForCount = max( 1, variables['level'] ) # How many consecutive self-closed end-markers to search for
                    ixAlignmentEnd = text.find( '\\zaln-e\\*' * lookForCount )
                    if ixAlignmentEnd!=-1 and ixAlignmentEnd < ixAlignmentStart:
                        # Usually this happens around punctuation such as Hebrew maqqef (where spaces aren't wanted)
                        # We have to process the end first
                        assert variables['level'] > 0
                        if debuggingThisModule: print( f"        Found {variables['level']} end markers inside line" )
                        assert variables['text']
                        if marker == 'SWAPPED': assert not variables['words']
                        variables['words'] += text[:ixAlignmentEnd] if marker=='SWAPPED' \
                                                else f' \\{marker} {text[:ixAlignmentEnd]}'
                        assert variables['words']
                        #print( "words1", variables['words'] )
                        assert '\\w*\\w' not in variables['words']
                        variables['saved'].append( (C,V, variables['text'], variables['words']) )
                        text = text[:ixAlignmentEnd] + text[ixAlignmentEnd+9*lookForCount:]
                        variables['text'] = variables['words'] = ''
                        variables['level'] = 0
                        if debuggingThisModule: print( f"      Decreased level to {variables['level']}" )
                        assert variables['level'] >= 0
                        if debuggingThisModule: print( f"      Now got rest='{text}'" )
                        continue
                    assert 'zaln-e' not in text[:ixAlignmentStart] # Make sure our nesting isn't confused
                    ixAlignmentStartEnding = text.find( '\\*' ) # Even start marker should be closed
                    if ixAlignmentStartEnding == -1: # Wasn't self-closing
                        loadErrors.append( _("{} {}:{} Unclosed '\\{}' Door43 custom alignment marker at beginning of line (with no text)") \
                                        .format( self.BBB, C, V, marker ) )
                        logging.warning( _("Unclosed '\\{}' Door43 custom alignment marker after {} {}:{} at beginning of line (with no text)") \
                                        .format( marker, self.BBB, C, V ) )
                        halt # Error messages need fixing
                    else: # self-closing was ok
                        variables['level'] += 1
                        if variables['level'] > variables['maxLevel']: variables['maxLevel'] = variables['level']
                        if variables['level'] > MAX_EXPECTED_NESTING_LEVELS: halt
                        if debuggingThisModule: print( f"      Increased level to {variables['level']}" )
                        variables['text'] += ('|' if variables['text'] else '') \
                                                + text[ixAlignmentStart+10:ixAlignmentStartEnding]
                        if debuggingThisModule: print( f"      Now got alignmentText='{variables['text']}'" )
                        text = text[:ixAlignmentStart] + text[ixAlignmentStartEnding+2:]
                        if debuggingThisModule: print( f"      Now got rest='{text}'" )

                #if variables['level'] > 0:
                    #variables['words'] += f'{marker} {text}'

                if debuggingThisModule: print( f"    findInternalStarts returning {marker!r}, {text!r} with lev={variables['level']}, aText='{variables['text']}', aWords='{variables['words']}'" )
                assert 'zaln-s' not in text
                return marker, text
            # end of findInternalStarts function


            # handleUWAlignment function main code
            if marker == 'zaln-s':
                assert not variables['text']
                assert text.startswith('| ')
                # Put marker into line then we can use the same function for inline milestone starts
                marker, text = findInternalStarts( 'SWAPPED', f'\\{marker} {text}', variables )

                ##assert 'zaln-e' not in text # NOT TRUE
                #if self.containerBibleObject:
                    #ixEnd1 = text.find( '\\*' )
                    #if ixEnd1 == -1: # Wasn't self-closing
                        #loadErrors.append( _("{} {}:{} Unclosed '\\{}' Door43 custom alignment marker at beginning of line (with no text)") \
                                        #.format( self.BBB, C, V, marker ) )
                        #logging.warning( _("Unclosed '\\{}' Door43 custom alignment marker after {} {}:{} at beginning of line (with no text)") \
                                        #.format( marker, self.BBB, C, V ) )
                    #else: # self-closing was ok
                        #variables['level'] += 1
                        #if variables['level'] > variables['maxLevel']: variables['maxLevel'] = variables['level']
                        #variables['text'], text = text[2:ixEnd1], text[ixEnd1+2:]
                        #if debuggingThisModule:
                            #print( f"Got alignmentText='{variables['text']}'" )
                            #print( f"Got rest='{text}'" )
                        #marker = 'p~'
                        #marker, text = findInternalStarts( marker, text, variables ) # Could be more
                        ##ixEnd2 = text.find( '\\zaln-e\\*' )
                        ##if ixEnd2 == -1: # No end alignment marker
                            ##variables['alignmentWords'] += text
                        ##else: # Got self-closed alignment end marker
                            ##variables['alignmentWords'] += text[:ixEnd2]
                            ##variables['alignments'][variables['alignmentText']] = variables['alignmentWords']
                            ##variables['alignmentText'], variables['alignmentWords'] = None, ''
                            ##text = text[:ixEnd2] + text[ixEnd2+9:]
                            ##assert 'zaln' not in text
                #else:
                    #loadErrors.append( _("{} {}:{} Removed '\\{}' Door43 custom alignment marker at beginning of line (with no text)") \
                                    #.format( self.BBB, C, V, marker ) )
                    #logging.warning( _("Removed '\\{}' Door43 custom alignment marker after {} {}:{} at beginning of line (with no text)") \
                                    #.format( marker, self.BBB, C, V ) )
                    #marker = '' # so it gets deleted

            elif marker == 'zaln-e': # unexpected
                logging.critical( "Didn't expect zaln-e marker at beginning of line" )
                halt

            # Could be v, w, etc. -- now look inside the text
            marker, text = findInternalStarts( marker, text, variables ) # Could be more

                #ixStart1 = text.find( '\\zaln-s | ' )
                #if ixStart1 == -1:
                    #if text.find('zaln-s') > 0:
                        #logging.error( f"Found unexpected 'zaln-s' in {self.BBB} {C}:{V} {marker}='{text}'" )
                #else: # Found it
                    #assert ixStart1 < 8 # Should be near the start of the line
                    #assert not variables['text']
                    #ixEnd1 = text.find( '\\*' )
                    #if ixEnd1 == -1: # Wasn't self-closing
                        #loadErrors.append( _("{} {}:{} Unclosed '\\{}' Door43 custom alignment marker at beginning of line (with no text)") \
                                        #.format( self.BBB, C, V, marker ) )
                        #logging.warning( _("Unclosed '\\{}' Door43 custom alignment marker after {} {}:{} at beginning of line (with no text)") \
                                        #.format( marker, self.BBB, C, V ) )
                    #else: # self-closing was ok
                        #variables['text'], text = text[ixStart1+10:ixEnd1], text[ixEnd1+2:]
                        #print( f"Got1 alignmentText='{variables['text']}'" )
                        #print( f"Got1 rest='{text}'" )

                #if variables['alignmentText']:
                    #ixEnd4 = text.find( '\\zaln-e\\*' )
                    #if ixEnd4 == -1: # No end alignment marker
                        #variables['alignmentWords'] += f'\{marker} {text}' if marker=='w' else text
                        #print( f"NoEnd1 alignmentWords='{variables['alignmentWords']}'" )
                    #else: # Found alignment end marker
                        #variables['alignmentWords'] += f'\{marker} {text[:ixEnd4]}' if marker=='w' else text[:ixEnd4]
                        #variables['alignments'][variables['alignmentText']] = variables['alignmentWords']
                        #print( f"GotEnd1 alignmentWords='{variables['alignmentWords']}'" )
                        #variables['alignmentText'], variables['alignmentWords'] = None, ''
                        #text = text[:ixEnd4] + text[ixEnd4+9:]
                        #assert 'zaln' not in text

            # Look for any self-closed end-alignment milestones
            if variables['level'] > 0:
                if debuggingThisModule: print( f"      Looking for {variables['level']} end markers..." )
                endMarkers = '\\zaln-e\\*' * variables['level']
                ixEndMarkers = text.find( endMarkers )
                assert ixEndMarkers != 0 # Not expected at the beginning of a line
                if ixEndMarkers > 0: # Found end alignment marker(s)
                    if debuggingThisModule: print( f"        Found {variables['level']} end markers" )
                    assert variables['text']
                    if marker == 'SWAPPED': assert not variables['words']
                    variables['words'] += text[:ixEndMarkers] if marker=='SWAPPED' \
                                            else f' \\{marker} {text[:ixEndMarkers]}'
                    assert variables['words']
                    #print( "words2", variables['words'] )
                    #assert '\\w*\\w' not in variables['words']
                    variables['saved'].append( (C,V, variables['text'], variables['words']) )
                    text = text[:ixEndMarkers]
                    assert not text[ixEndMarkers+len(endMarkers):] # End markers expected at the end of the line
                    variables['text'] = variables['words'] = ''
                    variables['level'] = 0
                    if debuggingThisModule: print( "      Reset level to zero" )
                    #if debuggingThisModule: print( f"      Decreased level to {variables['level']}" )
                    #assert variables['level'] >= 0
                elif '\\zaln-e' in text:
                    logging.critical( f"Not enough zaln-e markers (expected {variables['level']}) in {marker}={text}" )
                    halt # Not enough zaln-e markers
                else:
                    #assert '\\w*\\w' not in variables['words']
                    #print( self.wordName, self.BBB, C, V, "words3a", variables['words'] )
                    #print( f"{marker}={text}" )
                    if marker == 'SWAPPED': assert not variables['words']
                    variables['words'] += text if marker=='SWAPPED' else f' \\{marker} {text}'
                    #print( "words3b", variables['words'] )
                    #assert '\\w*\\w' not in variables['words']

            if debuggingThisModule: print( f"Got near end1 with {marker}='{text}'" )
            assert 'zaln' not in text # because we have no open levels
            if marker == 'SWAPPED': # then we need to supply a remaining marker
                if debuggingThisModule: print( f"Got near end2 with {marker}='{text}'" )
                if text.startswith( '\\w ' ): marker = 'p~'
            assert marker != 'SWAPPED'
            if debuggingThisModule: print( f"  handleUWAlignment returning {marker!r}, {text!r} with lev={variables['level']}, aText='{variables['text']}', aWords='{variables['words']}'" )
            assert 'zaln' not in variables['text']
            assert '\\w' not in variables['text']
            assert 'zaln' not in variables['words']
            return marker, text
        # end of handleUWAlignment


        # Main code for USFMBibleBook.load()
        issueLinePositioningErrors = True # internal markers at beginning of line, etc.
        #print( "OBNS", self.containerBibleObject.objectNameString )
        #print( dir(self.containerBibleObject) )

        gotUWAligning = False
        alignmentVariables = { 'level':0, 'maxLevel':0, 'text':'', 'words':'', 'saved':[] }
        try:
            if self.containerBibleObject.uWaligned:
                gotUWAligning = True
                issueLinePositioningErrors = False
        except AttributeError: pass # Don't worry about it

        if BibleOrgSysGlobals.verbosityLevel > 2: print( "  " + _("Loading {}…").format( filename ) )
        #self.BBB = BBB
        #self.isSingleChapterBook = BibleOrgSysGlobals.BibleBooksCodes.isSingleChapterBook( BBB )
        self.sourceFilename = filename
        self.sourceFolder = folder
        self.sourceFilepath = os.path.join( folder, filename ) if folder else filename
        originalBook = USFMFile()
        if encoding is None: encoding = 'utf-8'
        originalBook.read( self.sourceFilepath, encoding=encoding )

        # Do some important cleaning up before we save the data
        C, V = '-1', '-1' # So first/id line starts at -1:0
        lastMarker = lastText = ''
        loadErrors = []
        #print( "USFMBibleBook.load():", type(originalBook), type(originalBook.lines), len(originalBook.lines), originalBook.lines[0] )
        for marker,text in originalBook.lines: # Always process a line behind in case we have to combine lines
            if debuggingThisModule and gotUWAligning:
                print( f"\n\nAlignment level = {alignmentVariables['level']} (Max = {alignmentVariables['maxLevel']})" )
                print( f"Alignment text = {alignmentVariables['text']!r}" )
                print( f"Alignment words = {alignmentVariables['words']!r}" )
                #print( f"Alignments ({len(alignmentVariables['saved'])}) = {alignmentVariables['saved']}" )
                print( f"Num saved alignments = {len(alignmentVariables['saved']):,}" )

            #print( f"\nAfter {self.BBB} {C}:{V} \\{marker} {text!r}" )

            if marker == 's5': # it's a Door43 translatable section, i.e., chunking marker
                # We remove these
                if text:
                    if text.strip():
                        loadErrors.append( _("{} {}:{} Removed '\\{}' Door43 custom marker at beginning of line (WITH text)") \
                                            .format( self.BBB, C, V, marker ) )
                        logging.critical( _("Removed '\\{}' Door43 custom marker after {} {} {}:{} at beginning of line (WITH text)") \
                                            .format( marker, self.workName, self.BBB, C, V ) )
                        text = text.lstrip() # Can be an extra space in here!!! (eg., ULT MAT 12:17)
                        if text.startswith( '\\v ' ):
                            marker, text = 'v', text[3:] # Drop s5 and adjust marker
                        else:
                            print( f"s5 text='{text}'" )
                            halt
                    else: # was just whitespace
                        loadErrors.append( _("{} {}:{} Removed '\\{}' Door43 custom marker at beginning of line (with following whitespace)") \
                                            .format( self.BBB, C, V, marker ) )
                        logging.warning( _("Removed '\\{}' Door43 custom marker after {} {}:{} at beginning of line (with following whitespace)") \
                                            .format( marker, self.BBB, C, V ) )
                        continue # so it just gets ignored, effectively deleted
                else: # have s5 field without text!
                    loadErrors.append( _("{} {}:{} Removed '\\{}' Door43 custom marker at beginning of line (with no text)") \
                                        .format( self.BBB, C, V, marker ) )
                    logging.warning( _("Removed '\\{}' Door43 custom marker after {} {}:{} at beginning of line (with no text)") \
                                        .format( marker, self.BBB, C, V ) )
                    continue # so it just gets ignored, effectively deleted

            # Keep track of where we are for more helpful error messages
            if marker=='c' and text:
                #print( "bits", text.split() )
                try: C = text.split()[0]
                except IndexError: # Seems we had a \c field that's just whitespace
                    loadErrors.append( _("{} {}:{} Found {!r} invalid chapter field") \
                                        .format( self.BBB, C, V, text ) )
                    logging.critical( _("Found {!r} invalid chapter field after {} {}:{}") \
                                        .format( text, self.BBB, C, V ) )
                    self.addPriorityError( 100, C, V, _("Found invalid/empty chapter field in file") )
                V = '0'
            elif marker=='v' and text:
                newV = text.split()[0]
                if V=='0' and not ( newV=='1' or newV.startswith( '1-' ) ):
                    loadErrors.append( _("{} {}:{} Expected v1 after chapter marker not {!r}") \
                                        .format( self.BBB, C, V, newV ) )
                    logging.error( _("Unexpected {!r} verse number immediately after chapter field after {} {}:{}") \
                                        .format( newV, self.BBB, C, V ) )
                    self.addPriorityError( 100, C, V, _("Got unexpected chapter number") )
                V = newV
                if C == '-1': C = '1' # Some single chapter books don't have an explicit chapter 1 marker
            elif C == '-1' and marker!='intro': V = str( int(V) + 1 )
            elif marker=='restore': continue # Ignore these lines completely

            # Now load the actual Bible book data
            if BibleOrgSysGlobals.USFMMarkers.isNewlineMarker( marker ):
                if lastMarker: doaddLine( lastMarker, lastText )
                if gotUWAligning:
                    marker, text = handleUWAlignment( marker, text, alignmentVariables )
                lastMarker, lastText = marker, text
            elif BibleOrgSysGlobals.USFMMarkers.isInternalMarker( marker ) \
            or marker.endswith('*') and BibleOrgSysGlobals.USFMMarkers.isInternalMarker( marker[:-1] ): # the line begins with an internal marker -- append it to the previous line
                if issueLinePositioningErrors:
                    if text:
                        loadErrors.append( _("{} {}:{} Found '\\{}' internal marker at beginning of line with text: {!r}").format( self.BBB, C, V, marker, text ) )
                        logging.warning( _("Found '\\{}' internal marker after {} {}:{} at beginning of line with text: {!r}").format( marker, self.BBB, C, V, text ) )
                    else: # no text
                        loadErrors.append( _("{} {}:{} Found '\\{}' internal marker at beginning of line (with no text)").format( self.BBB, C, V, marker ) )
                        logging.warning( _("Found '\\{}' internal marker after {} {}:{} at beginning of line (with no text)").format( marker, self.BBB, C, V ) )
                    self.addPriorityError( 27, C, V, _("Found \\{} internal marker on new line in file").format( marker ) )
                if gotUWAligning:
                    marker, text = handleUWAlignment( marker, text, alignmentVariables )
                if not lastText.endswith(' '): lastText += ' ' # Not always good to add a space, but it's their fault!
                lastText +=  '\\' + marker + ' ' + text
                if BibleOrgSysGlobals.verbosityLevel > 3: print( "{} {} {} Appended {}:{!r} to get combined line {}:{!r}".format( self.BBB, C, V, marker, text, lastMarker, lastText ) )
            elif BibleOrgSysGlobals.USFMMarkers.isNoteMarker( marker ) \
            or marker.endswith('*') and BibleOrgSysGlobals.USFMMarkers.isNoteMarker( marker[:-1] ): # the line begins with a note marker -- append it to the previous line
                if text:
                    loadErrors.append( _("{} {}:{} Found '\\{}' note marker at beginning of line with text: {!r}").format( self.BBB, C, V, marker, text ) )
                    logging.warning( _("Found '\\{}' note marker after {} {}:{} at beginning of line with text: {!r}").format( marker, self.BBB, C, V, text ) )
                else: # no text
                    loadErrors.append( _("{} {}:{} Found '\\{}' note marker at beginning of line (with no text)").format( self.BBB, C, V, marker ) )
                    logging.warning( _("Found '\\{}' note marker after {} {}:{} at beginning of line (with no text)").format( marker, self.BBB, C, V ) )
                self.addPriorityError( 26, C, V, _("Found \\{} note marker on new line in file").format( marker ) )
                if not lastText.endswith(' ') and marker!='f': lastText += ' ' # Not always good to add a space, but it's their fault! Don't do it for footnotes, though.
                lastText +=  '\\' + marker + ' ' + text
                if BibleOrgSysGlobals.verbosityLevel > 3: print( "{} {} {} Appended {}:{!r} to get combined line {}:{!r}".format( self.BBB, C, V, marker, text, lastMarker, lastText ) )
            else: # the line begins with an unknown marker
                if marker in ('zaln-s','zaln-e'): # it's a Door43 alignment marker (should be self-closed)
                    gotUWAligning = True
                    marker, text = handleUWAlignment( marker, text, alignmentVariables )
                #elif self.containerBibleObject.uWaligned and marker == 'zaln-e': # it's a Door43 end-alignment marker (should be self-closed)
                    #print( f"etext='{text}'" )
                    #loadErrors.append( _("{} {}:{} Removed '\\{}' Door43 custom alignment marker at beginning of line (with no text)") \
                                        #.format( self.BBB, C, V, marker ) )
                    #logging.warning( _("Removed '\\{}' Door43 custom alignment marker after {} {}:{} at beginning of line (with no text)") \
                                        #.format( marker, self.BBB, C, V ) )
                    #marker = '' # so it gets deleted
                elif marker and marker[0] == 'z': # it's a custom marker
                    if text:
                        loadErrors.append( _("{} {}:{} Found '\\{}' unknown custom marker at beginning of line with text: {!r}") \
                                            .format( self.BBB, C, V, marker, text ) )
                        logging.warning( _("Found '\\{}' unknown custom marker after {} {}:{} at beginning of line with text: {!r}") \
                                            .format( marker, self.BBB, C, V, text ) )
                    else: # no text
                        loadErrors.append( _("{} {}:{} Found '\\{}' unknown custom marker at beginning of line (with no text)") \
                                            .format( self.BBB, C, V, marker ) )
                        logging.warning( _("Found '\\{}' unknown custom marker after {} {}:{} at beginning of line (with no text)") \
                                            .format( marker, self.BBB, C, V ) )
                    self.addPriorityError( 80, C, V, _("Found \\{} unknown custom marker on new line in file").format( marker ) )
                else: # it's an unknown marker
                    if text:
                        loadErrors.append( _("{} {}:{} Found '\\{}' unknown marker at beginning of line with text: {!r}") \
                                            .format( self.BBB, C, V, marker, text ) )
                        logging.error( _("Found '\\{}' unknown marker after {} {}:{} at beginning of line with text: {!r}") \
                                            .format( marker, self.BBB, C, V, text ) )
                    else: # no text
                        loadErrors.append( _("{} {}:{} Found '\\{}' unknown marker at beginning of line (with no text)") \
                                            .format( self.BBB, C, V, marker ) )
                        logging.error( _("Found '\\{}' unknown marker after {} {}:{} at beginning of line (with no text)") \
                                            .format( marker, self.BBB, C, V ) )
                    self.addPriorityError( 100, C, V, _("Found \\{} unknown marker on new line in file").format( marker ) )
                    for tryMarker in sortedNLMarkers: # Try to do something intelligent here -- it might be just a missing space
                        if marker.startswith( tryMarker ): # Let's try changing it
                            if lastMarker: doaddLine( lastMarker, lastText )
                            #if marker=='s5' and not text:
                                ## Door43 projects use empty s5 fields as chunking markers
                                #lastMarker, lastText = 's', '---'
                            #else:
                            # Move the extra appendage to the marker into the actual text
                            lastMarker, lastText = tryMarker, marker[len(tryMarker):] + ' ' + text
                            if text:
                                loadErrors.append( _("{} {}:{} Changed '\\{}' unknown marker to {!r} at beginning of line: {}").format( self.BBB, C, V, marker, tryMarker, text ) )
                                logging.warning( _("Changed '\\{}' unknown marker to {!r} after {} {}:{} at beginning of line: {}").format( marker, tryMarker, self.BBB, C, V, text ) )
                            else:
                                loadErrors.append( _("{} {}:{} Changed '\\{}' unknown marker to {!r} at beginning of otherwise empty line").format( self.BBB, C, V, marker, tryMarker ) )
                                logging.warning( _("Changed '\\{}' unknown marker to {!r} after {} {}:{} at beginning of otherwise empty line").format( marker, tryMarker, self.BBB, C, V ) )
                            break
                    # Otherwise, don't bother processing this line -- it'll just cause more problems later on
        if lastMarker: doaddLine( lastMarker, lastText ) # Process the final line

        if not originalBook.lines: # There were no lines!!!
            loadErrors.append( _("{} This USFM file was totally empty: {}").format( self.BBB, self.sourceFilename ) )
            logging.error( _("USFM file for {} was totally empty: {}").format( self.BBB, self.sourceFilename ) )
            lastMarker, lastText = 'rem', 'This (USFM) file was completely empty' # Save something since we had a file at least

        if gotUWAligning or alignmentVariables['saved']:
            assert alignmentVariables['level'] == 0
            assert not alignmentVariables['text']
            assert not alignmentVariables['words']
            if alignmentVariables['saved']:
                self.uWalignments = alignmentVariables['saved']
                self.containerBibleObject.uWaligned = True
                if debuggingThisModule:
                    print( f"\n\nGot ({len(self.uWalignments):,}) alignments for {self.BBB}" )
                    print( f"  Alignments max level was {alignmentVariables['maxLevel']}" )
                    #for j, (C,V,text,words) in enumerate( self.uWalignments, start=1 ):
                        #print( f"{j} {self.BBB} {C}:{V} '{text}'\n    = {words}" )
                        #if j > 8: break
            #if self.BBB == 'GEN': halt
        if loadErrors: self.errorDictionary['Load Errors'] = loadErrors
        #if debugging: print( self._rawLines ); halt
    # end of USFMBibleBook.load
# end of class USFMBibleBook



def demo():
    """
    Demonstrate reading and processing some USFM Bible databases.
    """
    if BibleOrgSysGlobals.verbosityLevel > 0: print( ProgNameVersion )


    def demoFile( name, filename, folder, BBB ):
        if BibleOrgSysGlobals.verbosityLevel > 1: print( _("Loading {} from {}…").format( BBB, filename ) )
        UBB = USFMBibleBook( name, BBB )
        UBB.load( filename, folder, encoding )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "  ID is {!r}".format( UBB.getField( 'id' ) ) )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "  Header is {!r}".format( UBB.getField( 'h' ) ) )
        if BibleOrgSysGlobals.verbosityLevel > 1: print( "  Main titles are {!r} and {!r}".format( UBB.getField( 'mt1' ), UBB.getField( 'mt2' ) ) )
        #if BibleOrgSysGlobals.verbosityLevel > 0: print( UBB )
        UBB.validateMarkers()
        UBBVersification = UBB.getVersification ()
        if BibleOrgSysGlobals.verbosityLevel > 2: print( UBBVersification )
        UBBAddedUnits = UBB.getAddedUnits ()
        if BibleOrgSysGlobals.verbosityLevel > 2: print( UBBAddedUnits )
        discoveryDict = UBB._discover()
        #print( "discoveryDict", discoveryDict )
        UBB.check()
        UBErrors = UBB.getErrors()
        if BibleOrgSysGlobals.verbosityLevel > 2: print( UBErrors )
    # end of demoFile


    from InputOutput import USFMFilenames

    if 1: # Test individual files -- choose one of these or add your own
        name, encoding, testFolder, filename, BBB = "USFM3Test", 'utf-8', BibleOrgSysGlobals.BOS_TEST_DATA_FOLDERPATH.joinpath( 'USFM3AllMarkersProject/'), '81-COLeng-amp.usfm', 'COL' # You can put your test file here
        #name, encoding, testFolder, filename, BBB = "WEB", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Bibles/English translations/WEB (World English Bible)/2012-06-23 eng-web_usfm/'), "06-JOS.usfm", "JOS" # You can put your test file here
        #name, encoding, testFolder, filename, BBB = "WEB", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Bibles/English translations/WEB (World English Bible)/2012-06-23 eng-web_usfm/'), "44-SIR.usfm", "SIR" # You can put your test file here
        #name, encoding, testFolder, filename, BBB = "Matigsalug", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Matigsalug/Bible/MBTV/'), "MBT102SA.SCP", "SA2" # You can put your test file here
        #name, encoding, testFolder, filename, BBB = "Matigsalug", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Matigsalug/Bible/MBTV/'), "MBT15EZR.SCP", "EZR" # You can put your test file here
        #name, encoding, testFolder, filename, BBB = "Matigsalug", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Matigsalug/Bible/MBTV/'), "MBT41MAT.SCP", "MAT" # You can put your test file here
        #name, encoding, testFolder, filename, BBB = "Matigsalug", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Matigsalug/Bible/MBTV/'), "MBT67REV.SCP", "REV" # You can put your test file here
        if os.access( testFolder, os.R_OK ):
            demoFile( name, filename, testFolder, BBB )
        else: print( _("Sorry, test folder '{}' doesn't exist on this computer.").format( testFolder ) )

    if 0: # Test a whole folder full of files
        name, encoding, testFolder = "Matigsalug", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Matigsalug/Bible/MBTV/' ) # You can put your test folder here
        #name, encoding, testFolder = "WEB", 'utf-8', BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../../../Data/Work/Bibles/English translations/WEB (World English Bible)/2012-06-23 eng-web_usfm/' ) # You can put your test folder here
        if os.access( testFolder, os.R_OK ):
            if BibleOrgSysGlobals.verbosityLevel > 1: print( _("Scanning {} from {}…").format( name, testFolder ) )
            fileList = USFMFilenames.USFMFilenames( testFolder ).getMaximumPossibleFilenameTuples()
            for BBB,filename in fileList:
                demoFile( name, filename, testFolder, BBB )
        else: print( _("Sorry, test folder '{}' doesn't exist on this computer.").format( testFolder ) )

    if 0: # Test with translationCore test files
        testFolder = BibleOrgSysGlobals.PARALLEL_RESOURCES_BASE_FOLDERPATH.joinpath( '../../ExternalPrograms/usfm-js/__tests__/resources/' )
        for filename in os.listdir( testFolder ):
            if filename.endswith( '.usfm' ):
                if BibleOrgSysGlobals.verbosityLevel > 0:
                    print( f"\nLoading translationCore test file: {filename}…" )
                #filepath = os.path.join( testFolder, filename )
                UBB = USFMBibleBook( 'test', 'TST' )
                UBB.load( filename, testFolder )
# end of demo

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic set-up
    parser = BibleOrgSysGlobals.setup( ProgName, ProgVersion )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser )

    demo()

    BibleOrgSysGlobals.closedown( ProgName, ProgVersion )
# end of USFMBibleBook.py