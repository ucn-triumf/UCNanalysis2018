import ROOT
import sys
from array import array
import numpy
import math
import itertools
import UCN

#Background Li6: 2.16 +/- 0.03
#           He3: 0.0403 +/- 0.0017

# analyze storage time from list of runs
def ReadCycles(infile, experiments):
  countperiodP1 = 1
  countperiodP2 = 2
  countperiodP3 = 3
  countperiodP4 = 4
  countperiodP5 = 5
  monitorperiod = 0
  backgroundperiod = 0
  storageperiod = 0

 
  
  for ex in experiments:
    ex['start'] = []
    ex['beamcurrent'] = []
    ex['li6counts'] = []
    ex['li6countsfull'] = []
    ex['countduration'] = []
    ex['monitorcounts'] = []
    ex['monitorduration'] = []
    ex['monitorcounts2'] = []
    ex['monitorduration2'] = []
    ex['li6background'] = []
    ex['backgroundduration'] = []
    ex['storageduration'] = []
    ex['beamcurrent'] = []
    ex['mintemperature'] = []
    ex['maxtemperature'] = []
    ex['minvaporpressure'] = []
    ex['maxvaporpressure'] = []
    ex['SCMcurrent'] = []
    ex['he3rate'] = []
    ex['li6rate'] = []
    ex['cycle'] =[]
    ex['N0'] = [] 
    ex['N1'] = []
    ex['numN0cycles'] = []
    ex['numN1cycles'] = []
    ex['monitorN0ir'] = [] 
    ex['monitorN1ir'] = []
    ex['monitorN0ct'] = [] 
    ex['monitorN1ct'] = []

  for cycle in infile.cycledata:
    run = cycle.runnumber

    if not any(run in ex['runs'] for ex in experiments): # if there is no experiment using this cycle
      continue
    
    Li6 = cycle.countsLi6

    He3 = cycle.countsHe3
    d = cycle.durations

    # filter useless cycles
    if min(cycle.B1V_KSM_PREDCUR) < 0.1:
      print('SKIPPING cycle {0} in run {1} because beam dropped below 0.1uA ({2}uA)'.format(cycle.cyclenumber, cycle.runnumber, min(cycle.B1V_KSM_PREDCUR)))
      continue
    if numpy.std(cycle.B1V_KSM_PREDCUR) > 0.2:
      print('SKIPPING cycle {0} in run {1} because beam fluctuated by {2}uA'.format(cycle.cyclenumber, cycle.runnumber, numpy.std(cycle.B1V_KSM_PREDCUR)))
      continue
    if Li6[10] == 0:
      print('SKIPPING cycle {0} in run {1} because Li6 does not contain data in all periods'.format(cycle.cyclenumber, cycle.runnumber))
      continue
    if He3[monitorperiod] < 1000:
      print('SKIPPING cycle {0} in run {1} because He3 saw less than 1000 monitor counts ({2})'.format(cycle.cyclenumber, cycle.runnumber, He3[monitorperiod]))
      continue
    if d[backgroundperiod] > 0 and Li6[backgroundperiod]/d[backgroundperiod] > 10:
      print('SKIPPING cycle {0} in run {1} because of high Li6 background ({2}/s)'.format(cycle.cyclenumber, cycle.runnumber, Li6[backgroundperiod]/d[backgroundperiod]))
      continue
    
    for ex in experiments:
      if run not in ex['runs']:
        continue
    
      ex['cycle'].append(cycle.cyclenumber)
      ex['start'].append(cycle.start)
      ex['beamcurrent'].append([cur for cur in cycle.B1V_KSM_PREDCUR])
      ex['mintemperature'].append(min([min(getattr(cycle,'UCN_ISO_{0}_RDTEMP'.format(TS))) for TS in ['TS11', 'TS12', 'TS14']]))
      ex['maxtemperature'].append(max([max(getattr(cycle,'UCN_ISO_{0}_RDTEMP'.format(TS))) for TS in ['TS11', 'TS12', 'TS14']]))
      if max(cycle.UCN_ISO_PG9L_RDPRESS) >= 2.:
        ex['minvaporpressure'].append(min(cycle.UCN_ISO_PG9H_RDPRESS))
        ex['maxvaporpressure'].append(max(cycle.UCN_ISO_PG9H_RDPRESS))
      else:
        ex['minvaporpressure'].append(min(cycle.UCN_ISO_PG9L_RDPRESS))
        ex['maxvaporpressure'].append(max(cycle.UCN_ISO_PG9L_RDPRESS))
      ex['SCMcurrent'].append([v/250e-6 for v in cycle.SCMVoltages3])
      ex['li6counts'].append(Li6[countperiodP1]+Li6[countperiodP2]+Li6[countperiodP3]+Li6[countperiodP4])
      #print('li6counts are {0} for cycle {1}'.format(Li6[countperiodP1]+Li6[countperiodP2]+Li6[countperiodP3]+Li6[countperiodP4], cycle.cyclenumber))
      ex['countduration'].append(d[countperiodP1]+d[countperiodP2]+Li6[countperiodP3]+Li6[countperiodP4])
      ex['monitorcounts'].append(He3[monitorperiod])
      ex['monitorduration'].append(d[monitorperiod])
      ex['monitorcounts2'].append(He3[countperiodP1]+He3[countperiodP2]+He3[countperiodP3]+He3[countperiodP4])
      ex['monitorduration2'].append(d[countperiodP1]+d[countperiodP2]+Li6[countperiodP3]+Li6[countperiodP4])
      ex['li6background'].append(Li6[backgroundperiod])
      ex['backgroundduration'].append(d[backgroundperiod])
      ex['storageduration'].append(d[storageperiod])
      #print('Monitor Conuts is {0}').format(He3[monitorperiod],)
      print("Readcycles")
      li6rate = ROOT.TH1D('Le6_{0}_{1}'.format(cycle.runnumber, cycle.cyclenumber), 'Li6 detector rate', int(math.floor(sum(d))-d[monitorperiod]), d[monitorperiod], math.floor(sum(d)))

      if cycle.cyclenumber%2==0:
        ex['numN0cycles'].append(1)
      if cycle.cyclenumber%2==1:
        ex['numN1cycles'].append(1)

      for c in getattr(cycle, 'Li6/hits'):
        if cycle.cyclenumber%2==0 and c>60.:
          ex['N0'].append(c)
        if cycle.cyclenumber%2==1 and c>60.:
          ex['N1'].append(c)    
         
        if c>60.:
          li6rate.Fill(c)
      for c in getattr(cycle, 'He3/hits'):
        if c<60.:
          if cycle.cyclenumber%2==0:
            ex['monitorN0ir'].append(c)
          if cycle.cyclenumber%2==1:
            ex['monitorN1ir'].append(c)    
        else:
          if cycle.cyclenumber%2==0:
            ex['monitorN0ct'].append(c)
          if cycle.cyclenumber%2==1:
            ex['monitorN1ct'].append(c)    
  
      norm = 1./float(He3[monitorperiod])#li6rate.GetEntries()
      li6rate.Scale(norm)
      li6rate.GetXaxis().SetTitle('Time (s)')
      li6rate.GetYaxis().SetTitle('Li6 rate (s^{-1})')
      li6rate.SetDirectory(0)
      ex['li6rate'].append(li6rate)
	  
	  
