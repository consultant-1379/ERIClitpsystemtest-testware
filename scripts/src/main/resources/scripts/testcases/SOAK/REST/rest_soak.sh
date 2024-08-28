#!/bin/sh
REST_URL="https://localhost:9999/litp/rest/v1" 
REST_BASIC_HEADER="bGl0cC1hZG1pbjpsaXRwX2FkbWlu"

#
# POST operation to create a package list item
# - this is created so that we can change name later via update
#

function wait_for_plan_to_compete {
    running=true
    iter=1
    totaliter=300
    duration=5
    while $running && (( $iter < $totaliter )); do
        iterationdate=$(date)
        echo "Starting wait for plan to complete iteration check: $iter at $iterationdate"
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"type": "plan"}' https://localhost:9999/litp/rest/v1/plans/plan -k  -X GET`
        a=$?
        if [[ $a -ne 0 ]]; then
	    echo "ERROR : curl to perform GET to query plan state failed with return code $a, GET operation returned $out"
        fi    
        if [[ $out == *'"messages"'* ]]; then
            echo "Warning : GET to retrieve plan running state failed, GET operation returned $out"
        else
            echo "Retrieved plan running state"
        fi
        if [[ $out == *'"state": "running"'* ]]; then
            echo "INFO : Plan still running, GET operation returned $out"
        elif [[ $out == *'"state": "successful"'* ]]; then
            running=false
            echo "INFO : Plan has been successful, GET operation returned $out"
        elif [[ $out == *'"state": "failed"'* ]]; then
            running=false
            echo "WARNING : GET to retrieve plan state indicates that plan has failed, GET operation returned $out"
        fi
        [ iter=$[iter++] ]
        sleep $duration
    done
    if $running; then
        totalseconds=$((iter * duration))
        echo "ERROR : Plan is still running after waiting a total of $totalseconds seconds."
        exit
    fi
}

#Remove initial deployment snapshot, usually present on all systems.
out=`curl -H 'Content-Type:application/json'  -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"action" : "remove", "force" : "True"}}' https://localhost:9999/litp/rest/v1/snapshots/snapshot -k -X DELETE`
a=$?
if [[ $a -ne 1 ]]; then
    echo "Removing Initial snapshot from system prior to REST SOAK loop initiation."
    wait_for_plan_to_compete
fi

out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "uPack","type": "package-list","properties": {"name": "uPack"}}' https://localhost:9999/litp/rest/v1/software/items -k`
a=$?
if [ $a -ne 0 ]; then
    echo "ERROR : curl to perform a POST to create package-list uPack gave return code $a, POST operation returned: $out"
fi
if [[ $out == *'"messages"'* ]]; then
    echo "WARNING : POST to create package list failed, POST operation returned: $out"
fi

