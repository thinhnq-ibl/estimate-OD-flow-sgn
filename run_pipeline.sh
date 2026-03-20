#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ========================================================
# AUTOMATED PIPELINE FOR ESTIMATE-OD-FLOW (SINGAPORE)
# ========================================================

echo "========================================="
echo " STEP 1: PROCESSING SHARE_DATA "
echo "========================================="
cd ./share_data
source ../.venv/bin/activate
python 1-get-cell-by-lat-lon.py
python 2_find-cell-in-subzone.py
python 3-get-pois-by-id.py
python 4-get-district-for-cell.py
python 5_sum_count.py
python 6-get-probability-cell.py

echo "========================================="
echo " STEP 2: PROCESSING GEN-CELL-FLOW-FOR-TEST "
echo "========================================="
cd ../gen-cell-flow-for-test
source ../.venv/bin/activate
python 1-find-cell-in-subzone.py
python 2-get-cpc-cell-out.py
python 3-only-get-percent.py

echo "========================================="
echo " STEP 3: PROCESSING GEN-OD-FLOW "
echo "========================================="
cd ../gen-OD-flow
source ../.venv/bin/activate
python 1_sum_count_out.py
python 2-find-cell-out-subzone.py
python 3_share_out_to_cell.py
python 4_sum_each_cell.py
python 5-get-near-cell.py
python 6-calculate-prob-in-per-cell-have-distance.py
python 7-calculate-amount-in-per-cell-have-distance.py
python 8-only-get-percent.py

echo "========================================="
echo " STEP 4: CALCULATING METRICS "
echo "========================================="
cd ../metric
source ../.venv/bin/activate
python CPC.py

echo "========================================="
echo " PIPELINE FINISHED SUCCESSFULLY! "
echo "========================================="
