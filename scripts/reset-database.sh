#!/bin/bash
bak= $pwd
cd ../data/db/
rm -fr dumps
rm -f virtuoso.db
rm -f virtuoso.lck
rm -f virtuoso.log
rm -f virtuoso.pxa
rm -f virtuoso-temp.db
rm -f virtuoso.trx
rm -f .config_set .data_loaded .dba_pwd_set
cd "$bak"
