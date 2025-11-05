#!/bin/bash
clear

BASE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $BASE

if [ -f LICENSE ]; then
	rsync -zar launch.sh phorg.py negro:phorg
	ssh -t negro phorg/launch.sh
	exit
fi

./phorg.py \
	--dry-run \
	--log /media/storage/home/ern0/phorg.log \
	--source /media/storage/home/ern0/pixx \
	--target /media/storage/home/ern0/orgpixx