for (( c=1; c<=50000; c++ ))
#for (( c=1; c<=1; c++ ))
do
    startdate=$(date)
    echo "Starting Iteration $c at $startdate"

    #Create deployment snapshot
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"type": "snapshot-base"}' https://localhost:9999/litp/rest/v1/snapshots/snapshot -k  -X POST`
    a=$?
    if [[ $a -ne 0 ]]; then
	echo "ERROR : curl to perform POST to create deployment snapshot failed with return code $a, POST operation returned $out"
    fi    
    if [[ $out == *'"messages"'* ]]; then
        echo "Warning : POST to create deployment snapshot failed, POST operation returned $out"
    else
        echo "Deployment Snapshot created"
    fi

    # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
    wait_for_plan_to_compete

    #GET snapshot information
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"type": "snapshot-base"}' https://localhost:9999/litp/rest/v1/snapshots/snapshot -k  -X GET`
    a=$?
    if [[ $a -ne 0 ]]; then
	echo "ERROR : curl to perform GET of snapshot information failed with return code $a, GET operation returned $out"
    fi    
    if [[ $out == *'"messages"'* ]]; then
	echo "Warning : GET of deployment snapshot information failed , GET operation returned $out"
    
    else
	echo "Deployment snapshot information printed"
    fi
    
    #Create named snapshot
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"type": "snapshot-base"}' https://localhost:9999/litp/rest/v1/snapshots/X -k  -X POST`
    a=$?
    if [[ $a -ne 0 ]]; then
	echo "ERROR : curl to perform POST to create named backup snapshot failed with return code $a, POST operation returned $out"
    fi    
    if [[ $out == *'"messages"'* ]]; then
	echo "Warning : POST to create named backup snapshot failed, POST operation returned $out"
    else
	echo "Named Backup Snapshot created"
    fi
    
    # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
    wait_for_plan_to_compete
    
    #GET snapshot information
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"type": "snapshot-base"}' https://localhost:9999/litp/rest/v1/snapshots/X -k  -X GET`
    a=$?
    if [[ $a -ne 0 ]]; then
	echo "ERROR : curl to perform GET of snapshot information failed with return code $a, GET operation returned $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
	echo "Warning : GET of named backup snapshot information failed, GET operation returned $out"
    else
	echo "Named backup snapshot information printed"
    fi

    # GET operation to request details of every model item in the deployment
    echo "Performing recursive GET via REST"
    litp show -p / -rl | while read line; do
        out=`curl -X GET -u litp-admin:litp_admin -k ${REST_URL}/${line}`
        a=$?
        if [ $a -ne 0 ]; then
             echo "ERROR : curl to perform a GET on model item $line gave return code $a, GET operation returned: $out"
        fi
        if [[ $out == *'"messages"'* ]]; then
            echo "WARNING : GET of litp mode item, found messages on $line is $out"
        fi
    done
    # Do an update, change force_debug to true
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"force_debug": "true"}}' https://localhost:9999/litp/rest/v1/litp/logging -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a PUT to enable debug logging gave return code $a, PUT operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to update force_debug to true failed, found messages on force_debug update, PUT operation returned: $out"
    fi
    echo "Success update force_debug $out"

    if [ $(($c % 2)) == 0 ]; then
        #  create of package with REST using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "finger","type": "invalid","properties": {"invalid": "finger"}}' https://localhost:9999/litp/rest/v1/software/items -k`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform a POST to create package finger with invalid data gave return code $a, POST operation returned: $out"
        fi
        if [[ $out != *'"InvalidTypeError"'* ]]; then
            echo "WARNING : POST to create package finger with invalid data failed with different error than expected, no 'InvalidTypeError' returned, POST operation returned: $out"
        fi
        echo "'InvalidTypeError' returned when create invalid finger"
        echo "Success Create invalid finger failed $out"
    fi

    #  create of package with REST using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "finger","type": "package","properties": {"name": "finger"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package finger gave return code $a, POST operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : POST to create package finger failed, POST operation returned: $out"
    fi
    echo "Success Create valid finger pass $out"

    if [ $(($c % 3)) == 0 ]; then
        # Inherit the finger package from software/items using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "finger","inherit": "/software/items/invalid_finger"}' https://localhost:9999/litp/rest/v1/deployments/d1/clusters/c1/nodes/n1/items -k`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform a POST to inherit a non-existing package gave return code $a, POST operation returned: $out"
        fi
        if [[ $out != *'"InvalidLocationError"'* ]]; then
            echo "WARNING : POST to inherit a non-existing package failed with different error than expected, no 'InvalidLocationError' returned, POST operation returned: $out"
        fi
        echo "'InvalidLocationError' returned when inherit invalid finger"
        echo "Succcess inherit invalid finger failed $out"
    fi

    # Inherit the finger package from software/items using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "finger","inherit": "/software/items/finger"}' https://localhost:9999/litp/rest/v1/deployments/d1/clusters/c1/nodes/n1/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform POST to inherit package finger gave return code $a, POST operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : POST to inherit package finger failed, POST operation returned: $out"
    fi
    echo "Success inherit valid finger pass $out"

    if [ $(($c % 4)) == 0 ]; then
        #  create plan using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "plan","type": "invalid_plan"}' https://localhost:9999/litp/rest/v1/plans -k`
        a=$?
        if [ $a -ne 0 ]; then
           echo "ERROR : curl to perform POST to create an invalid plan gave return code $a, POST operation returned: $out"
        fi
        if [[ $out != *'"InvalidRequestError"'* ]]; then
            echo "WARNING : POST to create a plan with invalid data failed with a different error than expected, no 'InvalidRequestError' returned, POST operation returned: $out"
        fi
        echo "'InvalidRequestError' returned on invalid create plan"
        echo "Success invalid create plan failed $out"
    fi

    #  create plan using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "plan","type": "plan"}' https://localhost:9999/litp/rest/v1/plans -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform POST to create a plan gave return code $a, POST operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : POST to create a plan failed, POST operation returned: $out"
    fi
    echo "Success valid create plan pass $out"

    if [ $(($c % 5)) == 0 ]; then
        #  run plan using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"state": "invalid"}}' https://localhost:9999/litp/rest/v1/plans/plan -k -X PUT`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform PUT to run an invalid plan gave return code $a, PUT operation returned: $out"
        fi
        if [[ $out != *'"InvalidRequestError"'* ]]; then
            echo "WARNING : PUT to run an invalid plan failed with a different error than expected, no 'InvalidRequestError' returned, PUT operation returned: $out"
        fi
        echo "'InvalidRequestError' returned on invalid run plan"
        echo "Success invalid run plan failed $out"
    fi

    #  run plan using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"state": "running"}}' https://localhost:9999/litp/rest/v1/plans/plan -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT to run a plan gave return code $a, PUT operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to run a plan failed, PUT operation returned: $out"
    fi
    echo "Success valid run plan pass $out"
    # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
    wait_for_plan_to_compete

    if [ $(($c % 6)) == 0 ]; then
        #  remove of inherited finger using invalid data 
        out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/deployments/d1/clusters/c1/nodes/n1/items/invalid_finger -k -X DELETE `
        a=$?
        if [ $a -ne 0 ]; then
           echo "ERROR : curl to perform DELETE to remove an inherited item with an invalid path gave return code $a, DELETE operation returned: $out" 
        fi
        if [[ $out != *'"InvalidLocationError"'* ]]; then
            echo "WARNING : DELETE to remove a non-existant package failed with a different error than expected, no 'InvalidLocationError' returned, DELETE operation returned: $out"
        fi
        echo "'InvalidLocationError' returned on invalid removal of inherited finger"
        echo "Success invalid removal of inherited finger failed $out"
    fi

    #  remove of inherited finger using valid data
    out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/deployments/d1/clusters/c1/nodes/n1/items/finger -k -X DELETE`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform DELETE to remove an inherited item for package finger gave return code $a, DELETE operation returned: $out" 
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : DELETE of inherited package finger failed, DELETE operation returned: $out"
    fi
    echo "Success valid removal of inherited finger pass $out"

    if [ $(($c % 7)) == 0 ]; then
        # remove an item using an invalid path
        out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/software/items/invalid -k -X DELETE`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform DELETE to remove an item with an invalid path gave return code $a, DELETE operation returned: $out" 
        fi
        if [[ $out != *'"InvalidLocationError"'* ]]; then
            echo "WARNING : DELETE of an invalid plan failed with a different error than expected, DELETE operation returned: $out"
        fi
        echo "'InvalidLocationError' returned on invalid removal of finger"
        echo "Success invalid removal of finger failed $out"
    fi

    #  remove of finger using valid data
    out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/software/items/finger -k -X DELETE `
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform DELETE to remove the finger software item gave return code $a, DELETE operation returned: $out" 
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : DELETE of package finger failed, DELETE operation returned: $out"
    fi
    echo "Success valid removal of finger pass $out"

    if [ $(($c % 8)) == 0 ]; then
        #  create plan using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "plan","type": "invalid_plan"}' https://localhost:9999/litp/rest/v1/plans -k`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform POST to create an invalid plan gave return code $a, POST operation returned: $out" 
        fi
        if [[ $out != *'"InvalidRequestError"'* ]]; then
            echo "WARNING : POST to create plan using invalid data failed with different error than expected, no 'InvalidRequestError' returned, POST operation returned: $out"
        fi
        echo "'InvalidRequestError' returned on invalid create plan"
        echo "Success invalid create plan failed $out"
    fi

    # Run the restore_model
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"update_trigger": "yes"}}' https://localhost:9999/litp/rest/v1/litp/restore_model -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT to perform restore_model gave return code $a, PUT operation returned: $out" 
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to restore model failed, PUT operation returned: $out"
    fi
    echo "Success restore_model pass $out"    

    # Check the inherited finger package is in Applied state
    out=`curl -X GET -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/deployments/d1/clusters/c1/nodes/n1/items/finger -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform GET on inherited finger gave return code $a, GET operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : GET of inherited package finger failed, GET operation returned: $out"
    fi
    if [[ $out != *'"Applied"'* ]]; then
        echo "WARNING : GET to ensure inherited package finger is in state Applied failed, GET operation returned: $out"
    fi
    echo "Success valid get of inherited finger pass $out"

    # Check the finger software item package is in Applied state
    out=`curl -X GET -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/software/items/finger -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform GET on software item finger gave return code $a, GET operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : GET of software package finger failed, GET operation returned: $out"
    fi
    if [[ $out != *'"Applied"'* ]]; then
        echo "WARNING : GET to ensure software package finger is in state Applied failed, GET operation returned: $out"
    fi
    echo "Success valid get of software item finger pass $out"

    #  remove of inherited finger using valid data
    out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/deployments/d1/clusters/c1/nodes/n1/items/finger -k -X DELETE`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform DELETE on inherited finger gave return code $a, DELETE operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : DELETE of inherited package finger failed, DELETE operation returned: $out"
    fi
    echo "Success valid removal of inherited finger pass $out"

    #  remove of finger using valid data
    out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' https://localhost:9999/litp/rest/v1/software/items/finger -k -X DELETE `
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform DELETE on software item finger gave return code $a, DELETE operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : DELETE of software package finger failed, DELETE operation returned: $out"
    fi
    echo "Success valid removal of finger pass $out"

    #  create plan using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "plan","type": "plan"}' https://localhost:9999/litp/rest/v1/plans -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform POST to create a valid plan gave return code $a, POST operation returned: $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : POST to create plan failed, POST operation returned: $out"
    fi
    echo "Success valid create plan pass $out"

    if [ $(($c % 9)) == 0 ]; then
        #  run plan using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"state": "invalid"}}' https://localhost:9999/litp/rest/v1/plans/plan -k -X PUT`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform PUT to run an invalid plan gave return code $a, PUT operation returned: $out"
        fi
        if [[ $out != *'"InvalidRequestError"'* ]]; then
            echo "WARNING : PUT to run plan using invalid data failed with a different error than expected, no 'InvalidRequestError' returned, PUT operation returned $out"
        fi
        echo "'InvalidRequestError' returned on invalid run plan"
        echo "Success invalid run plan failed $out"
    fi

    #  run plan using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"state": "running"}}' https://localhost:9999/litp/rest/v1/plans/plan -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT operation to run_plan failed with return code $a, PUT operation returned $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to run plan failed, PUT operation returned $out"
    else
	echo "Success valid run plan pass $out"
    fi
    # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
    wait_for_plan_to_compete

    if [ $(($c % 10)) == 0 ]; then
        # Do an update, change name on package-list using invalid data
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"name": ""}}' https://localhost:9999/litp/rest/v1/software/items/uPack -k -X PUT`
        a=$?
        if [ $a -ne 0 ]; then
            echo "ERROR : curl to perform PUT operation to make an invalid package-list update failed with return code $a, PUT operation returned $out"
        fi
        if [[ $out != *'"ValidationError"'* ]]; then
            echo "WARNING : PUT to update package list name failed with different error than expected, no 'ValidationError' returned, PUT operation returned $out"
        fi
        echo "'ValidationError' returned on invalid package-list update"
        echo "Success invalid package-list update failed $out"
    fi

    # Do an update, change name on package-list using valid data
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"name": "uPack'${c}'"}}' https://localhost:9999/litp/rest/v1/software/items/uPack -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT operation to make a valid update on uPack failed with return code $a, PUT operation returned $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to update package list name failed, PUT operation returned $out"
    else
	echo "Update name of upack successful  $out"
    fi

    # Do an update, change force_debug to false
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"force_debug": "false"}}' https://localhost:9999/litp/rest/v1/litp/logging -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT operation to make a valid update of force_debug to false failed with return code $a, PUT operation returned $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to update force_debug to false failed, PUT operation returned: $out"
    fi
    echo "Success valid update force_debug $out"

    # Do an update, change litp maintenace mode from -> false to -> true and back to -> false
     out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu'  -d '{"properties": {"enabled": "true"}}' https://localhost:9999/litp/rest/v1/litp/maintenance -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT operation to make a valid update maintenance mode to true failed with return code $a, PUT operation returned $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to update force_debug to true failed, PUT operation returned: $out"
    fi
    echo "Success update maintenance mode to $out"

     out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu'  -d '{"properties": {"enabled": "false"}}' https://localhost:9999/litp/rest/v1/litp/maintenance -k -X PUT`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform PUT operation to make a valid update maintenance mode to false failed with return code $a, PUT operation returned $out"
    fi
    if [[ $out == *'"messages"'* ]]; then
        echo "WARNING : PUT to update force_debug to true failed, PUT operation returned: $out"
    fi
    echo "Success update maintenance mode to $out"


    # JUNK Cases
    # JUNK is the corrupt data received from the server side 

    # JUNK : Incomplete Authorization content
