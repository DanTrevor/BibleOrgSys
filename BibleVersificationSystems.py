#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# BibleVersificationSystems.py
#   Last modified: 2012-06-04 (also update versionString below)
#
# Module handling BibleVersificationSystem_*.xml to produce C and Python data tables
#
# Copyright (C) 2010-2012 Robert Hunt
# Author: Robert Hunt <robert316@users.sourceforge.net>
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
Module handling BibleVersificationSystem_*.xml to produce C and Python data tables.
"""

progName = "Bible Chapter/Verse Systems handler"
versionString = "0.48"


import os, logging
from gettext import gettext as _

from singleton import singleton
import Globals
from BibleBooksCodes import BibleBooksCodes


@singleton # Can only ever have one instance
class BibleVersificationSystems:
    """
    Class for handling BibleVersificationSystems.

    This class doesn't deal at all with XML, only with Python dictionaries, etc.

    Note: BBB is used in this class to represent the three-character referenceAbbreviation.
    """

    def __init__( self ): # We can't give this parameters because of the singleton
        """
        Constructor: 
        """
        self.__DataDict = None # We'll import into this in loadData
    # end of __init__

    def loadData( self, XMLFolder=None ):
        """ Loads the XML data file and imports it to dictionary format (if not done already). """
        if not self.__DataDict: # Don't do this unnecessarily
            # See if we can load from the pickle file (faster than loading from the XML)
            picklesGood = False
            dataFilepath = os.path.join( os.path.dirname(__file__), "DataFiles/" )
            standardPickleFilepath = os.path.join( dataFilepath, "DerivedFiles", "BibleVersificationSystems_Tables.pickle" )
            if XMLFolder is None and os.access( standardPickleFilepath, os.R_OK ):
                standardXMLFolder = os.path.join( dataFilepath, "BookOrders/" )
                pickle8, pickle9 = os.stat(standardPickleFilepath)[8:10]
                picklesGood = True
                for filename in os.listdir( standardXMLFolder ):
                    filepart, extension = os.path.splitext( filename )
                    XMLfilepath = os.path.join( standardXMLFolder, filename )
                    if extension.upper() == '.XML' and filepart.upper().startswith("BIBLEVERSIFICATIONSYSTEM_"):
                      if pickle8 <= os.stat( XMLfilepath )[8] \
                      or pickle9 <= os.stat( XMLfilepath )[9]: # The pickle file is older
                        picklesGood = False; break
            if picklesGood:
                import pickle
                if Globals.verbosityLevel > 2: print( "Loading pickle file {}...".format( standardPickleFilepath ) )
                with open( standardPickleFilepath, 'rb') as pickleFile:
                    self.__DataDict = pickle.load( pickleFile ) # The protocol version used is detected automatically, so we do not have to specify it
            else: # We have to load the XML (much slower)
                from BibleVersificationSystemsConverter import BibleVersificationSystemsConverter
                if XMLFolder is not None: logging.warning( _("Bible versification systems are already loaded -- your given folder of '{}' was ignored").format(XMLFolder) )
                bvsc = BibleVersificationSystemsConverter()
                bvsc.loadSystems( XMLFolder ) # Load the XML (if not done already)
                self.__DataDict = bvsc.importDataToPython() # Get the various dictionaries organised for quick lookup
        return self
    # end of loadData

    def __str__( self ):
        """
        This method returns the string representation of the Bible versification systems object.
        Will return more information if the verbosity setting is higher.
        
        @return: the name of a Bible object formatted as a string
        @rtype: string
        """
        result = "BibleVersificationSystems object"
        result += ('\n' if result else '') + "  " + _("Number of systems = {}").format( len(self.__DataDict) )
        if Globals.verbosityLevel > 2:
            for systemName in self.__DataDict:
                CVData, OVData, CombVData, ReordVData = self.__DataDict[systemName]['CV'], self.__DataDict[systemName]['omitted'], self.__DataDict[systemName]['combined'], self.__DataDict[systemName]['reordered']
                # No longer true: assert( len(CVData) == len(OVData) == len(CombVData) == len(ReordVData) )
                if Globals.verbosityLevel > 3:
                    numChapters = 0
                    for BBB,bookData in CVData.items():
                        numChapters += int( bookData['numChapters'] )
                    result += ('\n' if result else '') + "    " + _("{} (data for {} books): chapter/verse data for {} total chapters").format( systemName, len(CVData), numChapters )
                    numOV = 0
                    for BBB,bookData in OVData.items():
                        numOV += len(bookData)
                    if numOV: result += ('\n' if result else '') + "      " + _("{} omitted verse data segments").format( numOV )
                    numCmV = 0
                    for BBB,bookData in CombVData.items():
                        numCmV += len(bookData)
                    if numCmV: result += ('\n' if result else '') + "      " + _("{} combined verse data segments").format( numCmV )
                    numRV = 0
                    for BBB,bookData in ReordVData.items():
                        numRV += len(bookData)
                    if numRV: result += ('\n' if result else '') + "      " + _("{} reordered verse data segments").format( numRV )
                else: # not that verbose
                    result += ('\n' if result else '') + "    " + _("{} (data for {} books)").format( systemName, len(CVData) )
        return result
    # end of __str__

    def __len__( self ):
        """ Returns the number of systems loaded. """
        return len( self.__DataDict )
    # end of __len__

    def getAvailableVersificationSystemNames( self ):
        """ Returns a list of available system name strings. """
        return [systemName for systemName in self.__DataDict]
    # end of getAvailableVersificationSystemNames

    def isValidVersificationSystemName( self, systemName ):
        """ Returns True or False. """
        return systemName in self.__DataDict
    # end of isValidVersificationSystemName

    def getVersificationSystem( self, systemName ):
        """ Returns the dictionary for the requested system. """
        if systemName in self.__DataDict:
            return self.__DataDict[systemName]
        # else
        logging.error( _("No '{}' system in Bible Versification Systems").format( systemName ) )
        if Globals.verbosityLevel > 2: logging.error( _("Available systems are {}").format( self.getAvailableVersificationSystemNames() ) )
    # end of getVersificationSystem

    def compareVersificationSystems( self, system1Name, system2Name=None ):
        """ Compares a given versification system against one, some, or all versification systems.
            system2Name can be a string or a list of strings.
        Prints the output of the comparison(s).
        """
        assert( system1Name in self.__DataDict )
        if system2Name is None: compareList = self.getAvailableVersificationSystemNames()
        elif isinstance( system2Name, list ):
            for name in system2Name:
                assert( name != system1Name )
                assert( name in self.__DataDict )
            compareList = system2Name
        elif isinstance( system2Name, str ):
            assert( system2Name != system1Name )
            assert( system2Name in self.__DataDict )
            compareList = [system2Name]
        else: raise Exception( "compareVersificationSystems parameter error" )

        displayCount = 3
        if Globals.verbosityLevel > 2: displayCount = 10
        if Globals.verbosityLevel > 3: displayCount = 0 # infinite

        numComparesDone, numExactMatches, numCloseMatches, result = 0, 0, 0, ''
        for compareSystemName in compareList:
            if compareSystemName == system1Name: continue # Don't check against yourself
            if Globals.verbosityLevel > 2 or len(compareList)>1:
                result += ('\n' if result else '') + "  " + _("Comparing {} against {}...").format( system1Name, compareSystemName )
            CVData1, OVData1, CoVData1, RVData1 = self.__DataDict[system1Name]['CV'], self.__DataDict[system1Name]['omitted'], self.__DataDict[system1Name]['combined'], self.__DataDict[system1Name]['reordered']
            CVData2, OVData2, CoVData2, RVData2 = self.__DataDict[compareSystemName]['CV'], self.__DataDict[compareSystemName]['omitted'], self.__DataDict[compareSystemName]['combined'], self.__DataDict[compareSystemName]['reordered']
            haveMajorDifferences, haveMinorDifferences, uncheckedBooks = False, False, []
            CVErrorCount, booksWithMajorDifferences, booksWithOnlyMinorDifferences, booksMatchExactly = 0, 0, 0, 0
            numBooks1 = len( CVData1 ); numBooks2 = len( CVData2 )
            if numBooks1 != numBooks2: result += ('\n' if result else '') + "    " + _("{} has information for {} books; {} has information for {} books").format( system1Name, numBooks1, compareSystemName, numBooks2 )
            elif Globals.verbosityLevel>1: result += ('\n' if result else '') + "    " + _("Both systems have information for {} books").format( numBooks1 )
            if OVData1 and not OVData2: result += ('\n' if result else '') + "      " + _("Only {} has omitted verse information").format( system1Name )
            if not OVData1 and OVData2: result += ('\n' if result else '') + "      " + _("{} has no omitted verse information (but {} does)").format( system1Name, compareSystemName )
            if CoVData1 and not CoVData2: result += ('\n' if result else '') + "      " + _("Only {} has combined verse information").format( system1Name )
            if not CoVData1 and CoVData2: result += ('\n' if result else '') + "      " + _("{} has no combined verse information (but {} does)").format( system1Name, compareSystemName )
            if RVData1 and not RVData2: result += ('\n' if result else '') + "      " + _("Only {} has reordered verse information").format( system1Name )
            if not RVData1 and RVData2: result += ('\n' if result else '') + "      " + _("{} has no reordered verse information (but {} does)").format( system1Name, compareSystemName )
            for BBB,thisCVData1 in CVData1.items():
                if BBB in CVData2:
                    bookHasMajorDifferences, bookHasMinorDifferences = False, False
                    # Compare main CV info
                    thisCVData2 = CVData2[BBB]
                    numChapters1 = thisCVData1['numChapters']; numChapters2 = thisCVData2['numChapters']
                    if numChapters1 != numChapters2:
                        result += ('\n' if result else '') + "      " + _("{} {} has information for {} chapters; {} {} has information for {} chapters").format( system1Name, BBB, numChapters1, compareSystemName, BBB, numChapters2 )
                        haveMajorDifferences, bookHasMajorDifferences = True, True
                    else:
                        for C in thisCVData1:
                            if C in thisCVData2 and C!='numChapters':
                                V1 = thisCVData1[C]; V2 = thisCVData2[C]
                                if V1 != V2:
                                    if CVErrorCount<displayCount or displayCount==0:
                                        result += ('\n' if result else '') + "        " + _("{} {} {} has {} verses; {} {} {} has {} verses").format( system1Name, BBB, C, V1, compareSystemName, BBB, C, V2 )
                                    elif CVErrorCount==displayCount:
                                        result += '\n' + "          " + _("...") + '  ' + _("(Increase verbosity to see more differences)")
                                    haveMajorDifferences, bookHasMajorDifferences = True, True
                                    CVErrorCount += 1
                    if OVData1 and OVData2: # Compare omitted verses
                        if BBB in OVData1 and BBB in OVData2:
                            thisOVData1 = OVData1[BBB]; thisOVData2 = OVData2[BBB]
                            for C,V in thisOVData1:
                                if (C,V) not in thisOVData2:
                                    result += ('\n' if result else '') + "        " + _("{}:{} is omitted in {} {} but not in {} {}").format( system1Name, BBB, C, V, compareSystemName, BBB )
                                    haveMinorDifferences, bookHasMinorDifferences = True, True
                            for C,V in thisOVData2:
                                if (C,V) not in thisOVData1:
                                    result += ('\n' if result else '') + "        " + _("{}:{} is not omitted in {} {} but is in {} {}").format( system1Name, BBB, C, V, compareSystemName, BBB )
                                    haveMinorDifferences, bookHasMinorDifferences = True, True
                        elif BBB in OVData1 and not BBB in OVData2:
                            result += ('\n' if result else '') + "      " + _("{} {} has omitted verse information but there is none for {} {}").format( system1Name, BBB, compareSystemName, BBB )
                            haveMinorDifferences, bookHasMinorDifferences = True, True
                        elif BBB not in OVData1 and BBB in OVData2:
                            result += ('\n' if result else '') + "      " + _("{} {} has no omitted verse information but {} {} does").format( system1Name, BBB, compareSystemName, BBB )
                            haveMinorDifferences, bookHasMinorDifferences = True, True
                        else: raise Exception( "OV programming error" )
                    if CoVData1 and CoVData2: # Compare combined verses
                        if BBB in CoVData1 and BBB in CoVData2:
                            thisCoVData1 = CoVData1[BBB]; thisCoVData2 = CoVData2[BBB]
                            for C,V in thisCoVData1:
                                if (C,V) not in thisCoVData2:
                                    result += ('\n' if result else '') + "        " + _("{}:{} is combined in {} {} but not in {} {}").format( system1Name, BBB, C, V, compareSystemName, BBB )
                                    haveMinorDifferences, bookHasMinorDifferences = True, True
                            for C,V in thisCoVData2:
                                if (C,V) not in thisCoVData1:
                                    result += ('\n' if result else '') + "        " + _("{}:{} is not combined in {} {} but is in {} {}").format( system1Name, BBB, C, V, compareSystemName, BBB )
                                    haveMinorDifferences, bookHasMinorDifferences = True, True
                        elif BBB in CoVData1 and not BBB in CoVData2:
                            result += ('\n' if result else '') + "      " + _("{} {} has combined verse information but there is none for {} {}").format( system1Name, BBB, compareSystemName, BBB )
                            haveMinorDifferences, bookHasMinorDifferences = True, True
                        elif BBB not in CoVData1 and BBB in CoVData2:
                            result += ('\n' if result else '') + "      " + _("{} {} has no combined verse information but {} {} does").format( system1Name, BBB, compareSystemName, BBB )
                            haveMinorDifferences, bookHasMinorDifferences = True, True
                        else: raise Exception( "OV programming error" )
                    if RVData1 and RVData2: # Compare reordered verses
                        if BBB in RVData1 and BBB in RVData2:
                            thisRVData1 = RVData1[BBB]; thisRVData2 = RVData2[BBB]
                            for C,V in thisRVData1:
                                if (C,V) not in thisRVData2:
                                    result += ('\n' if result else '') + "        " + _("{}:{} is reordered in {} {} but not in {} {}").format( system1Name, BBB, C, V, compareSystemName, BBB )
                                    haveMinorDifferences, bookHasMinorDifferences = True, True
                            for C,V in thisRVData2:
                                if (C,V) not in thisRVData1:
                                    result += ('\n' if result else '') + "        " + _("{}:{} is not reordered in {} {} but is in {} {}").format( system1Name, BBB, C, V, compareSystemName, BBB )
                                    haveMinorDifferences, bookHasMinorDifferences = True, True
                        elif BBB in RVData1 and not BBB in RVData2:
                            result += ('\n' if result else '') + "      " + _("{} {} has reordered verse information but there is none for {} {}").format( system1Name, BBB, compareSystemName, BBB )
                            haveMinorDifferences, bookHasMinorDifferences = True, True
                        elif BBB not in RVData1 and BBB in RVData2:
                            result += ('\n' if result else '') + "      " + _("{} {} has no reordered verse information but {} {} does").format( system1Name, BBB, compareSystemName, BBB )
                            haveMinorDifferences, bookHasMinorDifferences = True, True
                        else: raise Exception( "OV programming error" )
                    if bookHasMajorDifferences: booksWithMajorDifferences += 1
                    elif bookHasMinorDifferences: booksWithOnlyMinorDifferences += 1
                    else: booksMatchExactly += 1
                else: # this book isn't in the other versification scheme
                    uncheckedBooks.append( BBB )
                    haveMajorDifferences = True
            if uncheckedBooks: result += ('\n' if result else '') + "    " + _("The following books from {} were unable to be checked against {}: {}").format( system1Name, compareSystemName, uncheckedBooks )
            if not haveMajorDifferences:
                numCloseMatches += 1
                if not haveMinorDifferences: numExactMatches += 1
            numComparesDone += 1
        if Globals.verbosityLevel > 1 or numExactMatches!=numComparesDone:
            if numComparesDone==1: print( '\n' + _("Compared {} against {} (with {} exact system matches, {} close matches)").format( system1Name, system2Name, numExactMatches, numCloseMatches ) )
            else: print( '\n' + _("Compared {} against {} other systems (with {} exact system matches, {} close matches)").format( system1Name, numComparesDone, numExactMatches, numCloseMatches ) )
            if Globals.verbosityLevel > 1 and (booksMatchExactly or booksWithOnlyMinorDifferences):
                print( _("There were {} books that matched exactly, and another {} with only minor differences. ({} books checked that had major differences.)") \
                                .format( booksMatchExactly, booksWithOnlyMinorDifferences, booksWithMajorDifferences ) )
            print( result )
    # end of compareVersificationSystems

    def checkVersificationSystem( self, thisSystemName, versificationSchemeToCheck, extraVerseInfoToCheck=None ):
        """
        Check the given versification scheme against all the loaded systems.
        Create a new versification file if it doesn't match any.
        Returns the number of matched systems (which can also be used as a True/False "matched" flag).
        """
        assert( self.__DataDict )
        assert( versificationSchemeToCheck )
        omittedVersesToCheck, combinedVersesToCheck, reorderedVersesToCheck = {}, {}, {}
        if extraVerseInfoToCheck is not None:
            if "omitted" in extraVerseInfoToCheck: omittedVersesToCheck = extraVerseInfoToCheck["omitted"]
            if "combined" in extraVerseInfoToCheck: combinedVersesToCheck = extraVerseInfoToCheck["combined"]
            if "reordered" in extraVerseInfoToCheck: reorderedVersesToCheck = extraVerseInfoToCheck["reordered"]
            if not omittedVersesToCheck and not combinedVersesToCheck and not reorderedVersesToCheck: # Then what was there???
                logging.error( _("No useful information found in extraVerseInfoToCheck parameter: {}").format(extraVerseInfoToCheck) )

        # Make sure we have the bible books codes data loaded and available
        from BibleBooksCodes import BibleBooksCodes
        self.BibleBooksCodes = BibleBooksCodes().loadData()

        matchedVersificationSystemCodes, badOVList, badCVList, badRVList = [], [], [], []
        systemMatchCount, systemMismatchCount, allErrors, errorSummary = 0, 0, '', ''
        for versificationSystemCode in self.__DataDict: # Step through the various reference schemes
            #print( system )
            bookMismatchCount, chapterMismatchCount, verseMismatchCount, omittedVerseMismatchCount, combinedVerseMismatchCount, reorderedVerseMismatchCount, theseErrors = 0, 0, 0, 0, 0, 0, ''
            CVData, OVData, CombVData, ReordVData = self.__DataDict[versificationSystemCode]['CV'], self.__DataDict[versificationSystemCode]['omitted'], self.__DataDict[versificationSystemCode]['combined'], self.__DataDict[versificationSystemCode]['reordered']

            # Check verses per chapter
            for BBB in versificationSchemeToCheck.keys():
                #print( BBB )
                if BBB in CVData:
                    myContainer = versificationSchemeToCheck[BBB] if isinstance(versificationSchemeToCheck[BBB],list) else versificationSchemeToCheck[BBB].items() # Handles both lists and dictionaries
                    for chapterToCheck,numVersesToCheck in myContainer:
                        if not isinstance(chapterToCheck,str): raise Exception( "Chapter programming error" )
                        if not isinstance(numVersesToCheck,str): raise Exception( "Verse programming error" )
                        if chapterToCheck in CVData[BBB]: # That chapter number is in our scheme
                            if CVData[BBB][chapterToCheck] != numVersesToCheck:
                                theseErrors += ("\n" if theseErrors else "") + "    " + _("Doesn't match '{}' system at {} {} verse {}").format( versificationSystemCode, BBB, chapterToCheck, numVersesToCheck )
                                if bookMismatchCount==0 and chapterMismatchCount==0 and verseMismatchCount==0: rememberedBBB, rememberedChapter, rememberedVerses1, rememberedVerses2 = BBB, chapterToCheck, CVData[BBB][chapterToCheck], numVersesToCheck
                                verseMismatchCount += 1
                        else: # Our scheme doesn't have that chapter number
                            theseErrors += ("\n" if theseErrors else "") + "    " + _("Doesn't match '{}' system at {} chapter {} ({} verses)").format( versificationSystemCode, BBB, chapterToCheck, numVersesToCheck )
                            chapterMismatchCount += 1
                else:
                    theseErrors += ("\n" if theseErrors else "") + "    " + _("Can't find {} bookcode in {}").format( BBB, versificationSystemCode )
                    bookMismatchCount += 1

            # Check omitted verses
            if OVData and not omittedVersesToCheck:
                badOVList.append( versificationSystemCode )
            else:
                for BBB in omittedVersesToCheck.keys():
                    if BBB in OVData:
                        if OVData[BBB] == omittedVersesToCheck[BBB]: continue # Perfect match for this book
                        for cv in omittedVersesToCheck[BBB]:
                            if cv not in OVData[BBB]:
                                theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} not omitted in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                                if omittedVerseMismatchCount==0: rememberedOmission = BBB, cv[0], cv[1], thisSystemName, versificationSystemCode
                                omittedVerseMismatchCount += 1
                        for cv in OVData[BBB]:
                            if cv not in omittedVersesToCheck[BBB]:
                                theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} is omitted in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                                if omittedVerseMismatchCount==0: rememberedOmission = BBB, cv[0], cv[1], versificationSystemCode, thisSystemName
                                omittedVerseMismatchCount += 1
                    else: # We don't match
                        theseErrors += ("\n" if theseErrors else "") + "    " + _("No omitted verses for {} in {}").format( BBB, versificationSystemCode )
                        omittedVerseMismatchCount += len( omittedVersesToCheck[BBB] )

            # Check combined verses
            if CombVData and not combinedVersesToCheck:
                badCVList.append( versificationSystemCode )
            else:
                for BBB in combinedVersesToCheck.keys():
                    if BBB in CombVData:
                        if CombVData[BBB] == combinedVersesToCheck[BBB]: continue # Perfect match for this book
                        for cv in combinedVersesToCheck[BBB]:
                            if cv not in CombVData[BBB]:
                                theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} not combined in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                                if combinedVerseMismatchCount==0: rememberedCombination = BBB, cv[0], cv[1], thisSystemName, versificationSystemCode
                                combinedVerseMismatchCount += 1
                        for cv in CombVData[BBB]:
                            if cv not in combinedVersesToCheck[BBB]:
                                theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} is combined in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                                if combinedVerseMismatchCount==0: rememberedCombination = BBB, cv[0], cv[1], versificationSystemCode, thisSystemName
                                combinedVerseMismatchCount += 1
                    else: # We don't match
                        theseErrors += ("\n" if theseErrors else "") + "    " + _("No combined verses for {} in {}").format( BBB, versificationSystemCode )
                        combinedVerseMismatchCount += len( combinedVersesToCheck[BBB] )

            # Check reordered verses
            if ReordVData and not reorderedVersesToCheck:
                badRVList.append( versificationSystemCode )
            else:
                for BBB in reorderedVersesToCheck.keys():
                    if BBB in ReordVData:
                        if ReordVData[BBB] == reorderedVersesToCheck[BBB]: continue # Perfect match for this book
                        for cv in reorderedVersesToCheck[BBB]:
                            if cv not in ReordVData[BBB]:
                                theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} not reordered in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                                if reorderedVerseMismatchCount==0: rememberedReordering = BBB, cv[0], cv[1], thisSystemName, versificationSystemCode
                                reorderedVerseMismatchCount += 1
                        for cv in ReordVData[BBB]:
                            if cv not in reorderedVersesToCheck[BBB]:
                                theseErrors += ("\n" if theseErrors else "") + "   " + _("{}:{} is reordered in {} reference versification for {}").format( cv[0], cv[1], versificationSystemCode, BBB )
                                if reorderedVerseMismatchCount==0: rememberedReordering = BBB, cv[0], cv[1], versificationSystemCode, thisSystemName
                                reorderedVerseMismatchCount += 1
                    else: # We don't match
                        theseErrors += ("\n" if theseErrors else "") + "    " + _("No reordered verses for {} in {}").format( BBB, versificationSystemCode )
                        reorderedVerseMismatchCount += len( reorderedVersesToCheck[BBB] )

            if bookMismatchCount or chapterMismatchCount or verseMismatchCount or omittedVerseMismatchCount or combinedVerseMismatchCount or reorderedVerseMismatchCount:
                if omittedVersesToCheck:
                    thisError = "    " + _("Doesn't match '{}' system ({} book mismatches, {} chapter mismatches, {} verse mismatches, {} omitted-verse mismatches)").format( versificationSystemCode, bookMismatchCount, chapterMismatchCount, verseMismatchCount,omittedVerseMismatchCount )
                    if omittedVerseMismatchCount==1: thisError += "\n      " + _("Omitted verse mismatch was {} {}:{} omitted in {} but present in {}").format(rememberedOmission[0],rememberedOmission[1],rememberedOmission[2],rememberedOmission[3],rememberedOmission[4])
                    elif Globals.verbosityLevel>2 and bookMismatchCount==0 and chapterMismatchCount==0 and omittedVerseMismatchCount>0: thisError += "\n      " + _("First omitted verse mismatch was {} {}:{} omitted in {} but present in {}").format(rememberedOmission[0],rememberedOmission[1],rememberedOmission[2],rememberedOmission[3],rememberedOmission[4])
                elif combinedVersesToCheck: # only display one of these systems
                    thisError = "    " + _("Doesn't match '{}' system ({} book mismatches, {} chapter mismatches, {} verse mismatches, {} combined-verse mismatches)").format( versificationSystemCode, bookMismatchCount, chapterMismatchCount, verseMismatchCount,omittedVerseMismatchCount )
                    if combinedVerseMismatchCount==1: thisError += "\n      " + _("Combined verse mismatch was {} {}:{} between {} and {}").format(rememberedCombination[0],rememberedCombination[1],rememberedCombination[2],rememberedCombination[3],rememberedCombination[4])
                    elif Globals.verbosityLevel>2 and bookMismatchCount==0 and chapterMismatchCount==0 and combinedVerseMismatchCount>0: thisError += "\n      " + _("First combined verse mismatch was {} {}:{} omitted in {} but present in {}").format(rememberedCombination[0],rememberedCombination[1],rememberedCombination[2],rememberedCombination[3],rememberedCombination[4])
                elif reorderedVersesToCheck:
                    thisError = "    " + _("Doesn't match '{}' system ({} book mismatches, {} chapter mismatches, {} verse mismatches, {} reordered-verse mismatches)").format( versificationSystemCode, bookMismatchCount, chapterMismatchCount, verseMismatchCount,omittedVerseMismatchCount )
                    if reorderedVerseMismatchCount==1: thisError += "\n      " + _("Reordered verse mismatch was {} {}:{} between {} and {}").format(rememberedReordering[0],rememberedReordering[1],rememberedReordering[2],rememberedReordering[3],rememberedReordering[4])
                    elif Globals.verbosityLevel>2 and bookMismatchCount==0 and chapterMismatchCount==0 and reorderedVerseMismatchCount>0: thisError += "\n      " + _("First reordered verse mismatch was {} {}:{} omitted in {} but present in {}").format(rememberedReordering[0],rememberedReordering[1],rememberedReordering[2],rememberedReordering[3],rememberedReordering[4])
                else:
                    thisError = "    " + _("Doesn't match '{}' system ({} book mismatches, {} chapter mismatches, {} verse mismatches)").format( versificationSystemCode, bookMismatchCount, chapterMismatchCount, verseMismatchCount )
                if bookMismatchCount==0 and chapterMismatchCount==0 and verseMismatchCount==1: thisError += "\n      " + _("{} {} chapter {} had {} verses but {} had {}").format(thisSystemName, rememberedBBB, rememberedChapter, rememberedVerses2, versificationSystemCode, rememberedVerses1)
                theseErrors += ("\n" if theseErrors else "") + thisError
                if bookMismatchCount==0 or Globals.verbosityLevel>2: errorSummary += ("\n" if errorSummary else "") + thisError
                systemMismatchCount += 1
            else:
                #print( "  Matches '{}' system".format( versificationSystemCode ) )
                systemMatchCount += 1
                matchedVersificationSystemCodes.append( versificationSystemCode )
            if Globals.commandLineOptions.debug and chapterMismatchCount==0 and 0<verseMismatchCount<8 and omittedVerseMismatchCount<10: print( theseErrors )
            allErrors += ("\n" if allErrors else "") + theseErrors

        if badOVList:
            logging.warning( _("No omitted verse list provided to check against {}").format( badOVList ) )
        elif badCVList: # only display one of these warnings
            logging.warning( _("No combined verse list provided to check against {}").format( badCVList ) )
        elif badRVList:
            logging.warning( _("No reordered verse list provided to check against {}").format( badRVList ) )

        if systemMatchCount == 1: # What we hope for
            if badOVList: print( "  " + _("{} roughly matched {} versification (with these {} books)").format( thisSystemName, matchedVersificationSystemCodes[0], len(versificationSchemeToCheck) ) )
            else: print( "  " + _("{} matched {} versification (with these {} books)").format( thisSystemName, matchedVersificationSystemCodes[0], len(versificationSchemeToCheck) ) )
            if Globals.commandLineOptions.debug: print( errorSummary )
        elif systemMatchCount == 0: # No matches
            print( "  " + _("{} mismatched {} versification systems (with these {} books)").format( thisSystemName, systemMismatchCount, len(versificationSchemeToCheck) ) )
            toPrint = allErrors if Globals.commandLineOptions.debug else errorSummary
            if toPrint: print( toPrint )
        else: # Multiple matches
            print( "  " + _("{} matched {} versification system(s): {} (with these {} books)").format( thisSystemName, systemMatchCount, matchedVersificationSystemCodes, len(versificationSchemeToCheck) ) )
            if Globals.commandLineOptions.debug: print( errorSummary )

        if Globals.commandLineOptions.export and not systemMatchCount: # Write a new file
            outputFilepath = os.path.join( os.path.dirname(__file__), "DataFiles/", "ScrapedFiles/", "BibleVersificationSystem_"+thisSystemName + ".xml" )
            if Globals.verbosityLevel > 1: print( _("Writing {} books to {}...").format( len(versificationSchemeToCheck), outputFilepath ) )
            if omittedVersesToCheck:
                totalOmittedVerses = 0
                for BBB in omittedVersesToCheck.keys():
                    totalOmittedVerses += len( omittedVersesToCheck[BBB] )
                if Globals.verbosityLevel > 2: print( _("  Have {} omitted verses for {} books").format( totalOmittedVerses, len(omittedVersesToCheck) ) )
            with open( outputFilepath, 'wt' ) as myFile:
                for BBB in versificationSchemeToCheck:
                    myFile.write( "  <BibleBookVersification>\n" )
                    myFile.write( "    <nameEnglish>{}</nameEnglish>\n".format( self.BibleBooksCodes.getEnglishName_NR(BBB) ) ) # the English book name from the BibleBooksCodes.xml file
                    myFile.write( "    <referenceAbbreviation>{}</referenceAbbreviation>\n".format( BBB ) )
                    myFile.write( "    <numChapters>{}</numChapters>\n".format( len(versificationSchemeToCheck[BBB]) ) )
                    for c,numV in versificationSchemeToCheck[BBB]:
                        omittedVerseString = ''
                        if BBB in omittedVersesToCheck:
                            for oc,ov in omittedVersesToCheck[BBB]:
                                if oc == c: # It's this chapter
                                    omittedVerseString += (',' if omittedVerseString else '') + str(ov)
                        if omittedVerseString:
                            if Globals.verbosityLevel > 3 or Globals.commandLineOptions.debug: print( '   ', BBB, c+':'+omittedVerseString )
                            myFile.write( '    <numVerses chapter="{}" omittedVerses="{}">{}</numVerses>\n'.format( c, omittedVerseString, numV ) )
                        else:
                            myFile.write( '    <numVerses chapter="{}">{}</numVerses>\n'.format( c, numV ) )
                    myFile.write( "  </BibleBookVersification>\n" )
                myFile.write( "\n</BibleVersificationSystem>" )

        return systemMatchCount
    # end of checkVersificationSystem
# end of BibleVersificationSystems class


class BibleVersificationSystem:
    """
    Class for handling a particular Bible versification system.

    This class doesn't deal at all with XML, only with Python dictionaries, etc.
    """

    def __init__( self, systemName ):
        """
        Constructor: 
        """
        self._systemName = systemName
        self._bvss = BibleVersificationSystems().loadData() # Doesn't reload the XML unnecessarily :)
        result = self._bvss.getVersificationSystem( self._systemName )
        if result is not None:
            self.__chapterDataDict, self.__omittedVersesDict, self.__combinedVersesDict, self.__reorderedVersesDict = result['CV'], result['omitted'], result['combined'], result['reordered']
            # no longer true: assert( len(self.__chapterDataDict) == len(self.__omittedVersesDict) == len(self.__combinedVersesDict) == len(self.__reorderedVersesDict) )

        # Make sure we have the bible books codes data loaded and available
        self.__BibleBooksCodes = BibleBooksCodes().loadData()
    # end of __init__

    def __str__( self ):
        """
        This method returns the string representation of a Bible versification system.
        Will return more information if the verbosity setting is higher.
        
        @return: the name of a Bible object formatted as a string
        @rtype: string
        """
        result = "BibleVersificationSystem object"
        if Globals.verbosityLevel > 2:
            numChapters = 0
            for BBB,bookData in self.__chapterDataDict.items():
                numChapters += int( bookData['numChapters'] )
            if Globals.verbosityLevel > 3:
                result += ('\n' if result else '') + "  " + _("{} Bible versification system (data for {} books):").format( self._systemName, len(self.__chapterDataDict) )
                result += ('\n' if result else '') + "    " + _("Chapter/verse data for {} total chapters").format( numChapters )
                numOV = 0
                for BBB,bookData in self.__omittedVersesDict.items():
                    numOV += len(bookData)
                if numOV: result += ('\n' if result else '') + "    " + _("{} omitted verse data segments").format( numOV )
                else: result += ('\n' if result else '') + "    " + _("No omitted verse data segments")
                numCmV = 0
                for BBB,bookData in self.__combinedVersesDict.items():
                    numCmV += len(bookData)
                if numCmV: result += ('\n' if result else '') + "    " + _("{} combined verse data segments").format( numCmV )
                else: result += ('\n' if result else '') + "    " + _("No combined verse data segments")
                numRV = 0
                for BBB,bookData in self.__reorderedVersesDict.items():
                    numRV += len(bookData)
                if numRV: result += ('\n' if result else '') + "    " + _("{} reordered verse data segments").format( numRV )
                else: result += ('\n' if result else '') + "    " + _("No reordered verse data segments")
            else: # not that verbose
                result += ('\n' if result else '') + "  " + _("{} Bible versification system (data for {} books)").format( self._systemName, len(self.__chapterDataDict) )
        else: #not very verbose
            result += ('\n' if result else '') + " " + _("{} Bible versification system").format( self._systemName )
        return result
    # end of __str__

    def __len__( self ):
        """ Returns the number of books defined in this versification system.
            NOTE: This value is not useful for finding the number of books in a particular Bible. """
        return len( self.__chapterDataDict  )
    # end of __len__

    def numAvailableBooks( self ):
        """ Returns the number of available books in the versification system.
            NOTE: This value is not useful for finding the number of books in a particular Bible. """
        return len( self.__chapterDataDict )
    # end of numAvailableBooks

    def getVersificationSystemName( self ):
        """ Return the book order system name. """
        return self._systemName
    # end of getVersificationSystemName

    def getNumChapters( self, BBB ):
        """ Returns the number of chapters (int) in the given book.
            Returns None if we don't have any chapter information for this book. """
        assert( len(BBB) == 3 )
        if not self.__BibleBooksCodes.isValidReferenceAbbreviation( BBB ): raise KeyError
        if BBB in self.__chapterDataDict:
            return int( self.__chapterDataDict[BBB]['numChapters'] )
        # else
        return None
    # end of getNumChapters

    def getNumVerses( self, BBB, C ):
        """ Returns the number of verses (int) in the given book and chapter. """
        assert( len(BBB) == 3 )
        if isinstance(C, int): # Just double-check the parameter
            logging.debug( _("BibleVersificationSystem.getNumVerses was passed an integer chapter instead of a string with {} {}").format(BBB,C) )
            C = str( C )
        return int( self.__chapterDataDict[BBB][C] )
    # end of getNumVerses

    def isSingleChapterBook( self, BBB ):
        """ Returns True/False to indicate if this book only contains a single chapter.
            Returns None if we don't have any chapter information for this book. """
        assert( len(BBB) == 3 )
        if not self.__BibleBooksCodes.isValidReferenceAbbreviation( BBB ): raise KeyError
        if BBB in self.__chapterDataDict:
            return self.__chapterDataDict[BBB]['numChapters'] == '1'
        # else
        return None
    # end of isSingleChapterBook

    def getNumVersesList( self, BBB ):
        """ Returns a list containing an integer for each chapter indicating the number of verses. """
        assert( len(BBB) == 3 )
        myList = []
        for x in self.__chapterDataDict[BBB].keys():
            if x!='numChapters': myList.append( int( self.__chapterDataDict[BBB][x] ) )
        return myList
    # end of getNumVersesList

    def getOmittedVerseList( self, BBB, fullRefs=False ):
        """ Returns a list of (C,V) tuples noting omitted verses in the given book.

        If fullRefs are requested, the list consists of (BBB,C,V) tuples instead. """
        if fullRefs:
            return [(BBB,C,V) for (C,V) in self.__omittedVersesDict[BBB]]
        # else
        return self.__omittedVersesDict[BBB]
    # end of getOmittedVerseList

    def isOmittedVerse( self, referenceTuple ):
        """ Returns True/False indicating if the given reference is omitted in this system. """
        BBB, C, V, S = referenceTuple
        if isinstance(C, int): # Just double-check the parameter
            logging.debug( _("BibleVersificationSystem.isOmittedVerse was passed an integer chapter instead of a string with {} {}").format(BBB,C) )
            C = str( C )
        if isinstance(V, int): # Just double-check the parameter
            logging.debug( _("BibleVersificationSystem.isOmittedVerse was passed an integer verse instead of a string with {} {}:{}").format(BBB,C,V) )
            V = str( V )
        if BBB not in self.__omittedVersesDict: return False
        return (C,V) in self.__omittedVersesDict[BBB]
    # end of isOmittedVerse

    def getAuxilliaryVerseList( self, listName ):
        """ gets a list of auxilliary verse information for "omitted", "combined", or "reordered" verses. """
        assert( listName in ["omitted", "combined", "reordered"] )
        if listName=="omitted": return self.__omittedVersesDict
        if listName=="combined": return self.__combinedVersesDict
        if listName=="reordered": return self.__reorderedVersesDict
    # end of getAuxilliaryVerseList

    def isValidBCVRef( self, referenceTuple, referenceString=None, wantErrorMessages=False ):
        """ Returns True/False indicating if the given reference is valid in this system. """
        BBB, C, V, S = referenceTuple
        assert( len(BBB) == 3 )
        assert( not C or C.isdigit() ) # Should be no suffix on C (although it can be blank if the reference is for a whole book)
        assert( not V or V.isdigit() ) # Should be no suffix on V (although it can be blank if the reference is for a whole chapter)
        assert( not S or len(S)==1 and S.isalpha() ) # Suffix should be only one lower-case letter if anything
        myReferenceString = " (from '{}')".format(referenceString) if referenceString is not None else ''

        if BBB in self.__chapterDataDict:
            if C in self.__chapterDataDict[BBB]:
                if not V: return True # NOTE: This allows blank verse numbers (as a reference can refer to an entire chapter)
                if int(V) <= int(self.__chapterDataDict[BBB][C]):
                    if not self.isOmittedVerse( referenceTuple ):
                        return True
                    elif wantErrorMessages: logging.error( _("{} {}:{} is omitted in {} versification system {}").format(BBB,C,V,self.getVersificationSystemName(),myReferenceString) )
                elif wantErrorMessages: logging.error( _("{} {}:{} is invalid verse in {} versification system {}").format(BBB,C,V,self.getVersificationSystemName(),myReferenceString) )
            elif wantErrorMessages: logging.error( _("{} {}:{} is invalid chapter in {} versification system {}").format(BBB,C,V,self.getVersificationSystemName(),myReferenceString) )
        elif wantErrorMessages: logging.error( _("{} {}:{} is invalid book in {} versification system {}").format(BBB,C,V,self.getVersificationSystemName(),myReferenceString) )
        return False
    # end of isValidBCVRef

    def expandCVRange( self, startRef, endRef, referenceString=None, bookOrderSystem=None, wantErrorMessages=False ):
        """ Returns a list containing all valid references (inclusive) between the given values. """
        assert( startRef and len(startRef)==4 )
        assert( endRef and len(endRef)==4 )

        haveErrors, haveWarnings = False, False
        myReferenceString = " (from '{}')".format(referenceString) if referenceString is not None else ''
        if not self.isValidBCVRef( startRef, referenceString, wantErrorMessages ):
            haveErrors = True
        if not self.isValidBCVRef( endRef, referenceString, wantErrorMessages ):
            haveErrors = True
        if haveErrors: return None

        (BBB1, C1, V1, S1), (BBB2, C2, V2, S2) = startRef, endRef

        # Check book details
        if BBB1!=BBB2:
            if bookOrderSystem is None:
                if wantErrorMessages: logging.error( _("Book order system not specified (range covers {} to {}){}").format( BBB1, BBB2, myReferenceString ) )
                haveErrors = True
                return None
            if not bookOrderSystem.correctlyOrdered( BBB1, BBB2 ):
                if wantErrorMessages: logging.error( _("Book range out of order ({} before {}){}").format( BBB1, BBB2, myReferenceString ) )
                haveErrors = True
            if haveErrors: return None

        # Check chapter details
        C1int, C2int = int(C1), int(C2)
        if BBB1==BBB2 and C1int > C2int:
            if wantErrorMessages: logging.error( _("Chapter range out of order ({} before {}) in {}{}").format( C1, C2, BBB1, myReferenceString ) )
            haveErrors = True
        if haveErrors: return None

        # Check verse details
        if V1: V1int = int(V1)
        else: V1int = 1 # Start with verse one if no verse specified (e.g., for a chapter range)
        if V2: V2int = int(V2)
        else: V2int = self.getNumVerses( BBB2, C2 ) # End with the last verse if no verse specified (e.g., for a chapter range)
        if BBB1==BBB2 and C1int==C2int and V1int>=V2int:
            if wantErrorMessages: logging.error( _("Verse range out of order ({} before {}) in {} {}{}").format( V1, V2, BBB1, C1, myReferenceString ) )
            haveErrors = True
        if haveErrors: return None

        resultList = []
        if BBB1 == BBB2: # It's a chapter or verse range within the same book
            for Cint in range( C1int, C2int+1 ):
                if Cint==C1int and Cint==C2int: # We're on the only chapter
                    startVint = V1int
                    endVint = V2int
                elif Cint==C1int: # We're on the first chapter
                    startVint = V1int
                    endVint = self.getNumVerses( BBB1, str(Cint) )
                elif Cint==C2int: # We're on the final chapter
                    startVint = 1
                    endVint = V2int
                else: # Must be an inbetween chapter
                    startVint = 1
                    endVint = self.getNumVerses( BBB1, str(Cint) )
                for Vint in range( startVint, endVint+1 ):
                    if Cint==C1int and Vint==V1int: S = S1
                    elif Cint==C2int and Vint==V2int: S = S2
                    else: S = ''
                    resultList.append( (BBB1, str(Cint), str(Vint), S,) )
        else: # it's a range that spans multiple books
            BBB, Cfirst, Vfirst = BBB1, C1int, V1int
            while BBB != BBB2: # Go to the end of this book
                Clast = self.getNumChapters( BBB )
                for Cint in range( Cfirst, Clast+1 ):
                    Vlast = self.getNumVerses( BBB, str(Cint) )
                    if Cint==Cfirst: # We're on the first chapter
                        startVint = V1int
                        endVint = Vlast
                    else: # It's not the first chapter
                        startVint = 1
                        endVint = Vlast
                    for Vint in range( startVint, endVint+1 ):
                        if Cint==C1int and Vint==V1int: S = S1
                        else: S = ''
                        resultList.append( (BBB, str(Cint), str(Vint), S,) )
                BBB, Cfirst, Vfirst = bookOrderSystem.getNextBook( BBB ), 1, 1
            for Cint in range( 1, C2int+1 ): # Now finish the last book
                if Cint==C2int: # We're on the final chapter
                    startVint = 1
                    endVint = V2int
                else: # Must be an inbetween chapter
                    startVint = 1
                    endVint = self.getNumVerses( BBB1, str(Cint) )
                for Vint in range( startVint, endVint+1 ):
                    if Cint==C2int and Vint==V2int: S = S2
                    else: S = ''
                    resultList.append( (BBB2, str(Cint), str(Vint), S,) )

        #print( startRef, endRef, resultList, haveErrors, haveWarnings )
        return resultList #, haveErrors, haveWarnings
    # end of expandCVRange
