#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ========================================================
# AUTOMATED PIPELINE FOR ESTIMATE-OD-FLOW (SINGAPORE)
# ========================================================

echo "========================================="
echo " STEP 3: PROCESSING GEN-CELL-FLOW-FOR-TEST "
echo "========================================="
cd ./gen-cell-flow-for-test
source ../.venv/bin/activate
python 1-get-cpc-cell-out.py
python 2-get-cell-out.py
python 3-only-get-percent.py

echo "========================================="
echo " STEP 4: PROCESSING GEN-OD-FLOW "
echo "========================================="
cd ../gen-OD-flow
source ../.venv/bin/activate
python 1-get-out-cell.py
python 2-get-near-cell.py
python 3-calculate-prob-in-per-cell-have-distance.py
python 4-calculate-amount-in-per-cell-have-distance.py
python 5-only-get-percent.py

echo "========================================="
echo " STEP 5: CALCULATING METRICS "
echo "========================================="
cd ../metric
source ../.venv/bin/activate
python CPC.py

echo "========================================="
echo " PIPELINE FINISHED SUCCESSFULLY! "
echo "========================================="