#   out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0c' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with corrupt server request gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *"400 Bad Request"* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Incomplete Authorization content' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Incomplete Authorization content' $out"
    
    # JUNK : Missing all Authorization content 
    out=`curl -H 'Content-Type:application/json' -H 'Authorization:' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with corrupt server request gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *"401 Unauthorized"* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Missing all Authorization content' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Missing all Authorization content' $out"

    # JUNK : Incorrect Authorization credentials 
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bbbbcC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with corrupt server request gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *"401 Unauthorized"* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Incorrect Authorization credentials' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Incorrect Authorization credentials' $out"

    # JUNK : No Authorization 
    out=`curl -H 'Content-Type:application/json' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with corrupt server request gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *"401 Unauthorized"* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'No Authorization' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'No Authorization' $out"
    
    # JUNK :  Incomplete Content-Type
    out=`curl -H 'Content-Type:application' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with incomplete content-type data gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"HeaderNotAcceptableError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Incomplete Content-Type' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Incomplete Content-Type' $out"
    
    # JUNK : Missing all Content-Type
    out=`curl -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with incomplete content-type data gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"HeaderNotAcceptableError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Missing all Content-Type' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Missing all Content-Type' $out"
    
    # JUNK :  JUNK Wrong Content-Type value
    out=`curl -H 'Content-Type:text/plain' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with incomplete content-type data gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"HeaderNotAcceptableError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Wrong Content-Type value' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Wrong Content-Type value' $out"
    
    # JUNK :  Missing destination content
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with Missing destination content data gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"InvalidRequestError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Missing destination content' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Missing destination content' $out"
     
    # JUNK :  Incomplete destination content
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with Incomplete destination content data gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"InvalidRequestError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Incomplete destination content' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Incomplete destination content' $out"
    
    # JUNK :  Special char present in destination
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items/* -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with Special char present in destination content data gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"InvalidLocationError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Special char present in destination' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Special char present in destination' $out"
    
    # JUNK :  Half request content
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '' https://localhost:9999/litp/rest/v1/software/items -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with only half request content data - no destination data - gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"InvalidRequestError"'* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Half request content' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Half request content' $out"

    # JUNK :  Destination server incomplete address
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/ -k`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with Destination server incomplete address gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *"404 Not Found"* ]]; then
        echo "WARNING : POST to create package firefox with corrupt server request 'Destination server incomplete address' failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with corrupt server request 'Destination server incomplete address' $out"

    # JUNK : ATTEMPT TO UTILISE TRACE OPTION
    out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"id": "junk_test","type": "package","properties": {"name": "firefox"}}' https://localhost:9999/litp/rest/v1/software/items -k -X TRACE`
    a=$?
    if [ $a -ne 0 ]; then
        echo "ERROR : curl to perform a POST to create package firefox with TRACE enabled gave return code $a, POST operation returned: $out"
    fi
    if [[ $out != *'"MethodNotAllowedError"'* ]]; then
        echo "WARNING : POST to create package firefox with TRACE enabled request failed with different error than expected, POST operation returned: $out"
    fi
    echo "Valid response from server for POST with TRACE enabled request $out"
    if [ $(($c % 2)) == 0 ]; then
        #Remove named snapshot
        out=`curl -H 'Content-Type:application/json'  -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"action" : "remove", "force" : "True"}}' https://localhost:9999/litp/rest/v1/snapshots/X -k -X PUT
`
        a=$?
        if [[ $a -ne 0 ]]; then
            echo "ERROR : curl to perform PUT to force remove named backup snapshot failed with return code $a,  PUT operation returned $out"
        fi    
        if [[ $out == *'"messages"'* ]]; then
            echo "WARNING : PUT to force remove named backup snapshot failed, PUT operation returned $out"
        else
            echo "Named backup snapshot force removed"
        fi
        # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
        wait_for_plan_to_compete

        #Remove snapshot
        out=`curl -H 'Content-Type:application/json'  -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"action" : "remove", "force" : "True"}}' https://localhost:9999/litp/rest/v1/snapshots/snapshot -k -X PUT
`
        a=$?
        if [[ $a -ne 0 ]]; then
            echo "ERROR : curl to perform PUT to remove deployment snapshot failed with return code $a, PUT operation returned $out"
        fi    
        if [[ $out == *'"messages"'* ]]; then
            echo "WARNING : PUT to remove deployment snapshot failed, PUT operation returned $out"
        else
            echo "Deployment snapshot Removed"
        fi
        # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
         wait_for_plan_to_compete
    else
        #Remove named snapshot
        out=`curl -H 'Content-Type:application/json'  -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"action" : "remove", "force" : "True"}}' https://localhost:9999/litp/rest/v1/snapshots/X -k -X DELETE
`
        a=$?
        if [[ $a -ne 0 ]]; then
            echo "ERROR : curl to perform PUT to force remove named backup snapshot failed with return code $a,  DELETE operation returned $out"
        fi    
        if [[ $out == *'"messages"'* ]]; then
	    echo "WARNING : DELETE to force remove named backup snapshot failed, DELETE operation returned $out"
        else
	    echo "Named backup snapshot force removed"
        fi
        # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
        wait_for_plan_to_compete

        #Remove snapshot
        out=`curl -H 'Content-Type:application/json'  -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"properties": {"action" : "remove", "force" : "True"}}' https://localhost:9999/litp/rest/v1/snapshots/snapshot -k -X DELETE
`
        a=$?
        if [[ $a -ne 0 ]]; then
	    echo "ERROR : curl to perform DELETE to remove deployment snapshot failed with return code $a, DELETE operation returned $out"
        fi    
        if [[ $out == *'"messages"'* ]]; then
	    echo "WARNING : DELETE to remove deployment snapshot failed, DELETE operation returned $out"
	
        else
	    echo "Deployment snapshot Removed"
        fi
        # LOOP UNTIL PLAN NO LONGER IN RUNNING STATE
        wait_for_plan_to_compete
        #Get snapshot info snapshot
        out=`curl -H 'Content-Type:application/json' -H 'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' -d '{"type": "snapshot-base"}' https://localhost:9999/litp/rest/v1/snapshots -k  -X GET`
        a=$?
        if [[ $a -ne 0 ]]; then
	    echo "ERROR : curl to perform GET operation of snapshot information failed with return code $a, GET returned $out"
        fi    
        if [[ $out == *'"messages"'* ]]; then
	    echo "WARNING : Get returned snapshot information unexpectedly , GET operation returned $out"
        else
	    echo "all snapshots successfully removed"
        fi
    fi
    finishdate=$(date)
    echo "Completed Iteration $c at $finishdate"

done
