# -*- coding: utf-8 -*-
""" PicoQuant functionalities from FCS_viewer

This file contains classes and functions that are used by PyCorrFit
to import PicoQuant *.pt3 files.

The code was written by
Dr. Dominic Waithe
Wolfson Imaging Centre.
Weatherall Institute of Molecular Medicine.
University of Oxford

https://github.com/dwaithe/FCS_viewer

See Also:
The wrapper: `read_pt3_PicoQuant.py`
Fast implementation of dividAndConquer: `read_pt3_PicoQuant_fib4.pyx`
"""
import numpy as np
import os 
import struct
import read_pt3_PicoQuant_fib4 as fib4


__all__ = ["picoObject", "delayTime2bin", "pt3import", "tttr2xfcs"]


class picoObject():
    #This is the function which you store the variables in.
    def __init__(self,filepath):
        #Binning window for decay function
       
        #Parameters for auto-correlation and cross-correlation.
        
        self.parentId = None
        self.type = 'mainObject'
        self.PIE = 0
        self.filepath = str(filepath)
        self.nameAndExt = os.path.basename(self.filepath).split('.')
        self.name = self.nameAndExt[0]
        main.data.append(filepath);
        main.objectRef.append(self)
        #Imports pt3 file format to object.
        self.unqID = main.label.numOfLoaded
        self.objId1 = None
        self.objId2 = None
        self.objId3 = None
        self.objId4 = None
        self.processData();
        


        self.dTimeMin = 0
        self.dTimeMax = np.max(self.dTimeArr)
        self.subDTimeMin = self.dTimeMin
        self.subDTimeMax = self.dTimeMax
        self.plotOn = True;
        
        main.label.numOfLoaded = main.label.numOfLoaded+1
        main.label.generateList()
        main.TGScrollBoxObj.generateList()
        main.updateCombo()
        main.cbx.setCurrentIndex(main.label.numOfLoaded-1)
        main.plot_PhotonCount(main.label.numOfLoaded-1)
        

        

    def processData(self):
        self.NcascStart=int(main.NcascStartEdit.text())
        self.NcascEnd =int(main.NcascEndEdit.text())
        self.Nsub =int(main.NsubEdit.text())
        self.winInt = float(main.winIntEdit.text())
        self.photonCountBin = float(main.photonCountEdit.text())
        
        #File import 
        self.chanArr, self.trueTimeArr, self.dTimeArr,self.resolution = pt3import(self.filepath)
        
        #Colour assigned to file.
        self.color = main.colors[self.unqID]
        
        #Channel ids of each photon.
        self.subChanArr = np.array(self.chanArr)
        
        #Generates the interleaved excitation channel if required.
        if (self.PIE != 0):
            self.pulsedInterleavedExcitation()


        #Calculates decay function for  both channels.
        self.photonDecayCh1,self.decayScale1 = delayTime2bin(self.dTimeArr,self.subChanArr,1,self.winInt)
        self.photonDecayCh2,self.decayScale2 = delayTime2bin(self.dTimeArr,self.subChanArr,2,self.winInt)
        
        #Time series of photon counts
        self.timeSeries1,self.timeSeriesScale1 = delayTime2bin(self.trueTimeArr/1000000,self.subChanArr,1,self.photonCountBin)
        self.timeSeries2,self.timeSeriesScale2 = delayTime2bin(self.trueTimeArr/1000000,self.subChanArr,2,self.photonCountBin)

        #Calculates initial auto-correlation and cross-correlation.
        self.auto, self.autotime = self.crossAndAuto()
        

        #Normalisation of the TCSPC data:
        maxY = np.ceil(max(self.trueTimeArr))
        self.autoNorm = np.zeros((self.auto.shape))
        self.autoNorm[:,0,0] = ((self.auto[:,0,0]*maxY)/(self.count0*self.count0))-1
        self.autoNorm[:,1,1] = ((self.auto[:,1,1]*maxY)/(self.count1*self.count1))-1
        self.autoNorm[:,1,0] = ((self.auto[:,1,0]*maxY)/(self.count1*self.count0))-1
        self.autoNorm[:,0,1] = ((self.auto[:,0,1]*maxY)/(self.count0*self.count1))-1
        

        #Normalisaation of the decay functions.
        self.photonDecayCh1Min = self.photonDecayCh1-np.min(self.photonDecayCh1)
        self.photonDecayCh1Norm = self.photonDecayCh1Min/np.max(self.photonDecayCh1Min)
        self.photonDecayCh2Min = self.photonDecayCh2-np.min(self.photonDecayCh2)
        self.photonDecayCh2Norm = self.photonDecayCh2Min/np.max(self.photonDecayCh2Min)

       #Adds names to the fit function for later fitting.
        if self.objId1 == None:
            corrObj= corrObject(self.filepath,form);
            self.objId1 = corrObj.objId
            form.objIdArr.append(corrObj.objId)
            self.objId1.name = self.name+'_CH1_Auto_Corr'
            self.objId1.updateFitList()
        self.objId1.autoNorm = np.array(self.autoNorm[:,0,0]).reshape(-1)
        self.objId1.autotime = np.array(self.autotime).reshape(-1)
        self.objId1.param = form.def_param
        form.fill_series_list(form.objIdArr)
        

        if self.objId2 == None:
            corrObj= corrObject(self.filepath,form);
            self.objId2 = corrObj.objId
            form.objIdArr.append(corrObj.objId)
            self.objId2.name = self.name+'_CH1_Cross_Corr'
            self.objId2.updateFitList()
        self.objId2.autoNorm = np.array(self.autoNorm[:,0,1]).reshape(-1)
        self.objId2.autotime = np.array(self.autotime).reshape(-1)
        self.objId2.param = form.def_param
        form.fill_series_list(form.objIdArr)

        if self.objId3 == None:
            corrObj= corrObject(self.filepath,form);
            self.objId3 = corrObj.objId
            form.objIdArr.append(corrObj.objId)
            self.objId3.name = self.name+'_CH2_Auto_Corr'
            self.objId3.updateFitList()
        self.objId3.autoNorm = np.array(self.autoNorm[:,1,1]).reshape(-1)
        self.objId3.autotime = np.array(self.autotime).reshape(-1)
        self.objId3.param = form.def_param
        form.fill_series_list(form.objIdArr)

        if self.objId4 == None:
            corrObj= corrObject(self.filepath,form);
            self.objId4 = corrObj.objId
            form.objIdArr.append(corrObj.objId)
            self.objId4.name = self.name+'_CH2_Cross_Corr'
            self.objId4.updateFitList()
        self.objId4.autoNorm = np.array(self.autoNorm[:,1,0]).reshape(-1)
        self.objId4.autotime = np.array(self.autotime).reshape(-1)
        self.objId4.param = form.def_param
        form.fill_series_list(form.objIdArr)


    def pulsedInterleavedExcitation(self):
        #PIE Advanced Fluorescence Fluctuation Spectroscopy with Pulsed Interleaved Excitation Development and Applications
        #Matthias Holler aus Bergisch Gladbach 2011
        switchInd = np.where([self.subChanArr == 15])[1]
        print 'dimensions before: '+str(switchInd)
        newArr =[]
        if self.PIE == 1:
            
            self.subChanArr[0:switchInd[0]] = 18;
            for i in range(2,switchInd.shape[0],2):
                self.subChanArr[switchInd[i-1]:switchInd[i]] = 18;
                #print 'from: '+str(switchInd[i-1])+str('to: '+str(switchInd[i]))
        if self.PIE == 2:
            for i in range(1,switchInd.shape[0],2):
                self.subChanArr[switchInd[i-1]:switchInd[i]] = 18;
            self.subChanArr[switchInd[-1]:-1] = 18;
        print 'dimensions after: '+str(self.subChanArr[switchInd.shape[0]-100:-1])
        print 'how it looks aftert'+str(np.sum([self.subChanArr == 15]))

    def crossAndAuto(self):
        #We only want photons in channel 1 or two.
        validPhotons = self.subChanArr[self.subChanArr < 3]
        y = self.trueTimeArr[self.subChanArr < 3]
        #Creates boolean for photon events in either channel.
        num = np.zeros((validPhotons.shape[0],2))
        num[:,0] = (np.array([np.array(validPhotons) ==1])).astype(np.int)
        num[:,1] = (np.array([np.array(validPhotons) ==2])).astype(np.int)
        self.count0 = np.sum(num[:,0]) 
        self.count1 = np.sum(num[:,1]) 
        #Function which calculates auto-correlation and cross-correlation.
        autoOutput, autoTimeOutput = tttr2xfcs(y,num,self.NcascStart,self.NcascEnd, self.Nsub)
        #Convert to ms units
        return autoOutput, autoTimeOutput;





