# Very basic same command in parallel

#!/bin/bash
set -x
hour="00"
litp update -p /litp/logging -o force_debug=false
for (( c=1; c<=200000; c++ ))
do
# Do something on first itteration each hour
    if [ $hour != $(date +%H) ]
        then
        hour=$(date +%H)    
        echo "iteration count=" $c " date = "  $(date)
        #Get number of open files    
        status=$(service litpd status)
        pid=$(echo $status  | tr -dc '0-9') 
        lsof=$(lsof -p $pid)
        losf_wc=$(lsof -p $pid | wc -l)
        ls_proc=$(ls -l /proc/${pid}/fd)
        echo "losf_file_count = " $losf_wc "loop count=" $c " date = "  $(date)
    fi

# CLI Positive
    litp create -p /software/items/cpack${c} -t package-list -o name=cpack${c}
    litp create -p /software/items/cpack${c}/packages/cpack${c} -t package -o name=cpack${c}
    litp inherit -p /deployments/d1/clusters/c1/nodes/n1/items/cpack${c} -s /software/items/cpack${c}
    date #CLI
# REST Positve
    curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "rpack'${c}'","type": "package-list","properties": {"name": "rpack'${c}'"}}' https://localhost:9999/litp/rest/v1/software/items -k
    curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "rpack'${c}'","type": "package","properties": {"name": "rpack'${c}'"}}' https://localhost:9999/litp/rest/v1/software/items/rpack${c}/packages -k
    litp inherit -p /deployments/d1/clusters/c1/nodes/n1/items/rpack${c} -s /software/items/rpack${c} 
    date #REST
# XML Positive
  # XML Load file without arguments
    cp addPackList.xml addPackList${c}.xml
    sed -i "s/telnet/XML_load${c}/" addPackList${c}.xml  
    litp load -p /software/items -f addPackList${c}.xml

  # XML litp load with --merge
    cp addPackage.xml addPackage${c}.xml
    sed -i "s/telnet/XML_merge${c}/" addPackage${c}.xml
    litp load -p /software/items/XML_load${c}/packages -f addPackage${c}.xml --merge
    litp inherit -p /deployments/d1/clusters/c1/nodes/n1/items/XML${c} -s /software/items/XML_load${c}
  
  # XML litp export
    litp export -p /software/items -f xml_export_items${c}.xml 

  # XML litp load with --replace
    # "XML_replace" will replace the item "XML_merge" in model
    sed -i "s/XML_merge${c}/XML_replace${c}/" xml_export_items${c}.xml 
    litp load -p /software/ -f xml_export_items${c}.xml --replace
    date #XML
    n=$((c%5))
    if [ $n -eq 0 ]; then
       # CLI negative
        litp create -p /software/items/BAD_CLI -t NOT-package- -o name=cpack_BAD${c}
        if [ $? -ne 1 ]; 
            then echo "Error CLI_01 unexpected error code. Expected 1 got " $? 
        fi

        litp create -p /software/items/cpack${c}/packages/BAD_CLI -t package -o name=cpack_BAD${c} version=1.4.2@
        if [ $? -ne 1 ]; 
            then echo "Error CLI_02 unexpected error code. Expected 1 got " $? 
        fi

        litp inherit -p /deployments/d1/clusters/c1/nodes/n1/items/BAD_CLI -s /software/items/BAD_CLI
        if [ $? -ne 1 ]; 
            then echo "Error CLI_03 unexpected error code. Expected 1 got " $? 
        fi

        date #CLI_neg
        # XML negative 
        litp load -p /software/items -f bad_pkg_01.xml --replace
        if [ $? -ne 1 ]; 
            then echo "Error XML_01 ${c} unexpected error code. Expected 1 got " $? 
        fi

        litp load -p /software/items -f bad_pkg_02.xml --merge
        if [ $? -ne 1 ]; 
            then echo "Error XML_02 ${c} unexpected error code. Expected 1 got " $? 
        fi

        litp load -p /software/items -f bad_pkg_03.xml --replace
        if [ $? -ne 1 ]; 
            then echo "Error XML_03 ${c} unexpected error code. Expected 1 got " $? 
        fi

        litp load -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces  -f bad_readonly_bridge_04.xml --replace # expects item "br1"     to already exist
        if [ $? -ne 1 ]; 
            then echo "Error XML_04 ${c} unexpected error code. Expected 1 got " $? 
        fi

        litp load -p /deployments/d1/clusters/c1/nodes/n1/system/disks/ -f bad_readonly_disk_type_05.xml --replace # expects item "disk0_1" to already exist and for disk_type=true
        if [ $? -ne 1 ]; 
            then echo "Error XML_05 ${c} unexpected error code. Expected 1 got " $? 
        fi

        # Load XML package into incorrect #1
        litp load -p /ms -f addPackage${c}.xml --merge    
        if [ $? -ne 1 ];
            then echo "Error XML_06 ${c} unexpected error code. Expected 1 got " $? 
        fi

        # Load XML package into incorrect location #2
        litp load -p /plans/plan/ -f addPackage${c}.xml --merge
        if [ $? -ne 1 ];
            then echo "Error XML_07 ${c} unexpected error code. Expected 1 got " $? 
        fi

        # incomplete XMl file with merge
        cp xml_incomplete.xml xml_incomplete${c}.xml
        sed -i "s/telnet/XML_load_incomplete${c}/" xml_incomplete${c}.xml
        litp load -p /software/items/ -f xml_incomplete${c}.xml --merge                                  
        if [ $? -ne 1 ];
            then echo "Error XML_08 ${c} unexpected error code. Expected 1 got " $? 
        fi

        # incomplete XMl file with replace
        cp xml_incomplete.xml xml_incomplete${c}.xml
        sed -i "s/telnet/XML_load_incomplete${c}/" xml_incomplete${c}.xml
        litp load -p /software/items/ -f xml_incomplete${c}.xml --replace
        if [ $? -ne 1 ];
            then echo "Error XML_09 ${c} unexpected error code. Expected 1 got " $?
        fi
        # Try load command with incorrect argument
        cp addPackList.xml addPackList_inc_arg${c}.xml
        sed -i "s/telnet/XML_load_no_merge${c}/" addPackList_inc_arg${c}.xml
        litp load -p /software/items/ -f addPackList_inc_arg{c}.xml --Incarg
        if [ $? -ne 2 ];
            then echo "Error XML_10 ${c} unexpected error code. Expected 2 got " $? 
        fi

        date #XML_neg
    fi

# Create and show plan
    litp show -p /software/items -r
    date #create_plan
    litp create_plan
    date #show_plan
    litp show_plan
    litp remove_plan

  # CLI Cleanup
    litp remove -p /software/items/cpack${c}

  # REST Cleanup
    curl -X DELETE -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/software/items/rpack${c} -k

  # XML Cleanup
    rm -f addPackage${c}.xml
    rm -f addPackList${c}.xml
    rm -f xml_export_items${c}.xml
    rm -f xml_incomplete${c}.xml
    rm -f addPackList_inc_arg${c}.xml
    curl -X DELETE -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/software/items/XML_load${c} -k
    date #cleanup
    # cleanup litp core files
    n=$((c%100))
    if [ $n -eq 0 ]; then
        rm -f /var/lib/litp/core/model/_load_snapshot_*
        rm -f /var/lib/litp/core/model/201*
    fi
done


