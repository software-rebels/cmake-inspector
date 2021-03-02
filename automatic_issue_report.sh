#!/usr/bin/env bash
rawurlencode() {
  local string="${1}"
  local strlen=${#string}
  local encoded=""
  local pos c o

  for (( pos=0 ; pos<strlen ; pos++ )); do
     c=${string:$pos:1}
     case "$c" in
        [-_.~a-zA-Z0-9] ) o="${c}" ;;
        * )               printf -v o '%%%02x' "'$c"
     esac
     encoded+="${o}"
  done
  echo "${encoded}"    # You can either set a return variable (FASTER) 
  REPLY="${encoded}"   #+or echo the result (EASIER)... or both... :p
}
token="210aadaa71d6004ccdf76fd77014483098a377d2"
owner="software-rebels"
repo="cmake-inspector"
curl  -H "Authorization: token $token" -X POST -i -d "{\"title\":\"${1}\",\"body\":\"$2\",\"labels\": $3}" https://api.github.com/repos/${owner}/${repo}/issues
# echo "curl  -H \"Authorization: token $token\" -X POST -i -d \"{\"title\":\"${1}\",\"body\":\"$2\",\"labels\": $3}\" https://api.github.com/repos/${owner}/${repo}/issues"
# $(curl  -H "Authorization: token $token" -X POST -i -d "{\"title\":\"${1}\",\"body\":\"$2\",\"labels\": $3}" https://api.github.com/repos/$owner/$repo/issues)