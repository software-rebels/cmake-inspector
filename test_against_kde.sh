#!/bin/bash
prjs=(  )
prjs=($(cut -d ',' -f2 ./KDE_command_analysis/repo_list.csv ))


rm -rf KDE/
mkdir KDE
cd KDE
rm .


for i in "${prjs[@]}"
do
    # echo "log:cloning $i"
    git clone https://github.com/$i.git -q
    cd ..
    # echo "log:Start analysing $i"
    python ./extract.py ./$i/ 2>&1 | grep  "^\[enterCommand_invocation\]"
    FILE=./graph.gv
    # First we clone the repository
    if [[ ! -f "$FILE"  ]]; then
        # echo "log:Error $i !"
	    echo $i
    else
        # echo "log:Finished $i successfully!"
        name=$(echo $i | tr "/" _)
        # echo "log:Finished $i successfully!"
        mv ./graph.gv ./graph_dots/$name
    fi
    cd KDE
done
cd ..