# end of BibleVersificationSystem class


def main():
    """
    Main program to handle command line parameters and then run what they want.
    """
    # Handle command line parameters
    from optparse import OptionParser
    parser = OptionParser( version="v{}".format( versionString ) )
    #parser.add_option("-e", "--export", action="store_true", dest="export", default=False, help="export the XML files to .py and .h tables suitable for directly including into other programs")
    Globals.addStandardOptionsAndProcess( parser )

    if Globals.verbosityLevel > 1: print( "{} V{}".format( progName, versionString ) )

    # Demo the BibleVersificationSystems object
    bvss = BibleVersificationSystems().loadData() # Doesn't reload the XML unnecessarily :)
    print( bvss ) # Just print a summary
    print( _("Available system names are: {}").format( bvss.getAvailableVersificationSystemNames() ) )
    if 0:
        for systemName in ('RSV52','NLT96','KJV'): # Test the system against itself
            print( "\nTesting {} against the system...".format( systemName ) )
            testSystem = bvss.getVersificationSystem( systemName )
            bvss.checkVersificationSystem( "testSystem-"+systemName+'-a', testSystem['CV'] ) # Just compare the number of verses per chapter
            bvss.checkVersificationSystem( "testSystem-"+systemName+'-b', testSystem['CV'], testSystem ) # include omitted/combined/reordered verses checks this time
    #bvss.compareVersificationSystems( "Septuagint", "SeptuagintBE" )
    #bvss.compareVersificationSystems( "SeptuagintBE", "Septuagint" )
    #bvss.compareVersificationSystems( "NRSV", "NRS89" )
    #bvss.compareVersificationSystems( "NRS89", "NRSV" )
    bvss.compareVersificationSystems( "Vulgate", ["Vulgate1","Vulgate2"] )
    #bvss.compareVersificationSystems( "Vulgate1", ["Vulgate","Vulgate2"] )
    #bvss.compareVersificationSystems( "Vulgate2", ["Vulgate","Vulgate1"] )
    #bvss.compareVersificationSystems( "NRSV" )

    # Demo a BibleVersificationSystem object -- this is the one most likely to be wanted by a user
    bvs = BibleVersificationSystem( "NLT96" )
    if bvs is not None:
        print( bvs ) # Just print a summary
        print( "Number of available books for {} is {}".format(bvs.getVersificationSystemName(),bvs.numAvailableBooks()) )
        BBB = 'PRO'
        print( "{} has {} chapters in {}".format(BBB,bvs.getNumChapters(BBB),bvs.getVersificationSystemName()) )
        BBB = 'MAT'; C='1'
        print( "{} {} has {} verses".format(BBB,C,bvs.getNumVerses(BBB,C)) )
        BBB = 'DAN'
        print( "Verse list for the {} chapters in {} is: {}".format(bvs.getNumChapters(BBB),BBB,bvs.getNumVersesList(BBB)) )
        BBB = 'MAT'; C='17'; V='21'; S=''; refTuple = (BBB,C,V,S,)
        print( "{} {} {} {} is omitted: {}".format(BBB,C,V,S,bvs.isOmittedVerse(refTuple)) )
        BBB = 'MAT'; C='17'; V='22'; S=''; refTuple = (BBB,C,V,S,)
        print( "{} {} {} {} is omitted: {}".format(BBB,C,V,S,bvs.isOmittedVerse(refTuple)) )
        BBB = 'MRK'; C='7'; V='16'; S=''; refTuple = (BBB,C,V,S,)
        print( "{} {} {} {} is omitted: {}".format(BBB,C,V,S,bvs.isOmittedVerse(refTuple)) )
        print( "Omitted verses in {} are: {}".format(BBB,bvs.getOmittedVerseList(BBB)) )
        for myRange in ((('MAT','2','1',''),('MAT','2','5','')), (('MAT','3','2','b'),('MAT','3','6','a')), (('MAT','3','15',''),('MAT','4','2','')), (('MAT','3','16','b'),('MAT','4','3','a')), (('MAT','3','2',''),('MAT','2','6',''))):
            print( "Expanding {} gives {}".format( myRange, bvs.expandCVRange( myRange[0],myRange[1],wantErrorMessages=True) ) )
# end of main

if __name__ == '__main__':
    main()
# end of BibleVersificationSystems.py