def delayTime2bin(dTimeArr, chanArr, chanNum, winInt):
    decayTime = np.array(dTimeArr)
    decayTimeCh =decayTime[chanArr == chanNum] 
    
    
    minDecayTime = np.min(decayTimeCh).astype(np.int32)
    maxDecayTime = np.max(decayTimeCh).astype(np.int32)
    
    numBins = np.ceil((maxDecayTime-minDecayTime)/winInt)
    maxDecayTime = numBins*winInt
    numBins = maxDecayTime/winInt

    mybins = np.linspace(minDecayTime,maxDecayTime, numBins+1)

    #bins are valued as half their span.
    photonsInBin, jnk = np.histogram(decayTimeCh, mybins)
    decayScale = mybins[:-1]+(winInt/2)
    
    #decayScale =  np.arange(0,decayTimeCh.shape[0])
   
       
    return np.array(photonsInBin).astype(np.float32), decayScale


def pt3import(filepath):
    """The file import for the .pt3 file"""
    f = open(filepath, 'rb')
    Ident = f.read(16)
    FormatVersion = f.read(6)
    CreatorName = f.read(18)
    CreatorVersion = f.read(12)
    FileTime = f.read(18)
    CRLF = f.read(2)
    CommentField = f.read(256)
    Curves = struct.unpack('i', f.read(4))[0]
    BitsPerRecord = struct.unpack('i', f.read(4))[0]
    RoutingChannels = struct.unpack('i', f.read(4))[0]
    NumberOfBoards = struct.unpack('i', f.read(4))[0]
    ActiveCurve = struct.unpack('i', f.read(4))[0]
    MeasurementMode = struct.unpack('i', f.read(4))[0]
    SubMode = struct.unpack('i', f.read(4))[0]
    RangeNo = struct.unpack('i', f.read(4))[0]
    Offset = struct.unpack('i', f.read(4))[0]
    AcquisitionTime = struct.unpack('i', f.read(4))[0]
    StopAt = struct.unpack('i', f.read(4))[0]
    StopOnOvfl = struct.unpack('i', f.read(4))[0]
    Restart = struct.unpack('i', f.read(4))[0]
    DispLinLog = struct.unpack('i', f.read(4))[0]
    DispTimeFrom = struct.unpack('i', f.read(4))[0]
    DispTimeTo = struct.unpack('i', f.read(4))[0]
    DispCountFrom = struct.unpack('i', f.read(4))[0]
    DispCountTo = struct.unpack('i', f.read(4))[0]
    DispCurveMapTo = [];
    DispCurveShow =[];
    for i in range(0,8):
        DispCurveMapTo.append(struct.unpack('i', f.read(4))[0]);
        DispCurveShow.append(struct.unpack('i', f.read(4))[0]);
    ParamStart =[];
    ParamStep =[];
    ParamEnd =[];
    for i in range(0,3):
        ParamStart.append(struct.unpack('i', f.read(4))[0]);
        ParamStep.append(struct.unpack('i', f.read(4))[0]);
        ParamEnd.append(struct.unpack('i', f.read(4))[0]);
        
    RepeatMode = struct.unpack('i', f.read(4))[0]
    RepeatsPerCurve = struct.unpack('i', f.read(4))[0]
    RepeatTime = struct.unpack('i', f.read(4))[0]
    RepeatWait = struct.unpack('i', f.read(4))[0]
    ScriptName = f.read(20)

    #The next is a board specific header

    HardwareIdent = f.read(16)
    HardwareVersion = f.read(8)
    HardwareSerial = struct.unpack('i', f.read(4))[0]
    SyncDivider = struct.unpack('i', f.read(4))[0]

    CFDZeroCross0 = struct.unpack('i', f.read(4))[0]
    CFDLevel0 = struct.unpack('i', f.read(4))[0]
    CFDZeroCross1 = struct.unpack('i', f.read(4))[0]
    CFDLevel1 = struct.unpack('i', f.read(4))[0]

    Resolution = struct.unpack('f', f.read(4))[0]

    #below is new in format version 2.0

    RouterModelCode      = struct.unpack('i', f.read(4))[0]
    RouterEnabled        = struct.unpack('i', f.read(4))[0]

    #Router Ch1
    RtChan1_InputType    = struct.unpack('i', f.read(4))[0]
    RtChan1_InputLevel   = struct.unpack('i', f.read(4))[0]
    RtChan1_InputEdge    = struct.unpack('i', f.read(4))[0]
    RtChan1_CFDPresent   = struct.unpack('i', f.read(4))[0]
    RtChan1_CFDLevel     = struct.unpack('i', f.read(4))[0]
    RtChan1_CFDZeroCross = struct.unpack('i', f.read(4))[0]
    #Router Ch2
    RtChan2_InputType    = struct.unpack('i', f.read(4))[0]
    RtChan2_InputLevel   = struct.unpack('i', f.read(4))[0]
    RtChan2_InputEdge    = struct.unpack('i', f.read(4))[0]
    RtChan2_CFDPresent   = struct.unpack('i', f.read(4))[0]
    RtChan2_CFDLevel     = struct.unpack('i', f.read(4))[0]
    RtChan2_CFDZeroCross = struct.unpack('i', f.read(4))[0]
    #Router Ch3
    RtChan3_InputType    = struct.unpack('i', f.read(4))[0]
    RtChan3_InputLevel   = struct.unpack('i', f.read(4))[0]
    RtChan3_InputEdge    = struct.unpack('i', f.read(4))[0]
    RtChan3_CFDPresent   = struct.unpack('i', f.read(4))[0]
    RtChan3_CFDLevel     = struct.unpack('i', f.read(4))[0]
    RtChan3_CFDZeroCross = struct.unpack('i', f.read(4))[0]
    #Router Ch4
    RtChan4_InputType    = struct.unpack('i', f.read(4))[0]
    RtChan4_InputLevel   = struct.unpack('i', f.read(4))[0]
    RtChan4_InputEdge    = struct.unpack('i', f.read(4))[0]
    RtChan4_CFDPresent   = struct.unpack('i', f.read(4))[0]
    RtChan4_CFDLevel     = struct.unpack('i', f.read(4))[0]
    RtChan4_CFDZeroCross = struct.unpack('i', f.read(4))[0]

    #The next is a T3 mode specific header.
    ExtDevices = struct.unpack('i', f.read(4))[0]

    Reserved1 = struct.unpack('i', f.read(4))[0]
    Reserved2 = struct.unpack('i', f.read(4))[0]
    CntRate0 = struct.unpack('i', f.read(4))[0]
    CntRate1 = struct.unpack('i', f.read(4))[0]

    StopAfter = struct.unpack('i', f.read(4))[0]
    StopReason = struct.unpack('i', f.read(4))[0]
    Records = struct.unpack('i', f.read(4))[0]
    ImgHdrSize =struct.unpack('i', f.read(4))[0]

    #Special Header for imaging.
    if ImgHdrSize > 0:
        ImgHdr = struct.unpack('i', f.read(ImgHdrSize))[0]
    ofltime = 0;

    cnt_1=0; cnt_2=0; cnt_3=0; cnt_4=0; cnt_Ofl=0; cnt_M=0; cnt_Err=0; # just counters
    WRAPAROUND=65536;

    #Put file Save info here.

    syncperiod = 1e9/CntRate0;
    #outfile stuff here.
    #fpout.
    #T3RecordArr = [];
    
    chanArr =np.zeros((Records,1));
    trueTimeArr =np.zeros((Records,1));
    dTimeArr=np.zeros((Records,1));
    #f1=open('./testfile', 'w+')
    for b in range(0,Records):
        T3Record = struct.unpack('I', f.read(4))[0];
        
        #T3RecordArr.append(T3Record)
        nsync = T3Record & 65535
        chan = ((T3Record >> 28) & 15);
        chanArr[b]=chan
        #f1.write(str(i)+" "+str(T3Record)+" "+str(nsync)+" "+str(chan)+" ")
        dtime = 0;
        
        if chan == 1:
            cnt_1 = cnt_1+1;dtime = ((T3Record >> 16) & 4095);#f1.write(str(dtime)+" ")
        elif chan == 2: 
            cnt_2 = cnt_2+1;dtime = ((T3Record >> 16) & 4095);#f1.write(str(dtime)+" ")
        elif chan == 3: 
            cnt_3 = cnt_3+1;dtime = ((T3Record >> 16) & 4095);#f1.write(str(dtime)+" ")
        elif chan == 4: 
            cnt_4 = cnt_4+1;dtime = ((T3Record >> 16) & 4095);#f1.write(str(dtime)+" ")
        elif chan == 15:
            markers = ((T3Record >> 16) & 15);
            
            if markers ==0:
                ofltime = ofltime +WRAPAROUND;
                cnt_Ofl = cnt_Ofl+1
                #f1.write("Ofl "+" ")
            else:
                cnt_M=cnt_M+1
                #f1.write("MA:%1u "+markers+" ")
            
        truensync = ofltime + nsync;
        truetime = (truensync * syncperiod) + (dtime*Resolution);
        trueTimeArr[b] = truetime
        dTimeArr[b] = dtime
        #f1.write(str(truensync)+" "+str(truetime)+"\n")
    f.close();
    #f1.close();
    
    
    return chanArr, trueTimeArr, dTimeArr, Resolution



