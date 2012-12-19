#!/usr/bin/python
import sys
import random
import time
import os.path


def lineCount(infileName=None):
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	i = -1
	for i, l in enumerate(infile):
		pass
	if (infileName is not None):
		infile.close()
	return i + 1

def sampleLines(n, infileName=None, outfileName=None, header=False):
	'''grab n random lines from a text file'''

	sys.stderr.write("counting lines\n")
	lc = lineCount(infileName)
	sys.stderr.write("sampling %d/%d indices\n" % (n, lc))
	if (header):
		keepIdxs = [0] + sorted(random.sample(xrange(1, lc), n))
	else:
		keepIdxs = sorted(random.sample(xrange(lc), n))
	
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	wroteCount = 0
	for i, line in enumerate(infile):
		if (i % 100000 == 0):
			sys.stderr.write("\t%d\n" % i)
		if (i == keepIdxs[0]):
			outfile.write(line)
			wroteCount += 1
			keepIdxs.pop(0)
			if (len(keepIdxs) == 0):
				break
	if (infileName is not None):
		infile.close()
	if (outfileName is not None):
		outfile.close()
	return wroteCount

def chunkFile(chunkSize, infileName=None, lineFunc=None, header=False):
	if (infileName is None):
		infile = sys.stdin
		outfileNamePrefix = "chunk_"
		outfileNameSuffix = ".txt"	
	else:
		infile = open(infileName, 'r')
		root, ext = os.path.splitext(infileName)
		outfileNamePrefix = root + "_"
		outfileNameSuffix = ext	

	headLine = infile.readline() if (header) else ""

	currLine = infile.readline()	
	currLineCount = chunkSize
	nextChunk = 0
	outfileNames = []
	while (currLine != ""):
		if (currLineCount >= chunkSize):
			outfileName = outfileNamePrefix + str(nextChunk) + outfileNameSuffix
			outfileNames.append(outfileName)
			sys.stderr.write("writing %d lines to file '%s'\n" % (chunkSize, outfileName))
			outfile = open(outfileName, 'w')
			outfile.write(headLine)
			currLineCount = 0			
			nextChunk += 1
		
		currLineCount += 1
		outfile.write(currLine if (lineFunc is None) else lineFunc(currLine))
		currLine = infile.readline()

	return outfileNames	
		



def getColumn(col, infileName=None, outfileName=None, delim='\t', append=False):
	#sys.stderr.write(str(infileName) + " -> " + str(outfileName) + "\n")
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'a' if (append) else 'w')
	lineCount = 0	
	for line in infile:
		lineCount += 1
		if (lineCount % 500000 == 0):
			sys.stderr.write("\t%d\n" % lineCount)
		outfile.write(line[:-1].split(delim)[col] + "\n")
	return lineCount

def getColumnM(col, infileNames, outfileName, delim='\t'):
	#sys.stderr.write(str(infileNames) + " -> " + str(outfileName) + "\n")
	lineCount = 0
	for i, infileName in enumerate(infileNames):
		sys.stderr.write("%d/%d %s:\n" % (i, len(infileNames) - 1, infileName))
		lineCount += getColumn(col, infileName, outfileName, delim, append=True)
		sys.stderr.write("\n")
	return lineCount

def addColumn(val, infileName=None, outfileName=None, idx=None, delim='\t'):
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')
	if (idx is None):
		suff = delim + val + "\n"
		for line in infile:
			outfile.write(line[:-1] + suff)
	else:
		for line in infile:
			elts = line[:-1].split(delim)
			elts.insert(idx, val)
			outfile.write(delim.join(elts) + "\n")



def filterGt(field, const, infileName=None, outfileName=None, header=True, delim='\t', append=False):
	return filterFile(lambda r: float(r[field])>const, infileName, outfileName, header, delim, append)
def filterLt(field, const, infileName=None, outfileName=None, header=True, delim='\t', append=False):
	return filterFile(lambda r: float(r[field])<const, infileName, outfileName, header, delim, append)
def filterIn(field, goodVals, infileName=None, outfileName=None, header=True, delim='\t', append=False):
	return filterFile(lambda r: r[field] in set(goodVals), infileName, outfileName, header, delim, append)

def filterFile(rowfunc, infileName=None, outfileName=None, header=True, delim='\t', append=False):
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'a' if (append) else 'w')

	if (header):
		line = infile.readline()
		fieldNames = line.rstrip("\n").split(delim)
		outfile.write(line)

	lineCount = 0
	for line in infile:
		fields = line.rstrip("\n").split(delim)
		if (header):
			rowData = dict([ (n, v) for n, v in zip(fieldNames, fields) ])
		else:
			rowData = fields
				
		if (rowfunc(rowData)):
			outfile.write(line)		
			lineCount += 1
	return lineCount




