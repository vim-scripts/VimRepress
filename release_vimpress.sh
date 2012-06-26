#!/bin/bash


TEMP_DIR=/tmp/vimpress_relase
REV=`hg summary|grep -e "^parent"|awk '{print $2}'|tr ':' '_'`
BRANCH=`hg branch`
hg archive $TEMP_DIR
VER=`grep Version plugin/vimrepress.vim | awk '{print $3}'`
RELEASE_FILE="/tmp/"$BRANCH"_"$VER"_r"$REV".zip"
cd $TEMP_DIR
if [[ -f $RELEASE_FILE ]]; then rm $RELEASE_FILE; fi
zip -x 'README.md' -x '.hgtags' -x '.hg_archival.txt' -x markdown_posts_upgrade.py -x release_vimpress.sh -r $RELEASE_FILE .
rm -rf $TEMP_DIR
echo $RELEASE_FILE


