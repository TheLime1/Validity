#!/bin/bash
DATE=$(cat date.txt)
dotnet DiscordChatExporter.Cli.dll export -t $DTOKEN -c $DCHANNEL --after $DATE
NOW=$(date +"%Y-%m-%d")
echo $NOW > date.txt