def tttr2xfcs(y,num,NcascStart,NcascEnd, Nsub):
    """autocorr, autotime = tttr2xfcs(y,num,10,20)
     Translation into python of:
     Fast calculation of fluorescence correlation data with asynchronous time-correlated single-photon counting.
     Michael Wahl, Ingo Gregor, Matthias Patting, Jorg Enderlein
     """
 
    dt = np.max(y)-np.min(y)
    y = np.round(y[:],0)
    numshape = num.shape[0]
     
    autotime = np.zeros(((NcascEnd+1)*(Nsub+1),1));
    auto = np.zeros(((NcascEnd+1)*(Nsub+1), num.shape[1], num.shape[1])).astype(np.float64)
    shift = float(0)
    delta = float(1)
    
    
    
    for j in range(0,NcascEnd):
        
        #Finds the unique photon times and their indices. The division of 'y' by '2' each cycle makes this more likely.
        y,k1 = np.unique(y,1)
        #Sums up the photon times in each bin.
        cs =np.cumsum(num,0).T
        #Prepares difference array so starts with zero.
        diffArr1 = np.zeros(( k1.shape[0]+1));
        diffArr2 = np.zeros(( k1.shape[0]+1));
        #Takes the cumulative sum of the unique photon arrivals
        diffArr1[1:] = cs[0,k1].reshape(-1)
        diffArr2[1:] = cs[1,k1].reshape(-1)
        num =np.zeros((k1.shape[0],2))
        #Finds the total photons in each bin. and represents as count.
        #This is achieved because we have the indices of each unique time photon and cumulative total at each point.
        num[:,0] = np.diff(diffArr1)
        num[:,1] = np.diff(diffArr2)
        
        
        for k in range(0,Nsub):
            shift = shift + delta
            lag = np.round(shift/delta,0)
    
            
            #Allows the script to be sped up.
            if j >= NcascStart:
                

                #Old method
                #i1= np.in1d(y,y+lag,assume_unique=True)
                #i2= np.in1d(y+lag,y,assume_unique=True)
                
                #New method, cython
                i1,i2 = fib4.dividAndConquer(y, y+lag,y.shape[0])
                i1 = i1.astype(np.bool);
                i2 = i2.astype(np.bool);
                
                #Faster dot product method, faster than converting to matrix.
                auto[(k+(j)*Nsub),:,:] = np.dot(num[i1,:].T,num[i2,:])/delta    
            
            autotime[k+(j)*Nsub] =shift;
        y = np.ceil(np.array(0.5*y))
        delta = 2*delta
    
    for j in range(0, auto.shape[0]):
        auto[j,:,:] = auto[j,:,:]*dt/(dt-autotime[j])
    autotime = autotime/1000000
    return auto, autotime
