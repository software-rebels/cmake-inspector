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
    echo "log:Start analysing $i"

    now=$(date)
    echo "$now:log:cloning $i"
    git clone https://github.com/$i.git -q
    cd ..
    # echo "log:Start analysing $i"
    # echo "git clone https://github.com/$i.git -q"
    echo "python ./extract.py ./$i/"
    python ./extract.py ./$i/ 2>&1 | grep  "^\[enterCommand_invocation\]"  >> ./KDE_command_analysis/ignored_commands.txt
    FILE=./graph.gv
    # First we clone the repository
    if [[ ! -f "$FILE"  ]]; then
        echo "log:Error $i !"
        # python ./extract.py ./$i/
	    echo $i >> ./KDE_command_analysis/issued_repos.txt
    else
        echo "log:Finished $i successfully!"
        name=$(echo $i | tr "/" _)
        # echo "log:Finished $i successfully!"
        mv ./graph.gv ./graph_dots/$name
    fi
    cd KDE
done
cd ..

