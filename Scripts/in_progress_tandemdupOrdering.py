from __future__ import division
import re, sys, math, operator, copy,collections
import numpy as np 
from itertools import groupby

def ProcessCLI(args):
    pbi,scaf,plenD=readgff(args[1])
    htscd=createHTSC(args[2],pbi)
    htsc=[]
    #print plenD.keys()

    for s1 in htscd.keys():
        LL=[]
        for s2 in htscd[s1].keys():
       # for s2 in htscd['scaffold_0306'].keys():
            #LL+=[htscd[s1][s2]]
            #ll=htscd['scaffold_0306'][s2]
            ll=htscd[s1][s2]
            out=domainsplit_tandemdup_ohno(ll,args[3],plenD)[0]
#            print out 
            if len(out)>0:
                for k in out: # domainsplit_tandemdup_ohno(ll,args[3],plenD)[0]:
                    print k
            #return
       # htsc+=[LL]

def comp(t1,t2):
    c=0
    for t in t1:
        if t in t2:
            c+=1
    return c 
    
def readOutput(infile):
    d=collections.OrderedDict()
    pairs=[]
    filename = open(infile,"r")
    for line in filename:
        if len(line)>0:
            line=line.strip().split()

            if GtoT(line[0]) not in d.keys() and "." not in GtoT(line[0]):
                d[GtoT(line[0])]=GtoT(line[1])
                pairs.append((GtoT(line[0]),GtoT(line[1])))
    return pairs, d

def GtoT(pbid):
    pbid=list(pbid)
    if len(pbid)>5 and pbid[5]=='G':
        pbid[5]='T'
    return ''.join(pbid)



def getInt(pb):
    return [int(i) for i in re.split(r'(\d+)',pb) if len(i) >0 and i.isdigit()][0]

def getdup1(lst):
    d={}
    for key, value in lst:
        d[key] = d.get(key, []) + [value]
    
    for k in d:
        if len(d[k])==1:
            print k, ','.join(d[k])
        else:
            print 'dup:', k, '-->', ' '.join(d[k])
    #return pdup(d)

def mltl(htscList):
    mult0=set();mult1=set();doubles0=doubles1=[]
    for tup in htscList:
        if tup[0] not in doubles0:
            doubles0+=[tup[0]]
        else:
            mult0.add(tup[0])
        if tup[1] not in doubles1:                
            doubles1+=[tup[1]]
        else:
            mult1.add(tup[1])
    return  mult0, mult1

def doublesd(htscList,mult0,mult1):
    doublesD={}
    for tup in htscList:
        if tup[0] in mult0:
            if tup[0] not in doublesD.keys():
                doublesD[tup[0]]=set()
                doublesD[tup[0]].add(tup[1])
            else:
                doublesD[tup[0]].add(tup[1])
 
        if tup[1] in mult1:
            if tup[1] not in doublesD.keys():
                doublesD[tup[1]]=set()
                doublesD[tup[1]].add(tup[0])
            else:
                doublesD[tup[1]].add(tup[0])                
    return doublesD

def getmlt(doublesD,plenD,en_psl):
    bestmultL=[]; noscorebestmultL=[]; casesL=[]
    for k in doublesD.keys(): 
        klen=float(plenD[k])
        vlentot=0; verror=0
        for v in doublesD[k]:
            try:
                vlentot+=float(plenD[v])
            except KeyError:
                print v, 'not found in the gff file'
                verror=99
        if verror!=99:
            if klen/vlentot > 1.5:
                casesL+=[(k,doublesD[k],"tandem duplication")]
            else:
                casesL+=[(k,doublesD[k]),"domain split"]
        else:casesL+=[(k,doublesD[k]),"there was a problem. some hits were not found in the gff file that the user supplied"]

        with open(en_psl,'r') as psl:
            for line in psl:
                if line[2] in doublesD[k]:
                    print "that was NOT THE PROBLEM AFTER ALL"
                if ((line[0] == k and line[2] in doublesD[k]) or (line[0] in doublesD[k] and line[2]==k)) and line[1]!=line[3]:
                    bestmultL.append(tuple(line[0],line[2],(float(line[-3]),float(line[-2]))))#we now have a tuple with the ohnologan, & its bitscore&ev
                    noscorebestmultL.append((line[0],line[2]))
            print  'best mult',bestmultL
    return bestmultL, noscorebestmultL, casesL

