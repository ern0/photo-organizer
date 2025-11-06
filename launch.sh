#!/bin/bash
clear

BASE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $BASE

if [ -f LICENSE ]; then

	rm -rf *.log

	rsync -zar launch.sh phorg.py negro:phorg
	ssh -t negro phorg/launch.sh

	scp negro:/media/storage/home/ern0/full.log .
	cat full.log | grep 'todo' > todo.log

	exit
fi

./phorg.py \
	--dry-run \
	--log /media/storage/home/ern0/full.log \
	--source /media/storage/home/ern0/pixx \
	--target /media/storage/home/ern0/orgpixx \
	--ignore-list \
		pix-select \
		_funi _mixed _tibi_canon_a100 agi_nandipix anim levivasut x y
