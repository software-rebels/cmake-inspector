#!/bin/bash
prjs=(  )
prjs=($(cut -d ',' -f2 ./issued_repos.csv ))
cd ..

for i in "${prjs[@]}"
do
    echo "---------$i-------------"
    cd KDE
    git clone https://github.com/$i.git -q
    cd ..
    name=$(echo $i | tr "/" _)
    a=$(python ./extract.py ./$i/ 2>&1 )
    echo $a> "./KDE_command_analysis/issues/$name.txt"
    
done

