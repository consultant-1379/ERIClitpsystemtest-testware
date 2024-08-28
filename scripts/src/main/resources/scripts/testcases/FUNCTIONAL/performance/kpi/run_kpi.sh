#!/bin/bash

echo "Run LITP KPI Key Operations"

echo "XML Operations"
echo "XML Merge"
sh /tmp/kpi/xml.sh merge 10
sleep 10
echo "XML Replace"
sh /tmp/kpi/xml.sh replace 10
sleep 10

echo "Snapshot Operations"
echo "Remove Snapshot"
sh /tmp/kpi/snapshot.sh
sleep 10
echo "Create Snapshot" 
sh /tmp/kpi/snapshot.sh
sleep 10

echo "Import / Upgrade Operations"
echo "Import ISO"
sh /tmp/kpi/import.sh iso /tmp/kpi/ERICenm_CXP9027091-1.10.57.iso
sleep 10
echo "Import OS Tarball"
sh /tmp/kpi/import.sh tarball /tmp/kpi/ERICrhel_CXP9026826-3.0.5.tar.gz
sleep 10
echo "Import RPM"
sh /tmp/kpi/import.sh rpm /tmp/kpi/java-1.6.0-openjdk-1.6.0.0-1.41.1.10.4.el6.x86_64.rpm
sleep 10

echo "LITPD SERVICE RESTART"
sh /tmp/kpi/litpd_restart.sh 10
sleep 10

echo "BUR Operations"
echo "Prepare Restore"
sh /tmp/kpi/prepare_restore.sh
sleep 10

echo "KPI RUN COMPLETE"

echo "Removing /tmp/kpi/ files"
rm -rf /tmp/kpi/*
