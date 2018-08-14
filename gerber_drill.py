'''
    A python script example to create plot files to build a board:
    Gerber files
    Drill files
    Map dril files
    This file is forked from "https://github.com/blairbonnett-mirrors/kicad/blob/master/demos/python_scripts_examples/gen_gerber_and_drill_files_board.py"
    Important note:
        this python script does not plot frame references (page layout).
        the reason is it is not yet possible from a python script because plotting
        plot frame references needs loading the corresponding page layout file
        (.wks file) or the default template.

        This info (the page layout template) is not stored in the board, and therefore
        not available.

        Do not try to change SetPlotFrameRef(False) to SetPlotFrameRef(true)
        the result is the pcbnew lib will crash if you try to plot
        the unknown frame references template.

        Anyway, in gerber and drill files the page layout is not plot
'''

import sys
import os
import re
import math

from pcbnew import *
def GenGerberDrill(board = None, split_G85 = 0.2, plotDir = "plot/"):
	if not board:
		board = GetBoard()

	pctl = PLOT_CONTROLLER(board)

	popt = pctl.GetPlotOptions()

	popt.SetOutputDirectory(plotDir)

	# Set some important plot options:
	popt.SetPlotFrameRef(False)     #do not change it
	popt.SetLineWidth(FromMM(0.35))

	popt.SetAutoScale(False)        #do not change it
	popt.SetScale(1)                #do not change it
	popt.SetMirror(False)
	popt.SetUseGerberAttributes(True)
	popt.SetUseGerberProtelExtensions(False)
	popt.SetExcludeEdgeLayer(False);
	popt.SetScale(1)
	popt.SetUseAuxOrigin(False)

	# This by gerbers only (also the name is truly horrid!)
	popt.SetSubtractMaskFromSilk(False)

	# Once the defaults are set it become pretty easy...
	# I have a Turing-complete programming language here: I'll use it...
	# param 0 is a string added to the file base name to identify the drawing
	# param 1 is the layer ID
	# param 2 is a comment
	plot_plan = [
		( "Top_Cu", F_Cu, "Top layer" ),
		( "Bottom_Cu", B_Cu, "Bottom layer" ),
		( "Bottom_Paste", B_Paste, "Paste Bottom" ),
		( "Top_Paste", F_Paste, "Paste top" ),
		( "Top_Silk", F_SilkS, "Silk top" ),
		( "Bottom_Silk", B_SilkS, "Silk top" ),
		( "Bottom_Mask", B_Mask, "Mask bottom" ),
		( "Top_Mask", F_Mask, "Mask top" ),
		( "EdgeCuts", Edge_Cuts, "Edges" ),
	]


	for layer_info in plot_plan:
		pctl.SetLayer(layer_info[1])
		pctl.OpenPlotfile(layer_info[0], PLOT_FORMAT_GERBER, layer_info[2])
		print 'plot %s' % pctl.GetPlotFileName()
		if pctl.PlotLayer() == False:
			print "plot error"

	#generate internal copper layers, if any
	lyrcnt = board.GetCopperLayerCount();

	for innerlyr in range ( 1, lyrcnt-1 ):
		pctl.SetLayer(innerlyr)
		lyrname = 'inner%s' % innerlyr
		pctl.OpenPlotfile(lyrname, PLOT_FORMAT_GERBER, "inner")
		print 'plot %s' % pctl.GetPlotFileName()
		if pctl.PlotLayer() == False:
			print "plot error"


	# At the end you have to close the last plot, otherwise you don't know when
	# the object will be recycled!
	pctl.ClosePlot()

	# Fabricators need drill files.
	# sometimes a drill map file is asked (for verification purpose)
	drlwriter = EXCELLON_WRITER( board )
	drlwriter.SetMapFileFormat( PLOT_FORMAT_PDF )

	mirror = False
	minimalHeader = False
	offset = wxPoint(0,0)
	# False to generate 2 separate drill files (one for plated holes, one for non plated holes)
	# True to generate only one drill file
	mergeNPTH = False
	drlwriter.SetOptions( mirror, minimalHeader, offset, mergeNPTH )

	metricFmt = True
	drlwriter.SetFormat( metricFmt )

	genDrl = True
	genMap = True
	print 'create drill and map files in %s' % pctl.GetPlotDirName()
	drlwriter.CreateDrillandMapFilesSet( pctl.GetPlotDirName(), genDrl, genMap );

	# One can create a text file to report drill statistics
	rptfn = pctl.GetPlotDirName() + 'drill_report.rpt'
	print 'report: %s' % rptfn
	drlwriter.GenDrillReportFile( rptfn );
	
	if split_G85:
		SplitG85InDrill(pctl.GetPlotDirName(), True, split_G85)
	return pctl.GetPlotDirName()

def FromGerberPosition(position_str):
	s1 = position_str.find('X')
	s2 = position_str.find('Y')
	if (s1 != -1) and (s2 != -1):
		x = float(position_str[s1+1:s2])
		y = float(position_str[s2+1:])
	return [x,y]

def same(p1,p2,diff = 0.0001):
	return (abs(p1[0]-p2[0])<diff) and (abs(p1[1]-p2[1])<diff)
	
def SplitG85(G85Data,step = 0.2):
	t = G85Data.split('G85')
	r = []
	if len(t) == 2:
		p1 = FromGerberPosition(t[0])
		p2 = FromGerberPosition(t[1])
		dx = p2[0] - p1[0]
		dy = p2[1] - p1[1]
		dist = sqrt(dx*dx+dy*dy)
		td = 0
		pt = [p1[0],p1[1]]
		count = 0
		while not same(pt,p2):
			r.append('X%sY%s\n' %(str(float('%.3f'%pt[0])),str(float('%.3f'%pt[1]))))
			pt[0] = pt[0] + step*dx/dist
			pt[1] = pt[1] + step*dy/dist
			if dist - td < (step*1.5):
				pt[0] = p2[0]
				pt[1] = p2[1]
			else:
				td = td + step
			count = count + 1
			if count > 50:
				break
		r.append('X%sY%s\n' %(str(float('%.3f'%pt[0])),str(float('%.3f'%pt[1]))))
		return r, True
	else:
		return [G85Data], False

def HoleSize(line):
	r = re.compile('(T[0-9]+)C([-0-9.]+)')
	m = r.match(line)
	if m:
		t = m.groups()
		return t[0], float(t[1])
	return None, None

def round(value, round = 0.1):
	if value < round:
		return round
	t = value / round
	t = math.ceil(t)
	return t * round

def SplitG85InDrill(drillPath, newfilename = True,step = 0.2):
	''' Split the G85 command to hole seqence in drill file
	'''
	files = [f for f in os.listdir(drillPath) if f.endswith('.drl')]
	for fn in files:
		infn = drillPath + fn
		outfn = infn
		if not fn.endswith('_no_slot.drl'):
			with open(infn, "r") as ins:
				outline = []
				skip_G05 = False
				holes = {}
				curHolesSize = None
				for line in ins:
					hn,hs = HoleSize(line)
					if hn and hs:
						holes[hn+'\n'] = hs
					if holes.has_key(line):
						curHolesSize = holes[line]
					step = 0.2
					if curHolesSize:
						step = round(curHolesSize/3)
					r, nextSkip = SplitG85(line, step)
					if skip_G05 and (r[0].find('G05') == 0):
						skip_G05 = False
					else:
						skip_G05 = nextSkip
						for l in r:
							outline.append(l)
				ins.close()
				if newfilename:
					outfn = infn.replace(".drl", "_no_slot.drl")
				fo = open(outfn, "w+")
				fo.writelines(outline)
				fo.close()
	