# analyze storage time from list of runs
def PolarizationOvertime(ex):

  #Hardcoded background error
  bg1 =2.16 #n/s
  bge1 = 0.03


  print('\nAnalyzing TCN' + ex['TCN'])
  
  ex['li6backgroundrate'] = sum(ex['li6background'])/sum(ex['backgroundduration'])
  ex['li6backgroundrateerr'] = math.sqrt(sum(ex['li6background']))/sum(ex['backgroundduration'])
  print('Li6 detector background rate: {0} +/- {1} 1/s'.format(ex['li6backgroundrate'], ex['li6backgroundrateerr']))

  # report average monitor counts, range of beam current, range of He-II temperature
  monitoravg = numpy.average(ex['monitorcounts'], None, [1./m for m in ex['monitorcounts']], True)
  print 'Monitor counts: {0} +/- {1}'.format(monitoravg[0], 1./math.sqrt(monitoravg[1]))
  print('Beam current from {0} to {1} uA'.format(min(min(c) for c in ex['beamcurrent']), max(max(c) for c in ex['beamcurrent'])))

  #print 'Temperatures from {0} to {1} K'.format(min(ex['mintemperature']), max(ex['maxtemperature']))

  #seting up float variable arrays to plot
  x = [float(c) for c in ex['cycle']]
  xerr = [0. for cycle in ex['cycle']]

  y = [float(c) for c in ex['li6counts']]
  yerr = [math.sqrt(float(c)) for c in ex['li6counts']]
  
  # plot uncorrected ucn counts in Li6 det vs cycle
  graph = ROOT.TGraphErrors(len(x), numpy.array(x), numpy.array(y), numpy.array(xerr), numpy.array(yerr)) 

  graph.SetTitle('TCN{0} Li6 counts per cycle'.format(ex['TCN']))
  graph.GetXaxis().SetTitle('Cycle Number')
  graph.GetYaxis().SetTitle('UCN-count unnormalized')
   
  #create the canvas and print
  canvas = ROOT.TCanvas('c', 'c')
  graph.Draw('AP')
  pdf = 'TCN{0}.pdf'.format(ex['TCN'])
  canvas.Print(pdf + '(')

  y = []
  yerr = []
  # plot background-uncorrected UCN counts correlated with monitor detector
  for cl,ch in zip(ex['li6counts'],ex['monitorcounts']):
    y.append(float(cl)/float(ch))
    yerr.append(math.sqrt(float(cl)/float(ch)/float(ch)+float(cl)*float(cl)/float(ch)/float(ch)/float(ch)))

  graph = ROOT.TGraphErrors(len(x), numpy.array(x), numpy.array(y), numpy.array(xerr), numpy.array(yerr))
  graph.SetTitle('TCN{0} (UCN Ratio for monitor counts norm to Irradiation He3)'.format(ex['TCN']))
  graph.GetXaxis().SetTitle('Cycle Number')
  graph.GetYaxis().SetTitle('Li6 counts/He3 Counts')
  # do single exponential fit with background
  graph.Draw('AP')
  canvas.Print(pdf)

  for cl,ch in zip(ex['li6counts'],ex['monitorcounts2']):
    y.append(float(cl)/float(ch))
    
    Dcl = math.sqrt(cl+bge1*bge1*120*120)
    yerr.append(math.sqrt(float(Dcl)*float(Dcl)/float(ch)/float(ch)+float(cl)*float(cl)/float(ch)/float(ch)*float(ch)))

  graph = ROOT.TGraphErrors(len(x), numpy.array(x), numpy.array(y), numpy.array(xerr), numpy.array(yerr))
  graph.SetTitle('TCN{0} (UCN Ratio for monitor counts norm to count period He3)'.format(ex['TCN']))
  graph.GetXaxis().SetTitle('Cycle Number')
  graph.GetYaxis().SetTitle('Li6 counts/He3 Counts')
  # do single exponential fit with background
  graph.Draw('AP')
  canvas.Print(pdf)

  #bins = [60., 62., 64., 67., 70., 74., 80., 100., 180.]
  bins = [60., 62., 62.5, 63., 63.5, 64., 67., 70., 74., 80., 100., 180.]
  times1 = [2. , 0.5, 0.5,  0.5, 0.5,  3.,  3.,  4.,  6., 20.,   80.]
  # polA = [1., 0.650421187204, 0.650382003687, 0.617015405736, 0.657047099164, 
  #          0.60224505266, 0.586506092553, 0.617312444481, 0.60206302199, 
  #          0.60583140569, 0.644695711584]
  
  #polA = [0.671,0.646,0.646,0.613,0.653,0.598,0.582,0.612,0.595,0.590,0.524]#TCN18-180
  #poleA = [0.048,0.297,0.031,0.033,0.033,0.015,0.016,0.016,0.015,0.012,0.017]
  f = open('TCN18-180-v3-polarization.txt','r')
  polA180 = []
  polAe180 = []
  numbin = 11
  for line in f:
    columns = line.split()
    polA180.append(float(columns[0]))
    polAe180.append(float(columns[1]))

  li6n0graph = ROOT.TH1D("Li6_N0","Li N0 Detector Rate",numbin,array('d',bins))
  li6n0graph.GetXaxis().SetTitle('Time (s)')
  li6n0graph.GetYaxis().SetTitle('Li6 rate (s^{-1})')
  li6n0graph.SetDirectory(0)
  for c in ex['N0']:
    li6n0graph.Fill(c)
  li6n0graph.Sumw2()
  

  li6n1graph = ROOT.TH1D("Li6_N1","Li N1 Detector Rate",numbin,array('d',bins))
  li6n1graph.GetXaxis().SetTitle('Time (s)')
  li6n1graph.GetYaxis().SetTitle('Li6 rate (s^{-1})')
  li6n1graph.SetDirectory(0)
  for c in ex['N1']:
    li6n1graph.Fill(c)
  li6n1graph.Sumw2()
  # li6n1graph.Draw()
  # canvas.Print(pdf)

  subgraph = li6n0graph.Clone("sub")
  altgraph = li6n1graph.Clone("alt")
  subgraph.Add(altgraph,-1.)
  addgraph = li6n0graph.Clone("add")
  addgraph.Add(altgraph,1.)
  subgraph.Divide(addgraph)
  subgraph.SetTitle('Polarization Over Time p^2 = {n0 - n1}/{n0 +n1}')
  subgraph.GetYaxis().SetTitle('Polarization Power Squared p^{2}')
  subgraph.GetXaxis().SetTitle('Time (s)')
  #subgraph.Draw('e1')
  #canvas.Print(pdf)

  Plotted = ROOT.TH1D('Polarization Power of SCM','',numbin,array('d',bins))
  i=1
  for a in polA180:
    e = 1./2.*float(subgraph.GetBinError(i))
    
    p = (abs(subgraph.GetBinContent(i))/a)
    if a == 1.: 
      p=0.
      e=0.
    Plotted.SetBinContent(i,p)
    Plotted.SetBinError(i,e)
    i=i+1
  Plotted.GetXaxis().SetTitle('Time (s)')
  Plotted.GetYaxis().SetTitle('Polarization Power, p')
  Plotted.SetTitle('Polarization Power Over Time (unnormalized)')


  Plotted.Draw('e1')

  canvas.Print(pdf)



  
  He3N0 = 0. #? cycles
  He3N1 = 0. #? cycles


  for cycle,monitor in zip(ex['cycle'],ex['monitorcounts']):
    if cycle%2==0:
      He3N0 = He3N0 + float(monitor)
    if cycle%2==1:
      He3N1 = He3N1 + float(monitor)
    print("n0, n1 He counts  {0}, {1}".format(He3N0,He3N1) )
  

  # Gets cycle number to account for each cycles throughing out runs
  numrun1=sum(ex['numN1cycles'])
  numrun0=sum(ex['numN0cycles'])

  print('There are {0} cycles for N0 and {1} cycles for N1').format(numrun0, numrun1)
  f = open("TCN{0}-polarization.txt".format(ex['TCN']),"w+")
  i = 1 
  for t in times1:
    num = numrun0
    LI = li6n0graph.GetBinContent(i)
    Nc = LI - bg1*t*num
    ebg = bge1/num
    eNc = math.sqrt(math.sqrt(LI**2)+(ebg*t)**2)
    HEc = (He3N0/120)*t #scaling the counts to bin size
    eHEc = (math.sqrt(He3N0)/120)*t #scaling the error to bin size 
    Rc = Nc/HEc
    eRc = math.sqrt((eNc/HEc)*(eNc/HEc)+(eHEc*Nc/(HEc*HEc))*(eHEc*Nc/(HEc*HEc)))
    li6n0graph.SetBinContent(i, Rc)# fill histogram with Ratio counts 
    li6n0graph.SetBinError(i, eRc)# fill histogram with error in ratio counts

    num = numrun1 
    LI = li6n1graph.GetBinContent(i)
    Nc = LI - bg1*t*num
    ebg = bge1/num
    eNc = math.sqrt(math.sqrt(LI**2)+(ebg*t)**2)
    HEc = (He3N1/120)*t #scaling the counts to bin size
    eHEc = (math.sqrt(He3N1)/120)*t #scaling the error to bin size 
    Rc = Nc/HEc
    eRc = math.sqrt((eNc/HEc)*(eNc/HEc)+(eHEc*Nc/(HEc*HEc))*(eHEc*Nc/(HEc*HEc)))

    li6n1graph.SetBinContent(i, Rc)# fill histogram with Ratio counts 
    li6n1graph.SetBinError(i, eRc)# fill histogram with error in ratio counts
    
    R0 = li6n0graph.GetBinContent(i)
    eR0 = li6n0graph.GetBinError(i)
    R1 = li6n1graph.GetBinContent(i)
    eR1 = li6n1graph.GetBinError(i)

    numer = R0-R1 
    denom = R1+R0
    eGlobal2 = eR0*eR0+eR1+eR1
    A = numer/denom #polarization assymetery
    # A = p_SCM * p_foil
    eA=abs(A)*math.sqrt((eGlobal2)/(numer*numer)+(eGlobal2)/(denom*denom)) #total error propagation for A
    f.write("{0} {1}\n".format(A,eA))

    i=i+1
  f.close()
  print("***new values***")
  Plotted2 = ROOT.TH1D('Polarization Power','',numbin,array('d',bins))
  i=1

  for a in polA180:
    e = 0.
    p = ((li6n0graph.GetBinContent(i)-li6n1graph.GetBinContent(i))/(li6n0graph.GetBinContent(i)+li6n1graph.GetBinContent(i)))
    Plotted2.SetBinContent(i,p/a)
    if a==1.:
      Plotted2.SetBinContent(i,0.)
    Plotted2.SetBinError(i,e)
    print(p/a)
    i=i+1
  Plotted2.GetXaxis().SetTitle('Time (s)')
  Plotted2.GetYaxis().SetTitle('Polarization Power, p')
  Plotted2.SetTitle('Polarization Power Over Time')
  Plotted2.Draw()
  canvas.Print(pdf)



  li6n0g = ROOT.TH1D("Li6_N0_rate","Li N0 Detector Rate",120,60.,180.)
  li6n0g.GetXaxis().SetTitle('Time (s)')
  li6n0g.GetYaxis().SetTitle('Li6 rate (s^{-1})')
  li6n0graph.SetDirectory(0)
  for c in ex['N0']:
    li6n0g.Fill(c)
  li6n0g.Sumw2()
  li6n0g.Draw()
  #canvas.Print(pdf)
  li6n1g = ROOT.TH1D("Li6_N1_rate","Li N1 Detector Rate",120,60.,180.)
  li6n1g.GetXaxis().SetTitle('Time (s)')
  li6n1g.GetYaxis().SetTitle('Li6 rate (s^{-1})')
  li6n1graph.SetDirectory(0)
  for c in ex['N1']:
    li6n1g.Fill(c)
  li6n1g.Sumw2()
  li6n1g.Draw()
  #canvas.Print(pdf)

  ## Here we use the previos graphs and manipulate only the bins in interval of 1 second

  li6n0ge = ROOT.TH1D("Li6_N0_rate_e","Li N0 Detector Rate e",120,60.,180.)
  li6n0ge.GetXaxis().SetTitle('Time (s)')
  li6n0ge.GetYaxis().SetTitle('Li6 rate (s^{-1})')
  li6n0ge.SetDirectory(0)
  for b in range(120):
    li6n0ge.SetBinContent(b, li6n0g.GetBinContent(b)-bg1)
    li6n0ge.SetBinError(b, math.sqrt(li6n0g.GetBinContent(b)+bge1*bge1))
  li6n0ge.Draw()
  #canvas.Print(pdf)
  li6n1ge = ROOT.TH1D("Li6_N1_rate_e","Li N1 Detector Rate e",120,60.,180.)
  li6n1ge.GetXaxis().SetTitle('Time (s)')
  li6n1ge.GetYaxis().SetTitle('Li6 rate (s^{-1})')
  #li6n10ge.SetDirectory(0)
  for b in range(120):
    li6n1ge.SetBinContent(b, li6n1g.GetBinContent(b)-bg1)
    li6n1ge.SetBinError(b, math.sqrt(li6n1g.GetBinContent(b)+bge1*bge1))
  li6n1ge.Draw("same")
 

  He3I0g = ROOT.TH1D("He3_N0_irradiation_rate","He N0 Detector Rate irr",60,0.,60.)
  He3I0g.GetXaxis().SetTitle('Time (s)')
  He3I0g.GetYaxis().SetTitle('He3Det neutron rate (s^{-1})')
  He3I0g.SetDirectory(0)
  for c in ex['monitorN0ir']:
    He3I0g.Fill(c)
  He3I0g.Sumw2()
  He3I0g.Draw()
  #canvas.Print(pdf)
  He3I1g = ROOT.TH1D("He3_N10_irradiation_rate","He N1 Detector Rate irr",60,0.,60.)
  He3I1g.GetXaxis().SetTitle('Time (s)')
  He3I1g.GetYaxis().SetTitle('He3Det neutron rate (s^{-1})')
  #He3I1g.SetDirectory(0)
  for c in ex['monitorN1ir']:
    He3I1g.Fill(c)
  He3I1g.Sumw2()
  He3I1g.Draw("same")
  canvas.Print(pdf)

  He3C0g = ROOT.TH1D("He3_N0_count_period_rate","He N0 Detector Rate ct",120,60.,180.)
  He3C0g.GetXaxis().SetTitle('Time (s)')
  He3C0g.GetYaxis().SetTitle('He3Det neutron rate (s^{-1})')
  He3C0g.SetDirectory(0)
  for c in ex['monitorN0ct']:
    He3C0g.Fill(c)
  He3C0g.Sumw2()
  He3C0g.Draw()
  He3C1g = ROOT.TH1D("He3_N1_count_period_rate","He N1 Detector Rate ct",120,60.,180.)
  He3C1g.GetXaxis().SetTitle('Time (s)')
  He3C1g.GetYaxis().SetTitle('He3Det neutron rate (s^{-1})')
  #He3C1g.SetDirectory(0)
  for c in ex['monitorN1ct']:
    He3C1g.Fill(c)
  He3C1g.Sumw2()
  He3C1g.Draw("same")
  canvas.Print(pdf)

  RatioN0ge = ROOT.TH1D("Ratio_n0_rate_e","Detector Ratio e",120,60.,180.)
  RatioN0ge.GetXaxis().SetTitle('Time (s)')
  RatioN0ge.GetYaxis().SetTitle('Ration of UCN Counts Li6/He3')
  RatioN0ge.SetDirectory(0)
  for nbin in range(120):
    RatioN0ge.SetBinContent(nbin,li6n0ge.GetBinContent(nbin)/(He3I0g.Integral(0,120)/120))
    RatioN0ge.SetBinError(nbin, math.sqrt( (li6n0ge.GetBinError(nbin)/li6n0ge.GetBinContent(nbin))**2 + ((li6n0ge.GetBinContent(nbin))**2)/((He3I0g.Integral(0,120)/120)**3) ))
  RatioN0ge.Draw()
  RatioN1ge = ROOT.TH1D("Ratio_n1_rate_e","Detector Ratio n1 e",120,60.,180.)
  for nbin in range(120):
    RatioN1ge.SetBinContent(nbin,li6n1ge.GetBinContent(nbin)/(He3I1g.Integral(0,120)/120))
    RatioN1ge.SetBinError(nbin, math.sqrt( (li6n1ge.GetBinError(nbin)/li6n1ge.GetBinContent(nbin))**2 + ((li6n1ge.GetBinContent(nbin))**2)/((He3I1g.Integral(0,120)/120)**3) ))
  RatioN1ge.Draw('same')
  

  
  gPolNorm = ROOT.TH1D("Polarization n0 and n1","",120,60.,180.)
  gPolNorm.GetXaxis().SetTitle('time (s)')
  gPolNorm.GetYaxis().SetTitle('polarization')


  for nbin in range(120):
    numN0=RatioN0ge.GetBinContent(nbin)
    errN0=RatioN0ge.GetBinError(nbin)
    numN1=RatioN1ge.GetBinContent(nbin)
    errN1=RatioN1ge.GetBinError(nbin)


    if ((numN0-numN1)/(numN0+numN1))<0.:
      pol1 = -1*math.sqrt(abs((numN0-numN1)/(numN0+numN1)) )
    else: pol1 = math.sqrt(abs((numN0-numN1)/(numN0+numN1)) )
    pol1 = ((numN0-numN1)/(numN0+numN1)) 
    gPolNorm.SetBinContent(nbin, pol1)

  
  gPolNorm.SetDirectory(0)
  gPolNorm.Draw()
  canvas.Print(pdf+ ')')


  
#ROOT.gStyle.SetOptStat(1001111)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(1111)
ROOT.gROOT.SetBatch(1)
ROOT.gErrorIgnoreLevel = ROOT.kInfo + 1

# list runs for each experiment
experiments = [{'TCN': '18-070-0A'  , 'runs': [1033]},
               {'TCN': '18-070-50A' , 'runs': [1037]},
               {'TCN': '18-070-100A', 'runs': [1041]},
               {'TCN': '18-070-150A', 'runs': [1039]},
               {'TCN': '18-070-175A', 'runs': [1045]},
               {'TCN': '18-070-200A', 'runs': [1035]}]


#experiments = [{'TCN': '18-180', 'runs': [1029]}]


ReadCycles(ROOT.TFile(sys.argv[1]), experiments)
			  
# loop over experiments
for ex in experiments:
 PolarizationOvertime(ex)