def domainsplit_tandemdup_ohno(htscList,en_psl,plenD):
    bestmultL=[]; noscorebestmultL=[]; casesL=[]; doublesD=dict()
    doubles0=[]; doubles1=[]; mult=set();
    mult0,mult1=mltl(htscList)
    #print len(mult0),len(mult1) 
    if len(mult0)>0 or len(mult1)>0:
        print len(mult0),len(mult1)
        print getmlt(doublesd(htscList,mult0,mult1),plenD,en_psl)
        bestmultL,noscorebestmultL,casesL=getmlt(doublesd(htscList,mult0,mult1),plenD,en_psl)
    #else: print 'Nothing here'
    return bestmultL, noscorebestmultL, casesL

def remove_ds_td_extras(htscList, bmL):#see comments above
    singly=htscList.copy()
    for htsc in singly:
        doubles0=[]; doubles1=[]; mult=set(); mult0=set(); mult1=set()
        for tup in htsc:
            if tup[0] not in doubles0:
                doubles0+=[tup[0]]
            else:
                mult0.add(tup[0]); mult.add(tup[0])
            if tup[1] not in doubles1:
                doubles1+=[tup[1]]
            else:
                mult1.add(tup[1]);mult.add(tup[1])
        for tup in htsc:
            for p in tup:
                if p in mult0 or p in mult1:
                    if tup or (tup[1],tup[0]) in bmL:
                        continue
                    else:
                        htsc.remove(tup)
    return singly
    
def fillht(htscL, en_pslout_file,pbi):
    '''now Roy must make copy of htscL and add the filled holes directly to it'''
    holesList=[];l2hL=[];l2thhL=[];twohitsholesList=[]
    hole1way=[];alltg=[]
    newhtscList=[q for q in htscL]
    for LT in newhtscList:
        for htsc in LT:
            b=len(htsc) 
            print 'input htsc-->',len(htsc),sorted(htsc,key=lambda tup:tup[0])
            htsc=sorted(htsc,key=lambda tup:tup[0])
            newhits=set()
            if len(htsc)>2:
                for i in range(1,len(htsc)-1):
                    if getInt(htsc[i-1][0])< getInt(htsc[i][0]) and getInt(htsc[i][0])< getInt(htsc[i+1][0]):
                        if getInt(htsc[i-1][1])< getInt(htsc[i][1]) and getInt(htsc[i][1])< getInt(htsc[i+1][1]):
                            if getInt(htsc[i-1][0])<(getInt(htsc[i][0])-1) and getInt(htsc[i-1][1])<(getInt(htsc[i][1])-1):
                                indivcol1=set(range(getInt(htsc[i-1][0])+1,getInt(htsc[i][0])))
                                indivcol2=set(range(getInt(htsc[i-1][1])+1,getInt(htsc[i][1])))
                                mycol=indivcol1.union(indivcol2)
                                dummy=[]
                                with open(en_pslout_file,'r') as en_pslout:
                                    for line in en_pslout:
                                        line=line.rstrip().split()
                                        if getInt(line[0]) in indivcol1 and getInt(line[2]) in indivcol2 and pbi[line[0]]!=pbi[line[2]]:
                                            dummy.append((line[0],line[2],(float(line[-3]),float(line[-2]))))
                                dummy_s=sorted(dummy,key=lambda tup:(tup[2][0]),reverse=True)
                                allowed=set()
                                kill_it=[]
                                for tup in dummy_s:
                                    if tup[0] not in allowed or tup[1] not in allowed:
                                        allowed.add(tup[0]);allowed.add(tup[1])
                                    else:
                                        kill_it.append(tup)
                                for tupk in kill_it:
                                    dummy_s.remove(tupk)
                                length2=[(trip[0],trip[1]) for trip in dummy_s]
                                for trip in length2:
                                    newhits.add((trip[0],trip[1]))
                                '''for trip in dummy_top:
                                    length2.append((trip[0],trip[1]))'''
                                l2hL+=[length2]
                                holesList+=[dummy_s]
                        
                        elif getInt(htsc[i-1][1])> getInt(htsc[i][1]) and getInt(htsc[i][1])> getInt(htsc[i+1][1]):#case: scafs in reverse order
                            if getInt(htsc[i-1][0])<(getInt(htsc[i][0])-1) and getInt(htsc[i-1][1])>(getInt(htsc[i][1])+1):#if there is a hole on BOTH scafs
                                indivcol1=set(range(getInt(htsc[i-1][0])+1,getInt(htsc[i][0])))
                                indivcol2=set(range(getInt(htsc[i-1][1])-1,getInt(htsc[i][1]),-1))
                                mycol=indivcol1.union(indivcol2)
                                dummy=[]
                                #print 'S1 holes -->', indivcol1
                                #print 'S2 holes -->', indivcol2
                                with open(en_pslout_file,'r') as en_pslout:
                                    for line in en_pslout:
                                        line=line.rstrip().split()
