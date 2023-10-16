#!/bin/sh
if [ $# != 2 ];
then
	echo "Usage: ./run.sh input_dir output_dir"
	echo "e.g. ./run.sh input output"
	exit 1
fi

INDIR=$1
OUTDIR=$2

# echo "Remove existing *txt files"
# /bin/rm *.txt

if [ ! -d ${OUTDIR} ];
then
# 	echo "Remove existing output files in output dir"
# 	/bin/rm -rf ${OUTDIR}/*html
# else
	echo "\nCreating output directory ${OUTDIR}"
	mkdir ${OUTDIR}
fi

python invertedfile.py ${INDIR} ${OUTDIR}

echo "Done. Goodluck :-)"