def addTransformColumn(searchCol, tags, outCol, infileName=None, outfileName=None, header=True, idx=None, delim='\t'):
	'''add a col with the first key in the list to be found in search col, ignoring case'''	
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')

	if (header):
		headElts = infile.readline()[:-1].split(delim)
		searchColIdx = headElts.index(searchCol)
		if (idx is None):
			headElts.append(outCol)
		else:
			headElts.insert(idx, outCol)
		outfile.write(delim.join(headElts) + "\n")
	else:
		searchColIdx = searchCol

	def firstFound(s, keys, default=None):
		for key in keys:
			if (s.find(key) > -1):
				return key
		return default

	tags = [ t.lower() for t in tags ]
	tag_count = {}
	for line in infile:
		elts = line[:-1].split(delim)
		valLong = elts[searchColIdx].lower()
		if (valLong):
			valShort = firstFound(valLong, tags, "<other>")
		else:
			valShort = ""
		tag_count[valShort] = tag_count.get(valShort, 0) + 1

		if (idx is None):
			elts.append(valShort)
		else:
			elts.insert(idx, valShort)
		outfile.write(delim.join(elts) + "\n")

	for tag, count in tag_count.items():
		sys.stderr.write("\t%s\t%d\n" % (tag, count))	

def cleanChars(chars, infileName=None, outfileName=None):
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')
	for line in infile:
		outfile.write(line.translate(None, chars))
	
def cleanCols(numCols, infileName=None, outfileName=None, delim="\t"):
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')
	delimCountGood = numCols - 1
	line = infile.readline()	
	readCount = 1
	writeCount = 0
	while (line):
		delimCount = line.count(delim)
		if (delimCount == delimCountGood):
			outfile.write(line)
			writeCount += 1
		else:
			if (delimCount < delimCountGood): # we got a short line
				lineNext = ""
				while (line.count(delim) < delimCountGood):
					lineNext = infile.readline()
					readCount += 1
					line = line[:-1] + lineNext
				if (line.count(delim) == delimCountGood): # the composite line is now good
					outfile.write(line)
					writeCount += 1
				elif (lineNext.count(delim) == delimCountGood):
					outfile.write(lineNext)
					writeCount += 1
				# else: scrap them all
		line = infile.readline()
		readCount += 1
	sys.stderr.write("read %d lines, wrote %d lines\n" % (readCount, writeCount))
				

def joinFiles(fn1, fn2, fnOut, key1, key2, outer=False, header=True, delim="\t"):
	f1 = open(fn1, 'r')
	f2 = open(fn2, 'r')
	fOut = open(fnOut, 'w')

	if (header):
		elts1 = f1.readline().rstrip("\n").split(delim)
		elts2 = f2.readline().rstrip("\n").split(delim)
		keyIdx1 = elts1.index(key1)
		keyIdx2 = elts2.index(key2)
		fields = [ e + "1" for e in elts1 ] + [ e + "2" for e in elts2 ]
		fOut.write(delim.join(fields) + "\n")
	else:
		keyIdx1 = key1
		keyIdx2 = key2

	# store all the lines from file 2 in memory
	lines2 = {} # key -> line	
	for line2 in f2:
		elts = line2.rstrip("\n").split(delim) 
		key = elts[keyIdx2]
		lines2[key] = line2
		fieldCount2 = len(elts) # awful, gets set every time
	blank2 = delim*(fieldCount2 - 1) + "\n"


	# now go through file 1 and attach them
	countLine1 = 0
	countWrote = 0
	for line1 in f1:
		countLine1 += 1
		elts = line1.rstrip("\n").split(delim) 			
		key = elts[keyIdx1]
		fieldCount1 = len(elts) # awful, gets set every time
		if (key in lines2):
			line2 = lines2[key]
			del lines2[key]
		else:
			if (outer):
				line2 = blank2
			else:
				continue
		lineJoined = line1.rstrip("\n") + delim + line2
		fOut.write(lineJoined)	
		countWrote += 1
	sys.stderr.write("wrote %d/%d lines from file1\n" % (countWrote, countLine1))

	if (outer):
		sys.stderr.write("adding %d orphaned lines2\n" % (len(lines2)))
		blank1 = delim*fieldCount1
		for line2 in lines2.values():
			fOut.write(blank1 + line2)		
			countWrote += 1
	else:
		sys.stderr.write("ignoring %d orphaned lines2\n" % (len(lines2)))
			
	sys.stderr.write("wrote %d lines total to %s\n\n\n" % (countWrote, fnOut))