#                                        print getInt(line[0]),getInt(line[1]), pbi[line[0]],pbi[line[1]]
                                        if getInt(line[0]) in list(indivcol1) and getInt(line[2]) in list(indivcol2) and pbi[line[0]]!=pbi[line[2]]:
                                 #           print line[0],line[1],float(line[-3]),float(line[-2])
                                            dummy.append((line[0],line[2],(float(line[-3]),float(line[-2]))))#we now have a tuple with the ohnologan, & its bitscore&ev
                                dummy_s=sorted(dummy,key=lambda tup:(tup[2][0]),reverse=True)
                                allowed=set()
                                kill_it=[]
                                #print 'dummy:', dummy
                                #print 'dummy_s: ',dummy_s

                                for tup in dummy_s:
                                    if tup[0] not in allowed or tup[1] not in allowed:
                                        allowed.add(tup[0]);allowed.add(tup[1])
                                    else:
                                        kill_it.append(tup)
                                for tupk in kill_it:
                                    dummy_s.remove(tupk)
                                #dummy_top=dummy_s[0:(max(len(indivcol1),len(indivcol2))+1)]
                                length2=[(trip[0],trip[1]) for trip in dummy_s]
                                for trip in length2:
                                    newhits.add((trip[0],trip[1]))
                                l2hL+=[length2]
                                holesList+=[dummy_s]
                                
            elif len(htsc)==2:
                for i in range(1,2):
                    if getInt(htsc[i-1][0])< getInt(htsc[i][0]):
                        if getInt(htsc[i-1][1])< getInt(htsc[i][1]):
                            if getInt(htsc[i-1][0])<(getInt(htsc[i][0])-1) and getInt(htsc[i-1][1])<(getInt(htsc[i][1])-1):
                                indivcol1=set(range(getInt(htsc[i-1][0])+1,getInt(htsc[i][0])))
                                indivcol2=set(range(getInt(htsc[i-1][1])+1,getInt(htsc[i][1])))
                                mycol=indivcol1.union(indivcol2)
                                dummy=[]
                                with open(en_pslout_file,'r') as en_pslout:
                                    for line in en_pslout:
                                        line=line.rstrip().split()
                                        if getInt(line[0]) in indivcol1 and getInt(line[2]) in indivcol2 and pbi[line[0]]!=pbi[line[2]]:
                                            dummy.append((line[0],line[2],(float(line[-3]),float(line[-2]))))
                                dummy_s=sorted(dummy,key=lambda tup:(tup[2][0]),reverse=True)
                                allowed=set()
                                kill_it=[]
                                for tup in dummy_s:
                                    if tup[0] not in allowed or tup[1] not in allowed:
                                        allowed.add(tup[0]);allowed.add(tup[1])
                                    else:
                                        kill_it.append(tup)
                                for tupk in kill_it:
                                    dummy_s.remove(tupk)
                                
                                length2=[(trip[0],trip[1]) for trip in dummy_s]
                                for trip in length2:
                                    newhits.add((trip[0],trip[1]))
                                l2thhL+=[length2]
                                twohitsholesList+=[dummy_s]
                        
                        elif getInt(htsc[i-1][1])> getInt(htsc[i][1]):
                            if getInt(htsc[i-1][0])<(getInt(htsc[i][0])-1) and getInt(htsc[i-1][1])>(getInt(htsc[i][1])+1):
                                indivcol1=set(range(getInt(htsc[i-1][0])+1,getInt(htsc[i][0])))
                                indivcol2=set(range(getInt(htsc[i-1][1])-1,getInt(htsc[i][1]),-1))
                                mycol=indivcol1.union(indivcol2)
                                dummy=[]
                                with open(en_pslout_file,'r') as en_pslout:
                                    for line in en_pslout:
                                        line=line.rstrip().split()
                                        if getInt(line[0]) in indivcol1 and getInt(line[2]) in indivcol2 and pbi[line[0]]!=pbi[line[2]]:
                                            dummy.append((line[0],line[2],(float(line[-3]),float(line[-2]))))
                                dummy_s=sorted(dummy,key=lambda tup:(tup[2][0]),reverse=True)
                                allowed=set()
                                kill_it=[]
                                for tup in dummy_s:
                                    if tup[0] not in allowed or tup[1] not in allowed:
                                        allowed.add(tup[0]);allowed.add(tup[1])
                                    else:
                                        kill_it.append(tup)
                                for tupk in kill_it:
                                    dummy_s.remove(tupk)
                                length2=[(trip[0],trip[1]) for trip in dummy_s]
                                for trip in length2:
                                    newhits.add((trip[0],trip[1]))
                                l2thhL+=[length2]
                                twohitsholesList+=[dummy_s] 
            for t in newhits:
                htsc+=[t]
                b+=1 ## update WGDone ie the number of new added htscs
            htsc=sorted(htsc,key=lambda tup: (tup[0]))
            #print len(htsc)
            alltg+=htsc
            print 'output htsc-->',len(htsc), htsc
        alltg=sorted(alltg,key=lambda tup:(tup[0]))
    return alltg #holesList, l2hL, twohitsholesList, l2thhL,newhtscList

