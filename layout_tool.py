#!/usr/bin/env python

import pcbnew
import csv
import re
import sys
import os

def MoveModules(x,y,refs, brd = None):
    if not brd:
        brd = pcbnew.GetBoard()
    for ref in refs:
        m = brd.FindModuleByReference(ref)
        if m:
            m.SetPosition(pcbnew.wxPointMM(x,y))
            x = x + m.GetBoundingBox().GetWidth()/1000000
    pcbnew.Refresh()
