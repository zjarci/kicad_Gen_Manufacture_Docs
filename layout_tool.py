#!/usr/bin/env python

import pcbnew
import csv
import re
import sys
import os

def MakeRefs(refs):
    '''
    Transform reference string 'R1-3,6-8,J1,2,5-7' 
       to string array ['R1','R2','R3','R6','R7','R8','J1','J2','J5','J6','J7']
    '''
    if type(refs) == list:
        return refs
    r = refs.upper().split(',')
    prefix = 'X'
    ref_list = []
    for s in r:
        m = re.match('([^0-9]+)',s)
        ts = s
        if m:
            prefix = m.group(0)
            ts = s[len(prefix):]
        ps = ts.find('-')
        if ps != -1:
            start_s = ts[:ps]
            end_s = ts[ps+1:]
            if (not start_s.isdigit()) or (not start_s.isdigit()):
                print 'Ref not Digital value'
            else:
                for i in range(int(start_s), int(end_s)+1):
                    ref_list.append(prefix+str(i))
        else:
            if not ts.isdigit():
                print 'Ref not Digital value'
            else:
                ref_list.append(prefix+ts)
    return ref_list

def MoveModules(x,y,refs, brd = None):
    if not brd:
        brd = pcbnew.GetBoard()
    for ref in MakeRefs(refs):
        m = brd.FindModuleByReference(ref)
        if m:
            m.SetPosition(pcbnew.wxPointMM(x,y))
            x = x + m.GetBoundingBox().GetWidth()/1000000
    pcbnew.Refresh()

def CopyModuleCourtyard(module, brd = None, layer = pcbnew.F_Paste):
    ''' Copy module courtyard to the destination layer
    '''
    if not brd:
        brd = pcbnew.GetBoard()
    poly = module.GetPolyCourtyardFront()
    dw = pcbnew.DRAWSEGMENT()
    dw.SetShape(pcbnew.S_POLYGON)
    dw.SetLayer(layer)
    dw.SetPolyShape(poly)
    brd.Add(dw)
    
def CopyCourtyard(refs = None, brd = None, layer = pcbnew.F_Paste):
    ''' Copy board modules courtyard to the destination layer
    '''
    if not brd:
        brd = pcbnew.GetBoard()
    if not refs:
        for m in brd.GetModules():
            if m.GetReference().find('J') == -1:
                CopyModuleCourtyard(m, brd, layer)
    else:
        for ref in MakeRefs(refs):
            m = brd.FindModuleByReference(ref)
            if m:
                CopyModuleCourtyard(m, brd, layer)
    pcbnew.Refresh()