def printht(htsc):
    md=[]
    ml=[]
    if len(htsc)>2:                                                                        
        for i in range(1,len(htsc)-1):
            if getInt(htsc[i-1][0])< getInt(htsc[i][0]) and getInt(htsc[i][0])< getInt(htsc[i+1][0]):
                if getInt(htsc[i-1][1])< getInt(htsc[i][1]) and getInt(htsc[i][1])< getInt(htsc[i+1][1]):
                    if i==1:
                        ml+=[htsc[i-1],htsc[i],htsc[i+1]]
                    elif i>1:
                        ml+=[htsc[i+1]]
                elif getInt(htsc[i-1][1])> getInt(htsc[i][1]) and getInt(htsc[i][1])> getInt(htsc[i+1][1]):
                    if i==1:
                        ml+=[htsc[i-1],htsc[i],htsc[i+1]]
                    elif i>1:
                        ml+=[htsc[i+1]]
                else:
                    print 'failed:', htsc[i]
        print ml
    elif len(htsc)==2:                                                                             
        if getInt(htsc[0][0])< getInt(htsc[1][0]):
            if getInt(htsc[0][1])> getInt(htsc[1][1]):
                md+=[htsc[0]]
                md+=[htsc[1]]
            elif getInt(htsc[0][1])<getInt(htsc[1][1]):
                md+=[htsc[0]]
                md+=[htsc[1]]
        print md 
    else:
        print 'single : ', htsc 


def getdup2(lst):
    d={}
    dd={}
    for key, value in lst:
        d[value] = d.get(value, []) + [key]
    for k in d.keys():
        if len(d[k])==1:
            print ','.join(d[k]), k
        else:
            print 'dup: ',','.join( d[k]),"-->", k
