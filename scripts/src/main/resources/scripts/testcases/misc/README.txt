How to use Process Results

Follow the below stops to generate required files for CI:

1) Update generate_items.py with iso, tarball and build numbers for the CI run.

2) Run sh process_results.sh. This script does the following:
> Generates the results email and the results history webpage based on job numbers completed in step 1
> Copies the current failure comments from .30 and loads it into the results_history.html file
> Copies the results history file back onto .30




