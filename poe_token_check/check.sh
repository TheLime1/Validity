#!/bin/bash
DATE=$(cat date.txt)
dotnet DiscordChatExporter.Cli.dll export -t $DTOKEN -c $DCHANNEL --after $DATE -f csv -o chat.csv
NOW=$(date +'%d-%b-%y %I:%M %p')
echo $NOW > date.txt