def getdupboth(lst):
    d1={}
    d2={}
    
    for k,v in lst:
        if k in d1:
            d1[k]+=[v]
        else:
            d1[k]=[v]
        if v in d2 :
            d2[v]+=[k]
        else:
            d2[v]+=[k]
    for k1 in d1:
        print k1,':',d1[k1]
    for k2 in d2:
        #if len(d2[k2])==1:
        print d2[k2],':',k2
        
def pdup(d):
    for k in d:
        if len(d[k])==1:
            print (k,d[k])
        else:
            print 'dup:',(k,d[k])
def prTp(lst):
    for k in lst:
        print k[0],k[1]

def getCts(lst):
    recip=[]
    recipC=0
    oneway=[]
    onewayC=0
    clst=copy.copy(lst)
    recip_seen=[]
    for (k,v) in clst:
        if (v,k) in clst:
            if (v,k) not in recip_seen:
                recip_seen.append((k,v))
                recip_seen.append((v,k))
                recipC+=1
        elif (v,k) not in clst:
            oneway.append((k,v))
            onewayC+=1 
#    print 'Reciprocal hits : ', len(recip_seen),recipC 
#    print 'One way Hits : ', len(oneway), onewayC

def getDistrib(lst,diPL):
    d=[]
    seen=[]
    for k,v in lst:
        if (v,k) not in seen:
            
            t=float(diPL[k]) / float(diPL[v])
            if t > 1.0:
                t=1/t
            d.append(t)
            seen.append((k,v))
    return d            
#Read in and update the psl output and find hits
def readpsl(pslout,pbidict):
    print 'Now creating the enriched psl output'
    bhits=[]
    hits=collections.OrderedDict()
    phits=collections.OrderedDict()
    scaffolds={}
    Lengthprot={}
    ps=collections.OrderedDict()
    with open(pslout,'r') as file:
        for line in file:
            line=line.rstrip().split()
            ov=max([ int(i) for i in re.split(r'(\d+)',line[-1]) if len(i)>0 and i.isdigit()])
            if float(line[4])>40.0 and ov/min(float(line[5]),float(line[6]))>=0.12:
                if line[0]!=line[2]:
                    if line[1] not in hits.keys():
                        hits[line[1]]=[line[3]]
                    else:
                        hits[line[1]].append(line[3])
                    if line[0] not in phits.keys():
                        phits[line[0]]={line[2]:line[-2]}
                    else:
                        phits[line[0]][line[2]]=line[-2]
                    if line[1] not in scaffolds.keys():
                        scaffolds[line[1]]=[line[0]]
                    else:
                        scaffolds[line[1]].append(line[0])
                    if line[3] not in scaffolds.keys():
                        scaffolds[line[3]]=[line[2]]
                    else:
                        scaffolds[line[3]].append(line[2])
                    if line[1]  in ps: 
                        if line[3] in ps[line[1]].keys():
                            ps[line[1]][line[3]]+=[(line[0],line[2],line[-2])]
                        else:
                            ps[line[1]][line[3]]=[(line[0],line[2],line[-2])]
                    else:
                        ps[line[1]]={}
                        ps[line[1]][line[3]]=[(line[0],line[2],line[-2])]
                    if line[0] not in Lengthprot:
                        Lengthprot[line[0]]=int(line[5])
                    if line[2] not in Lengthprot:
                        Lengthprot[line[2]]=int(line[6])
    for key in hits:
        kval=collections.Counter(hits[key])
        hits[key]=dict([a,-math.log(float(x)/sum(kval.values()))] for a, x in kval.iteritems())
    for k1 in hits: 
        for k2 in hits[k1]:
            score1=0
            score2=0
            try:
                score1=hits[k1][k2]
                
            except:
                score1=10
            try:
                score2=hits[k2][k1]
            except:
                score2=10
            score=score1+score2
            bhits.append((k1,k2,score))
    ghits=collections.OrderedDict()
    for p1 in phits.keys():
        minval=min([float(phits[p1][p2]) for p2 in phits[p1].keys()])
         
        uplimit=float(minval*10**10)
        check=0
        for p2 in phits[p1]:
            if float(phits[p1][p2]) <=uplimit:
                if p1 not in  ghits.keys():
                    ghits[p1]={}
                    ghits[p1][p2]=float(phits[p1][p2])
                else:
                    ghits[p1][p2]=float(phits[p1][p2])
            if float(phits[p1][p2])==minval and check==0:
                print p1,p2
                check=1
    betterHits=collections.OrderedDict()
    pairs=[]
    return 
    for g in ghits.keys():
        score=15.0
        bh=None
        if pbidict[g] not in betterHits.keys():
            betterHits[pbidict[g]]={}
