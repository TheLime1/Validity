#!/bin/bash
dotnet DiscordChatExporter.Cli.dll export -t ${{ secrets.DTOKEN }} -c ${{ secrets.DCHANNEL }}
