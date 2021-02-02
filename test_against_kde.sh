#!/bin/bash
prjs=(  )
prjs=($(cut -d ',' -f2 repo_list.csv ))


rm -rf KDE/
mkdir KDE
cd KDE
rm .


for i in "${prjs[@]}"
do
    git clone https://github.com/$i.git -q
    cd ..
    # First we clone the repository
    if [[ $(python ./extract.py ./$i/ 2>&1 | grep  "^line") ]]; then
	    echo $i
    fi
    cd KDE
done
cd ..