def joinFilesM(fileKeyTups, outfileName, outer=False, header=True, delim="\t"):

	numFiles = len(fileKeyTups)
	infiles = [ open(f, 'r') for f, k in fileKeyTups ]
	keys = [ k for f, k in fileKeyTups ]
	outfile = open(outfileName, 'w')

	keyIdxs = []			
	blanks = [] # need these if we're doing outer
	if (header):
		fieldsAll = []
		for i in range(numFiles):
			fields = infiles[i].readline().rstrip("\n").split(delim)
			blanks.append([""]*len(fields))
			keyIdxs.append(fields.index(keys[i]))
			for field in fields:
				while (field in fieldsAll):
					field += str(i)
				fieldsAll.append(field)
		outfile.write(delim.join(fieldsAll) + "\n")	
	
		sys.stderr.write("outfile fields:\n")
		for f, field in enumerate(fieldsAll):
			sys.stderr.write("\t%2d. %s\n" % (f, field))
			
	else:
		for i in range(numFiles):
			fields = infiles[i].readline().rstrip("\n").split(delim)
			blanks.append([""]*len(fields))
			infiles[i].seek(0)			
			keyIdxs.append(keys[i])	
	
	key_elts = {} # key -> [ field1, field2, ... ]
	sys.stderr.write("reading '%s'\n" % (fileKeyTups[0][0]))
	for line in infiles[0]:		
		elts = line.rstrip("\n").split(delim)
		key = elts[keyIdxs[0]]
		key_elts[key] = elts		

	tossedCounts = [0]*numFiles
	for i in range(1, numFiles):
		sys.stderr.write("have %d rows, attaching '%s'\n" % (len(key_elts), fileKeyTups[i][0]))
		key_eltsNew = {}
		for line in infiles[i]:		
			elts = line.rstrip("\n").split(delim)
			key = elts[keyIdxs[i]]
			if (key in key_elts):
				key_eltsNew[key] = key_elts[key] + elts
				del key_elts[key]
			else:
				if (outer):
					blank = []
					for j in range(i):
						blank.extend(blanks[j])	
					key_elts[key] = blank + elts	
				else:
					tossedCounts[i] += 1
		if (outer):
			for key, elts in key_elts.items():
				key_eltsNew[key] = key_elts[key] + blanks[i]
		else:
			# whatever is left is trash!
			tossedCounts[i-1] += len(key_elts)
		key_elts = key_eltsNew			
				
	for i in range(numFiles):
		sys.stderr.write("tossed %d rows from %s\n" % (tossedCounts[i], fileKeyTups[i][0]))
	sys.stderr.write("finished with %d rows\n" % (len(key_elts)))

	for elts in key_elts.values():
		outfile.write(delim.join(elts) + "\n")
		






abbrev_state = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

state_abbrev = {
		'Washington': 'WA',
		'Wisconsin': 'WI',
		'West Virginia': 'WV',
		'Florida': 'FL',
		'Wyoming': 'WY',
		'New Hampshire': 'NH',
		'New Jersey': 'NJ',
		'New Mexico': 'NM',
		'National': 'NA',
		'North Carolina': 'NC',
		'North Dakota': 'ND',
		'Nebraska': 'NE',
		'New York': 'NY',
		'Rhode Island': 'RI',
		'Nevada': 'NV',
		'Guam': 'GU',
		'Colorado': 'CO',
		'California': 'CA',
		'Georgia': 'GA',
		'Connecticut': 'CT',
		'Oklahoma': 'OK',
		'Ohio': 'OH',
		'Kansas': 'KS',
		'South Carolina': 'SC',
		'Kentucky': 'KY',
		'Oregon': 'OR',
		'South Dakota': 'SD',
		'Delaware': 'DE',
		'District of Columbia': 'DC',
		'Hawaii': 'HI',
		'Puerto Rico': 'PR',
		'Texas': 'TX',
		'Louisiana': 'LA',
		'Tennessee': 'TN',
		'Pennsylvania': 'PA',
		'Virginia': 'VA',
		'Virgin Islands': 'VI',
		'Alaska': 'AK',
		'Alabama': 'AL',
		'American Samoa': 'AS',
		'Arkansas': 'AR',
		'Vermont': 'VT',
		'Illinois': 'IL',
		'Indiana': 'IN',
		'Iowa': 'IA',
		'Arizona': 'AZ',
		'Idaho': 'ID',
		'Maine': 'ME',
		'Maryland': 'MD',
		'Massachusetts': 'MA',
		'Utah': 'UT',
		'Missouri': 'MO',
		'Minnesota': 'MN',
		'Michigan': 'MI',
		'Montana': 'MT',
		'Northern Mariana Islands': 'MP',
		'Mississippi': 'MS'
}


