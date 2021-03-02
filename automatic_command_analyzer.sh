#!/bin/bash
prjs=(  )
prjs=($(cut -d ',' -f2 KDE_command_analysis/repo_list.csv ))


rm -rf KDE/
mkdir KDE
cd KDE
rm .


for i in "${prjs[@]}"
do
    git clone https://github.com/$i.git -q
    cd ..
    pwd
    echo python KDE_command_analysis/visualizeCommands.py ./$i/ true
    # First we clone the repository
    if [[ $(python KDE_command_analysis/visualizeCommands.py ./$i/ true) ]]; then
	    echo $i
        trace=$(python KDE_command_analysis/visualizeCommands.py ./$i/ true)
        ./automatic_issue_report.sh "Repository $i has error" "We still do not analyze the $1 repository well."
    fi
    cd KDE
done
cd ..