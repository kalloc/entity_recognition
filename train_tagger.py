#!/usr/bin/env python3
# 
# many thanks to Mikhail Korobov - http://nbviewer.ipython.org/github/tpeng/python-crfsuite/blob/master/examples/CoNLL%202002.ipynb#

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="infile",
                  help="read data from this file (conll, json; use -j with json data)")
parser.add_option("-x", "--extractor", dest="extractor_module",
                  help="name of feature extractor python module", default="base_extractors")
parser.add_option("-o", "--output", dest="outfile",
                  help="specify destination CRFsuite model file (optional, filename autogenerated if not specified)", default="")
parser.add_option("-c", "--clusters", dest="clusterfile",
                  help="path to brown clusters file")
parser.add_option("-i", "--max-iter", dest="max_iterations",
                  help="number of training iterations", default=50)
parser.add_option("-m", "--min-freq", dest="min_freq",
                  help="minimum number of feature occurrences for inclusion", default=2)
parser.add_option("-V", "--verbose-training", dest="trainer_verbose", action="store_true",
                  help="output crfsuite progress during model training", default=False)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="dump progress info on stderr", default=True)
parser.add_option("-q", "--quiet", dest="verbose", action="store_false",
                  help="don't dump progress info on stderr", default=True)

(options, args) = parser.parse_args()
if not options.infile:
	parser.error('please specify at least an input file (-f)')

import sys
if options.verbose:
	print('init', file=sys.stderr)

import nltk
import pycrfsuite
import time

# local imports
import er

# import feature extraction
try:
	extractors = __import__(options.extractor_module)
except:
	sys.exit('Failed loading the specified feature extractor', sys.exc_info()[0])

try:
	word2features = extractors.word2features
	featurise = extractors.featurise
except:
	sys.exit("Feature extractor didn't fit API as expected")


if options.clusterfile:
	if options.verbose:
		print('reading in brown clusters', file=sys.stderr)
	brown_cluster = er.load_brown_clusters(options.clusterfile)
else:
	brown_cluster = {}

trainer = pycrfsuite.Trainer(verbose=options.trainer_verbose)

if options.verbose:
	print('building feature representations for examples', file=sys.stderr)


file_generator = er.load_conll_file(options.infile)


i = 0
for y, X, entry in file_generator:
	xrepr = featurise(X, brown_cluster)
	trainer.append(xrepr, y)

	i += 1
	if options.verbose:
		if not i % 100:
			print('.', end='', file=sys.stderr)
			if not i % 1000:
				print(i, end='', file=sys.stderr)
			sys.stderr.flush()

if options.verbose:
	print(' ', i, 'example sequences seen', file=sys.stderr)

trainer.set_params({
    'c1': 1.0,   # coefficient for L1 penalty
    'c2': 1e-3,  # coefficient for L2 penalty
    'feature.minfreq': options.min_freq,
    'max_iterations': options.max_iterations,  # stop earlier
    'feature.possible_transitions': True,	# include transitions that are possible, but not observed
    'feature.possible_states': True,			# include states that are possible, but not observed
#    'source_clusters': options.clusterfile,
#    'source_input': options.infile,
#    'source_built': time.strftime('%c'),
})


if options.verbose:
	print('CRF parameters:', trainer.get_params(), file=sys.stderr)

if not options.outfile:
	options.outfile = options.infile.split('/')[-1] + time.strftime('.%Y%m%d-%H%M%S') + '.crfsuite.model'
trainer.train(options.outfile)

if options.verbose:
	print('model written to ' + options.outfile, file=sys.stderr)