state_abbrev = dict([ (st, ab) for ab, st in abbrev_state.items() ])

def timestamp(length=12, t=None, spaces=False):
	if not (t):
		t = time.localtime()
	if (length == 12):
		return time.strftime("%Y%m%d %H%M", t) if (spaces) else time.strftime("%Y%m%d%H%M", t)
	elif (length == 14):
		return time.strftime("%Y%m%d %H%M%S", t) if (spaces) else time.strftime("%Y%m%d%H%M%S", t)
	elif (length == 8):
		return time.strftime("%Y%m%d", t)
def formatSecs(secs):
	secs = int(secs)
	if (secs < 3600):
		return time.strftime("%M:%S", time.gmtime(secs))
	elif (secs < 86400):
		return time.strftime("%H:%M:%S", time.gmtime(secs))
	else:
		return str(secs/86400) + ":" + time.strftime("%H:%M:%S", time.gmtime(secs%86400))
class Timer:
	def __init__(self):
		self.start = time.time()
	def reset(self):
		self.start = time.time()
	def elapsed(self):
		return time.time() - self.start
	def elapsedPr(self):
		return formatSecs(time.time() - self.start)
	def stderr(self, txt=""):
		sys.stderr.write(self.elapsedPr() + " " + txt + "\n")
tim = Timer()
def elapsedPr():
	return tim.elapsedPr()

def ts():
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def removeNonAscii(s):
	return "".join(i for i in s if (ord(i) < 128))

def removeNonAsciiFromFile(infileName=None, outfileName=None,):
	infile = sys.stdin if (infileName is None) else open(infileName, 'r')
	outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')
	for line in infile:
		outfile.write(removeNonAscii(line))

def countRowsCols(infileName, delim="\t"):
	rowCount = 0
	colCountTotal = 0
	colCountDistrib = {} # col count -> num rows with that col count
	with open(infileName) as infile:
		for line in infile:
			rowCount += 1
			colCount = len(line.split(delim))
			colCountTotal += colCount
			colCountDistrib[colCount] = colCountDistrib.get(colCount, 0) + 1
	colCountAvg = float(colCountTotal) / rowCount
	sys.stderr.write("%s: %d rows, %.2f cols\n" % (infileName, rowCount, colCountAvg))
	for c, r in colCountDistrib.items():
		sys.stderr.write("%10d rows have %d columns\n" % (r, c))
	return rowCount, colCountAvg



		
def factorialList(*paramLists):	
	# sys.stderr.write("paramLists: %s\n" % (str(paramLists)))		
	combos = [ [] ]
	paramListsRev = [x for x in paramLists ]
	paramListsRev.reverse()
	for paramList in paramListsRev:
		# sys.stderr.write("extending combos with %s\n" % (str(paramList)))
		combosNew = []
		for paramVal in paramList:
			for combo in combos:
				comboNew = [paramVal] + combo  
				combosNew.append(comboNew)
		combos = combosNew
	# sys.stderr.write("got %d combos:\n" % (len(combos)))
	# for combo in combos:
	# 	sys.stderr.write("%s\n" % (str(combo)))
	return [ tuple(x) for x in combos ]

# paramListDict: param -> [ setting1, setting2, ... ]
# returns list of dicts param -> setting
def factorialDict(paramListDict):	
	params = sorted(paramListDict.keys())
	paramLists = [ paramListDict[x] for x in params ]
	comboTups = factorialList(*paramLists)
	comboDicts = []
	for comboTup in comboTups:
		comboDicts.append(dict(zip(params, comboTup)))
	return comboDicts
	
def powerSet(lstguy):
	if (len(lstguy) == 0):
		return [[]]
	else:
		car = lstguy[0]
		cdr = lstguy[1:]
		# sys.stderr.write("car: %s, cdr: %s\n" % (car, cdr))
		smaller = powerSet(cdr)
		# sys.stderr.write("smaller: %s\n" % (smaller))	
		# rets = smaller[:]
		# for s in smaller:
		# 	rets.append([car] + s)
		# return rets
		return smaller + [ [car] + s for s in smaller ] 	







