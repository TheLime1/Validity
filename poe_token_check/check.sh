#!/bin/bash
DATE=$(cat date.txt)
dotnet DiscordChatExporter.Cli.dll export -t ${{ secrets.DTOKEN }} -c ${{ secrets.DCHANNEL }} --after $DATE
NOW=$(date +"%Y-%m-%d")
echo $NOW > date.txt
