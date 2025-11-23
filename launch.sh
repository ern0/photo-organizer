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
		/media/storage/home/ern0/pixx/pix-select \
		/media/storage/home/ern0/pixx/pix1/0_misc/_funi \
		/media/storage/home/ern0/pixx/pix1/0_misc/_mixed \
		/media/storage/home/ern0/pixx/pix1/0_misc/_tibi_canon_a100 \
		/media/storage/home/ern0/pixx/pix1/0_misc/anim \
		/media/storage/home/ern0/pixx/pix1/0_misc/levivasut \
		/media/storage/home/ern0/pixx/pix1/0_misc/x \
		/media/storage/home/ern0/pixx/pix1/0_misc/y
