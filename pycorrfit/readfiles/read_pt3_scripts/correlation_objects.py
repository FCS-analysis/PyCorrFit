import numpy as np
import os, sys
#from correlation_methods import *
#from import_methods import *
import time
#from fitting_methods import equation_
#from lmfit import minimize, Parameters,report_fit,report_errors, fit_report

from .correlation_methods import *
from .import_methods import *


"""FCS Bulk Correlation Software

    Copyright (C) 2015  Dominic Waithe

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

class picoObject():
    #This is the class which holds the .pt3 data and parameters
    def __init__(self,filepath, par_obj,fit_obj):
    
        #parameter object and fit object. If 
        self.par_obj = par_obj
        self.fit_obj = fit_obj
        self.type = 'mainObject'
        
        #self.PIE = 0
        self.filepath = str(filepath)
        self.nameAndExt = os.path.basename(self.filepath).split('.')
        self.name = self.nameAndExt[0]
        self.par_obj.data.append(filepath);
        self.par_obj.objectRef.append(self)
        
        #Imports pt3 file format to object.
        self.unqID = self.par_obj.numOfLoaded
        
        #For fitting.
        self.objId1 = None
        self.objId2 = None
        self.objId3 = None
        self.objId4 = None
        self.processData();
        
        self.plotOn = True;


    def processData(self):

        self.NcascStart = self.par_obj.NcascStart
        self.NcascEnd = self.par_obj.NcascEnd
        self.Nsub = self.par_obj.Nsub
        self.winInt = self.par_obj.winInt
        self.photonCountBin = self.par_obj.photonCountBin
        
        #File import 
        self.subChanArr, self.trueTimeArr, self.dTimeArr,self.resolution = pt3import(self.filepath)
        
        #Colour assigned to file.
        self.color = self.par_obj.colors[self.unqID % len(self.par_obj.colors)]

        #How many channels there are in the files.
        self.numOfCH =  np.unique(np.array(self.subChanArr)).__len__()-1 #Minus 1 because not interested in channel 15.
        #TODO Generates the interleaved excitation channel if required. 
        #if (self.aug == 'PIE'):
            #self.pulsedInterleavedExcitation()
        
        #Finds the numbers which address the channels.
        self.ch_present = np.unique(np.array(self.subChanArr[0:100]))

        #Calculates decay function for both channels.
        self.photonDecayCh1,self.decayScale1 = delayTime2bin(np.array(self.dTimeArr),np.array(self.subChanArr),self.ch_present[0],self.winInt)
        
        if self.numOfCH ==  2:
            self.photonDecayCh2,self.decayScale2 = delayTime2bin(np.array(self.dTimeArr),np.array(self.subChanArr),self.ch_present[1],self.winInt)

        #Time series of photon counts. For visualisation.
        self.timeSeries1,self.timeSeriesScale1 = delayTime2bin(np.array(self.trueTimeArr)/1000000,np.array(self.subChanArr),self.ch_present[0],self.photonCountBin)
        if self.numOfCH ==  2:
            self.timeSeries2,self.timeSeriesScale2 = delayTime2bin(np.array(self.trueTimeArr)/1000000,np.array(self.subChanArr),self.ch_present[1],self.photonCountBin)

        
        #Calculates the Auto and Cross-correlation functions.
        self.crossAndAuto(np.array(self.trueTimeArr),np.array(self.subChanArr))
        
        
           
       
        
        if self.fit_obj != None:
            #If fit object provided then creates fit objects.
            if self.objId1 == None:
                corrObj= corrObject(self.filepath,self.fit_obj);
                self.objId1 = corrObj.objId
                self.fit_obj.objIdArr.append(corrObj.objId)
                self.objId1.name = self.name+'_CH0_Auto_Corr'
                self.objId1.ch_type = 0 #channel 0 Auto
                self.objId1.prepare_for_fit()
            self.objId1.autoNorm = np.array(self.autoNorm[:,0,0]).reshape(-1)
            self.objId1.autotime = np.array(self.autotime).reshape(-1)
            self.objId1.param = self.fit_obj.def_param
            
            
            if self.numOfCH ==  2:
                if self.objId3 == None:
                    corrObj= corrObject(self.filepath,self.fit_obj);
                    self.objId3 = corrObj.objId
                    self.fit_obj.objIdArr.append(corrObj.objId)
                    self.objId3.name = self.name+'_CH1_Auto_Corr'
                    self.objId3.ch_type = 1 #channel 1 Auto
                    self.objId3.prepare_for_fit()
                self.objId3.autoNorm = np.array(self.autoNorm[:,1,1]).reshape(-1)
                self.objId3.autotime = np.array(self.autotime).reshape(-1)
                self.objId3.param = self.fit_obj.def_param
                
                if self.objId2 == None:
                    corrObj= corrObject(self.filepath,self.fit_obj);
                    self.objId2 = corrObj.objId
                    self.fit_obj.objIdArr.append(corrObj.objId)
                    self.objId2.name = self.name+'_CH01_Cross_Corr'
                    self.objId2.ch_type = 2 #01cross
                    self.objId2.prepare_for_fit()
                self.objId2.autoNorm = np.array(self.autoNorm[:,0,1]).reshape(-1)
                self.objId2.autotime = np.array(self.autotime).reshape(-1)
                self.objId2.param = self.fit_obj.def_param
                

                if self.objId4 == None:
                    corrObj= corrObject(self.filepath,self.fit_obj);
                    self.objId4 = corrObj.objId
                    self.fit_obj.objIdArr.append(corrObj.objId)
                    self.objId4.name = self.name+'_CH10_Cross_Corr'
                    self.objId4.ch_type = 3 #10cross
                    self.objId4.prepare_for_fit()
                self.objId4.autoNorm = np.array(self.autoNorm[:,1,0]).reshape(-1)
                self.objId4.autotime = np.array(self.autotime).reshape(-1)
                self.objId4.param = self.fit_obj.def_param
                
            self.fit_obj.fill_series_list()
        self.dTimeMin = 0
        self.dTimeMax = np.max(self.dTimeArr)
        self.subDTimeMin = self.dTimeMin
        self.subDTimeMax = self.dTimeMax
        del self.subChanArr 
        del self.trueTimeArr 
        del self.dTimeArr
    def crossAndAuto(self,trueTimeArr,subChanArr):
        #For each channel we loop through and find only those in the correct time gate.
        #We only want photons in channel 1 or two.
        y = trueTimeArr[subChanArr < 3]
        validPhotons = subChanArr[subChanArr < 3 ]


        #Creates boolean for photon events in either channel.
        num = np.zeros((validPhotons.shape[0],2))
        num[:,0] = (np.array([np.array(validPhotons) ==self.ch_present[0]])).astype(np.int32)
        if self.numOfCH ==2:
            num[:,1] = (np.array([np.array(validPhotons) ==self.ch_present[1]])).astype(np.int32)


        self.count0 = np.sum(num[:,0]) 
        self.count1 = np.sum(num[:,1])

        t1 = time.time()
        auto, self.autotime = tttr2xfcs(y,num,self.NcascStart,self.NcascEnd, self.Nsub)
        t2 = time.time()
        print 'timing',t2-t1
        

        #Normalisation of the TCSPC data:
        maxY = np.ceil(max(self.trueTimeArr))
        self.autoNorm = np.zeros((auto.shape))
        self.autoNorm[:,0,0] = ((auto[:,0,0]*maxY)/(self.count0*self.count0))-1
        
        if self.numOfCH ==  2:
            self.autoNorm[:,1,1] = ((auto[:,1,1]*maxY)/(self.count1*self.count1))-1
            self.autoNorm[:,1,0] = ((auto[:,1,0]*maxY)/(self.count1*self.count0))-1
            self.autoNorm[:,0,1] = ((auto[:,0,1]*maxY)/(self.count0*self.count1))-1
            

        #Normalisaation of the decay functions.
        self.photonDecayCh1Min = self.photonDecayCh1-np.min(self.photonDecayCh1)
        self.photonDecayCh1Norm = self.photonDecayCh1Min/np.max(self.photonDecayCh1Min)
        
        
        if self.numOfCH ==  2:
            self.photonDecayCh2Min = self.photonDecayCh2-np.min(self.photonDecayCh2)
            self.photonDecayCh2Norm = self.photonDecayCh2Min/np.max(self.photonDecayCh2Min)
        
        return 
   

    
    
class subPicoObject():
    def __init__(self,parentId,xmin,xmax,TGid,par_obj):
        #Binning window for decay function
        self.TGid = TGid
        #Parameters for auto-correlation and cross-correlation.
        self.parentId = parentId
        self.par_obj = par_obj
        self.NcascStart = self.parentId.NcascStart
        self.NcascEnd = self.parentId.NcascEnd
        self.Nsub = self.parentId.Nsub
        self.fit_obj = self.parentId.fit_obj
        
        self.type = 'subObject'
        #Appends the object to the subObject register.
        self.par_obj.subObjectRef.append(self)
        self.unqID = self.par_obj.subNum
        self.parentUnqID = self.parentId.unqID
        #self.chanArr = parentObj.chanArr
        #self.trueTimeArr = self.parentId.trueTimeArr
        #self.dTimeArr = self.parentId.dTimeArr
        self.color = self.parentId.color
        self.numOfCH = self.parentId.numOfCH
        self.ch_present = self.parentId.ch_present

        self.filepath = str(self.parentId.filepath)
        self.xmin = xmin
        self.xmax = xmax

        self.nameAndExt = os.path.basename(self.filepath).split('.')
        self.name = 'TG-'+str(self.unqID)+'-xmin_'+str(round(xmin,0))+'-xmax_'+str(round(xmax,0))+'-'+self.nameAndExt[0]

        self.objId1 = None
        self.objId2 = None
        self.objId3 = None
        self.objId4 = None
        self.processData();
        self.plotOn = True
        
        
    def processData(self):
        self.NcascStart= self.par_obj.NcascStart
        self.NcascEnd= self.par_obj.NcascEnd
        self.Nsub = self.par_obj.Nsub
        self.winInt = self.par_obj.winInt
        
        
        self.subChanArr, self.trueTimeArr, self.dTimeArr,self.resolution = pt3import(self.filepath)
        
        
        
        self.subArrayGeneration(self.xmin,self.xmax,np.array(self.subChanArr))
        
        


        self.dTimeMin = self.parentId.dTimeMin
        self.dTimeMax = self.parentId.dTimeMax
        self.subDTimeMin = self.dTimeMin
        self.subDTimeMax = self.dTimeMax
        

        
        #Adds names to the fit function for later fitting.
        if self.objId1 == None:
            corrObj= corrObject(self.filepath,self.fit_obj);
            self.objId1 = corrObj.objId
            self.fit_obj.objIdArr.append(corrObj.objId)
            self.objId1.name = self.name+'_CH0_Auto_Corr'
            self.objId1.ch_type = 0 #channel 0 Auto
            self.objId1.prepare_for_fit()
        self.objId1.autoNorm = np.array(self.autoNorm[:,0,0]).reshape(-1)
        self.objId1.autotime = np.array(self.autotime).reshape(-1)
        self.objId1.param = self.fit_obj.def_param
        
        
        if self.numOfCH ==2:
            if self.objId3 == None:
                corrObj= corrObject(self.filepath,self.fit_obj);
                self.objId3 = corrObj.objId
                self.fit_obj.objIdArr.append(corrObj.objId)
                self.objId3.name = self.name+'_CH1_Auto_Corr'
                self.objId3.ch_type = 1 #channel 1 Auto
                self.objId3.prepare_for_fit()
            self.objId3.autoNorm = np.array(self.autoNorm[:,1,1]).reshape(-1)
            self.objId3.autotime = np.array(self.autotime).reshape(-1)
            self.objId3.param = self.fit_obj.def_param
            if self.objId2 == None:
                corrObj= corrObject(self.filepath,self.fit_obj);
                self.objId2 = corrObj.objId
                self.fit_obj.objIdArr.append(corrObj.objId)
                self.objId2.name = self.name+'_CH01_Cross_Corr'
                self.objId2.ch_type = 2 #channel 01 Cross
                self.objId2.prepare_for_fit()
            self.objId2.autoNorm = np.array(self.autoNorm[:,0,1]).reshape(-1)
            self.objId2.autotime = np.array(self.autotime).reshape(-1)
            self.objId2.param = self.fit_obj.def_param
            if self.objId4 == None:
                corrObj= corrObject(self.filepath,self.fit_obj);
                self.objId4 = corrObj.objId
                self.fit_obj.objIdArr.append(corrObj.objId)
                self.objId4.name = self.name+'_CH10_Cross_Corr'
                self.objId4.ch_type = 3 #channel 10 Cross
                self.objId4.prepare_for_fit()
            self.objId4.autoNorm = np.array(self.autoNorm[:,1,0]).reshape(-1)
            self.objId4.autotime = np.array(self.autotime).reshape(-1)
            self.objId4.param = self.fit_obj.def_param
            
        
        self.fit_obj.fill_series_list()  
        del self.subChanArr 
        del self.trueTimeArr 
        del self.dTimeArr 
    


    def subArrayGeneration(self,xmin,xmax,subChanArr):
        if(xmax<xmin):
            xmin1 = xmin
            xmin = xmax
            xmax = xmin1
        #self.subChanArr = np.array(self.chanArr)
        #Finds those photons which arrive above certain time or below certain time.
        photonInd = np.logical_and(self.dTimeArr>=xmin, self.dTimeArr<=xmax).astype(np.bool)
        
        subChanArr[np.invert(photonInd).astype(np.bool)] = 16
        
        self.crossAndAuto(subChanArr)

        return
    def crossAndAuto(self,subChanArr):
        #We only want photons in channel 1 or two.
        validPhotons = subChanArr[subChanArr < 3]
        y = self.trueTimeArr[subChanArr < 3]
        #Creates boolean for photon events in either channel.
        num = np.zeros((validPhotons.shape[0],2))
        num[:,0] = (np.array([np.array(validPhotons) ==self.ch_present[0]])).astype(np.int)
        if self.numOfCH == 2:
            num[:,1] = (np.array([np.array(validPhotons) ==self.ch_present[1]])).astype(np.int)

        self.count0 = np.sum(num[:,0]) 
        self.count1 = np.sum(num[:,1]) 
        #Function which calculates auto-correlation and cross-correlation.



        auto, self.autotime = tttr2xfcs(y,num,self.NcascStart,self.NcascEnd, self.Nsub)

        maxY = np.ceil(max(self.trueTimeArr))
        self.autoNorm = np.zeros((auto.shape))
        self.autoNorm[:,0,0] = ((auto[:,0,0]*maxY)/(self.count0*self.count0))-1
        if self.numOfCH ==2:
            self.autoNorm[:,1,1] = ((auto[:,1,1]*maxY)/(self.count1*self.count1))-1
            self.autoNorm[:,1,0] = ((auto[:,1,0]*maxY)/(self.count1*self.count0))-1
            self.autoNorm[:,0,1] = ((auto[:,0,1]*maxY)/(self.count0*self.count1))-1

        return 

class corrObject():
    def __init__(self,filepath,parentFn):
        #the container for the object.
        self.parentFn = parentFn
        self.type = 'corrObject'
        self.filepath = str(filepath)
        self.nameAndExt = os.path.basename(self.filepath).split('.')
        self.name = self.nameAndExt[0]
        self.ext = self.nameAndExt[-1]
        self.autoNorm=[]
        self.autotime=[]
        self.model_autoNorm =[]
        self.model_autotime = []
        self.datalen= []
        self.objId = self;
        self.param = []
        self.goodFit = True
        self.fitted = False
        self.checked = False
        self.toFit = False
       
        #main.data.append(filepath);
        #The master data object reference 
        #main.corrObjectRef.append(self)
        #The id in terms of how many things are loaded.
        #self.unqID = main.label.numOfLoaded;
        #main.label.numOfLoaded = main.label.numOfLoaded+1
    def prepare_for_fit(self):
        if self.parentFn.ch_check_ch0.isChecked() == True and self.ch_type == 0:
            self.toFit = True
        if self.parentFn.ch_check_ch1.isChecked() == True and self.ch_type == 1:
            self.toFit = True
            
        if self.parentFn.ch_check_ch01.isChecked() == True and self.ch_type == 2:
            self.toFit = True
        if self.parentFn.ch_check_ch10.isChecked() == True and self.ch_type == 3:
            self.toFit = True
        #self.parentFn.modelFitSel.clear()
        #for objId in self.parentFn.objIdArr:
         #   if objId.toFit == True:
          #      self.parentFn.modelFitSel.addItem(objId.name)
        self.parentFn.updateFitList()
    def residual(self, param, x, data,options):
    
        A = equation_(param, x,options)
        residuals = data-A
        return residuals
    def fitToParameters(self):
        self.parentFn.updateParamFirst()
        self.parentFn.updateTableFirst()
        self.parentFn.updateParamFirst()
        

        #convert line coordinate
        
        #Find the index of the nearest point in the scale.
        
        data = np.array(self.autoNorm).astype(np.float64).reshape(-1)
        scale = np.array(self.autotime).astype(np.float64).reshape(-1)
        indx_L = int(np.argmin(np.abs(scale -  self.parentFn.dr.xpos)))
        indx_R = int(np.argmin(np.abs(scale -  self.parentFn.dr1.xpos)))
        

        res = minimize(self.residual, self.param, args=(scale[indx_L:indx_R+1],data[indx_L:indx_R+1], self.parentFn.def_options))
        self.residualVar = res.residual
        output = fit_report(self.param)
        print 'residual',res.chisqr
        if(res.chisqr>0.05):
            print 'CAUTION DATA DID NOT FIT WELL CHI^2 >0.05',res.chisqr
            self.goodFit = False
        else:
            self.goodFit = True
        self.fitted = True
        self.chisqr = res.chisqr
        rowArray =[];
        localTime = time.asctime( time.localtime(time.time()) )
        rowArray.append(str(self.name))  
        rowArray.append(str(localTime))
        rowArray.append(str(self.parentFn.diffModEqSel.currentText()))
        rowArray.append(str(self.parentFn.def_options['Diff_species']))
        rowArray.append(str(self.parentFn.tripModEqSel.currentText()))
        rowArray.append(str(self.parentFn.def_options['Triplet_species']))
        rowArray.append(str(self.parentFn.dimenModSel.currentText()))
        rowArray.append(str(scale[indx_L]))
        rowArray.append(str(scale[indx_R]))

        for key, value in self.param.iteritems() :
            rowArray.append(str(value.value))
            rowArray.append(str(value.stderr))
            if key =='GN0':
                try:
                    rowArray.append(str(1/value.value))
                except:
                    rowArray.append(str(0))
        
        self.rowText = rowArray
        
        self.parentFn.updateTableFirst();
        self.model_autoNorm = equation_(self.param, scale[indx_L:indx_R+1],self.parentFn.def_options)
        self.model_autotime = scale[indx_L:indx_R+1]
        self.parentFn.on_show()

        #self.parentFn.axes.plot(model_autotime,model_autoNorm, 'o-')
        #self.parentFn.canvas.draw();
    
    def load_from_file(self,channel):
        tscale = [];
        tdata = [];
        if self.ext == 'SIN':
            self.parentFn.objIdArr.append(self.objId)
            proceed = False
            
            for line in csv.reader(open(self.filepath, 'rb'),delimiter='\t'):
                
                if proceed ==True:
                    if line ==[]:
                        break;
                    
                    
                    tscale.append(float(line[0]))
                    tdata.append(float(line[channel+1]))
                else:
                  
                  if (str(line)  == "[\'[CorrelationFunction]\']"):
                    proceed = True;
            

            self.autoNorm= np.array(tdata).astype(np.float64).reshape(-1)
            self.autotime= np.array(tscale).astype(np.float64).reshape(-1)*1000
            self.name = self.name+'-CH'+str(channel)
            self.ch_type = channel;
            self.prepare_for_fit()


            self.param = self.parentFn.def_param
            self.parentFn.fill_series_list()
            
        
                    #Where we add the names.


        if self.ext == 'csv':
            
            self.parentFn.objIdArr.append(self)
            
            c = 0
            
            for line in csv.reader(open(self.filepath, 'rb')):
                if (c >0):
                    tscale.append(line[0])
                    tdata.append(line[1])
                c +=1;

            self.autoNorm= np.array(tdata).astype(np.float64).reshape(-1)
            self.autotime= np.array(tscale).astype(np.float64).reshape(-1)
            self.ch_type = 0
            self.datalen= len(tdata)
            self.objId.prepare_for_fit()