#        print 'P1: ', g
        for g2 in ghits[g].keys():
#            print 'P2',g2, ghits[g][g2],hits[pbidict[g]][pbidict[g2]]
            if hits[pbidict[g]][pbidict[g2]]<score:
                bh=g2
                score=hits[pbidict[g]][pbidict[g2]]
        pairs.append((g,bh))
        if pbidict[bh] not in betterHits[pbidict[g]].keys():
            betterHits[pbidict[g]][pbidict[bh]]=[(g,bh)]
        else:
            betterHits[pbidict[g]][pbidict[bh]].append((g,bh))
    getCts(pairs)
   # print getDistrib(pairs,Lengthprot) 
    for k in betterHits.keys():
        for g in betterHits[k].keys():
            htsc=sorted(betterHits[k][g],key=lambda tup: (tup[0]))
            gh=[]

## get scaffolds dictionary
def readScaf(psl):
    scaffolds={}
    filename=open(psl,"r")
    for line in filename:
        line=line.rstrip().split()
        if line[1] in scaffolds and line[3] in scaffolds[line[1]]:
            scaffolds[line[1]][line[3]]+=[(line[0],line[2],line[-2])]
        else:
            scaffolds[line[1]]={line[3]:[(line[0],line[2],line[-2])]}


## create htsc from best hits ouput
def createHTSC(bihits,pbidict):
    print 'Now creating htsc ...'
    sca_sca_hits=collections.OrderedDict()
    with open(bihits,'r')as file:
        for line in file:
            line=line.rstrip().split()
            if pbidict[line[0]] not in sca_sca_hits.keys():
                sca_sca_hits[pbidict[line[0]]]=collections.OrderedDict()
                if pbidict[line[1]] not in sca_sca_hits[pbidict[line[0]]].keys(): 
                    sca_sca_hits[pbidict[line[0]]][pbidict[line[1]]]=[(line[0],line[1])]
                else: 
                    sca_sca_hits[pbidict[line[0]]][pbidict[line[1]]].append((line[0],line[1]))
            else:
                if pbidict[line[1]] not in sca_sca_hits[pbidict[line[0]]].keys():
                    sca_sca_hits[pbidict[line[0]]][pbidict[line[1]]]=[(line[0],line[1])]
                else:
                    sca_sca_hits[pbidict[line[0]]][pbidict[line[1]]].append((line[0],line[1]))
    return sca_sca_hits

#Read he gff3 files and create a dictionary: scaffolds: list of proteins                                   
def readgff(f):
    print 'Reading the gff3 file ...'
    filename = open(f, "r")
    scaffolds=collections.OrderedDict()
    pbi=collections.OrderedDict()
    plenD=collections.OrderedDict()
    for line in filename:
        line=line.strip().split()
        
        if line[0][:8]=='scaffold' and line[2]=='mRNA':
            #pt=re.split(r'[=;\s]',line[8])[1]
            pbi[re.split(r'[=;\s]',line[8])[1]]=line[0]
            plenD[re.split(r'[=;\s]',line[8])[1]]=int(line[4])-int(line[3])+1
        if line[0] not in scaffolds.keys():
            scaffolds[line[0]]=[re.split(r'[=;\s]',line[8])[1]]
        else:
            scaffolds[line[0]].append(re.split(r'[=;\s]',line[8])[1])
    for k in scaffolds.keys():
        scaffolds[k]=sorted(scaffolds[k])
            
    return pbi,scaffolds,plenD  
 
if __name__ == '__main__':
    ProcessCLI(sys.argv)
