#!/bin/bash
# CHECK before each new run:
#   datasets (list of problems)
#   results_dir (where to check/write results),
#   classifiers_to_run (list of classifiers to run)
# While reading is fine, please don't write anything to the default directories in this script

# Start and end for resamples
max_folds=1 # Changed from 30 to single resample for fixed length experiment
start_fold=1

# To avoid dumping 1000s of jobs in the queue we have a higher level queue
max_num_submitted=500

# Queue options are https://sotonac.sharepoint.com/teams/HPCCommunityWiki/SitePages/Iridis%205%20Job-submission-and-Limits-Quotas.aspx
queue="batch"

# The partition name may not always be the same as the queue name, i.e. batch is the queue, serial is the partition
# This is used for the script job limit queue
queue_alias=$queue

# Enter your username and email here
username="ik2g21"
mail="NONE"
mailto="$username@soton.ac.uk"

# MB for jobs, increase incrementally and try not to use more than you need. If you need hundreds of GB consider the huge memory queue.
max_memory=8000

# Max allowable is 60 hours
max_time="60:00:00"

# Start point for the script i.e. 3 datasets, 3 classifiers = 9 jobs to submit, start_point=5 will skip to job 5
start_point=1

# Put your home directory here
local_path="/mainfs/lyceum/$username/aeon"

# Datasets to use and directory of data files. Default is Tony's work space, all should be able to read these. Change if you want to use different data or lists
data_dir="/mainfs/home/ajb2u23/Data" # Path to 112 univariate data and possibly 26 multivariate
datasets="/mainfs/home/ajb2u23/DataSetLists/TSC_112_2019.txt" 

# Results and output file write location. Change these to reflect your own file structure
results_dir="$local_path/ClassificationResults/results/"
out_dir="$local_path/ClassificationResults/output/"

# The python script we are running
script_file_path="$local_path/tsml-eval/tsml_eval/experiments/classification_experiments.py"
second_script_file_path="$local_path/tsml-eval/tsml_eval/_wip/shapelets/fixed_length_STC_eval.py"

# Environment name, change accordingly, for set up, see https://github.com/time-series-machine-learning/tsml-eval/blob/main/_tsml_research_resources/soton/iridis/iridis_python.md
# Separate environments for GPU and CPU are recommended
env_name="tsml-eval"

# Classifiers to loop over. Must be separated by a space
# See list of potential classifiers in set_classifier
classifiers_to_run="stc fixedlengthshapelettransformclassifier dilatedlengthshapelettransformclassifier rdst" # Fixed length experiment

# You can add extra arguments here. See tsml_eval/utils/arguments.py parse_args
# You will have to add any variable to the python call close to the bottom of the script
# and possibly to the options handling below

# Generate a results file for the train data as well as test, usually slower
generate_train_files="false"

# If set for true, looks for <problem><fold>_TRAIN.ts file. This is useful for running tsml-java resamples
predefined_folds="false"

# Normalize data before fit/predict
normalise_data="false"

# ======================================================================================
# ======================================================================================
# Don't change anything under here (unless you want to change how the experiment
# is working)
# ======================================================================================
# ======================================================================================

# Set to -tr to generate test files
generate_train_files=$([ "${generate_train_files,,}" == "true" ] && echo "-tr" || echo "")

# Set to -pr to use predefined folds
predefined_folds=$([ "${predefined_folds,,}" == "true" ] && echo "-pr" || echo "")

# Set to -rn to normalize data
normalise_data=$([ "${normalise_data,,}" == "true" ] && echo "-rn" || echo "")

count=0
while read dataset; do
    for classifier in $classifiers_to_run; do

        # Skip to the script start point
        ((count++))
if ((count>=start_point)); then

            # This is the loop to keep from dumping everything in the queue which is maintained around max_num_submitted jobs
            num_jobs=$(squeue -u ${username} --format="%20P %5t" -r | awk '{print $2, $1}' | grep -e "R ${queue_alias}" -e "PD ${queue_alias}" | wc -l)
while [ "${num_jobs}" -ge "${max_num_submitted}" ]
do
    echo Waiting 60s, "${num_jobs}" currently submitted on ${queue}, user-defined max is ${max_num_submitted}
                sleep 60
                num_jobs=$(squeue -u ${username} --format="%20P %5t" -r | awk '{print $2, $1}' | grep -e "R ${queue_alias}" -e "PD ${queue_alias}" | wc -l)
            done

            mkdir -p "${out_dir}${classifier}/${dataset}/"

            # This skips jobs which have test/train files already written to the results directory. Only looks for Resamples, not Folds (old file name)
            array_jobs=""
for (( i=start_fold-1; i<max_folds; i++ ))
do
                if [ -f "${results_dir}${classifier}/Predictions/${dataset}/testResample${i}.csv" ]; then
                    if [ "${generate_train_files}" == "true" ] && ! [ -f "${results_dir}${classifier}/Predictions/${dataset}/trainResample${i}.csv" ]; then
                        array_jobs="${array_jobs}${array_jobs:+,}$((i + 1))"
                    fi
                else
                    array_jobs="${array_jobs}${array_jobs:+,}$((i + 1))"
                fi
            done

if [ "${array_jobs}" != "" ]; then

                # Determine if length_selector argument should be included
                if [ "$classifier" == "fixedlengthshapelettransformclassifier" ]; then
                    length_selector="--kwargs length_selector FIXED str"
                elif [ "$classifier" == "dilatedlengthshapelettransformclassifier" ]; then
                    length_selector="--kwargs length_selector DILATED str"
                else
                    length_selector=""
                fi

                # This creates the script to run the job based on the info above
                echo "#!/bin/bash
#SBATCH --mail-type=${mail}
#SBATCH --mail-user=${mailto}
#SBATCH -p ${queue}
#SBATCH -t ${max_time}
#SBATCH --job-name=${classifier}${dataset}
#SBATCH --array=${array_jobs}
#SBATCH --mem=${max_memory}M
#SBATCH -o ${out_dir}${classifier}/${dataset}/%A-%a.out
#SBATCH -e ${out_dir}${classifier}/${dataset}/%A-%a.err
#SBATCH --nodes=1

. /etc/profile

module load anaconda/py3.10
source activate $env_name

# Input args to the default classification_experiments are in main method of
# https://github.com/time-series-machine-learning/tsml-eval/blob/main/tsml_eval/experiments/classification_experiments.py
python -u ${script_file_path} ${data_dir} ${results_dir} ${classifier} ${dataset} \$((\$SLURM_ARRAY_TASK_ID - 1)) ${generate_train_files} ${predefined_folds} ${normalise_data} ${length_selector}" > generatedFile.sub

                echo "${count} ${classifier}/${dataset}"
                sbatch < generatedFile.sub

            else
    echo "${count} ${classifier}/${dataset}" has finished all required resamples, skipping
            fi
        fi
    done
done < ${datasets}

echo Finished submitting jobs

### OPTIONAL: wait for all jobs to complete
# Wait for most jobs to finish
echo "Waiting for most jobs to complete..."
while true; do
    # Get the number of jobs for the user
    JOB_COUNT=$(squeue -u ${username} | grep -v "JOBID" | wc -l)

    # Check if the job count is less than or equal to MAX_JOBS
    if [ "$JOB_COUNT" -le "30" ]; then
        echo "Number of jobs is now $JOB_COUNT, which is less than or equal to $MAX_JOBS."
        break
    fi

    echo "Some jobs are still running:"
    squeue -u ${username}
    echo "Waiting for jobs to complete..."
    sleep 120
done

# Run the second Python script
echo "Running second Python script..."
mkdir -p "${local_path}/ClassificationResults/evaluated_results/bashoutput"
# This creates the script to run the job based on the info above
echo "#!/bin/bash
#SBATCH --mail-type=${mail}
#SBATCH --mail-user=${mailto}
#SBATCH -p ${queue}
#SBATCH -t ${max_time}
#SBATCH --job-name=result_eval
#SBATCH --mem=${max_memory}M
#SBATCH -o ${local_path}/ClassificationResults/evaluated_results/bashoutput/%A-%a.out
#SBATCH -e ${local_path}/ClassificationResults/evaluated_results/bashoutput/%A-%a.err
#SBATCH --nodes=1

. /etc/profile

module load anaconda/py3.10
source activate $env_name

# Input args to the default classification_experiments are in main method of
# https://github.com/time-series-machine-learning/tsml-eval/blob/main/tsml_eval/experiments/classification_experiments.py
python -u ${second_script_file_path}" > generatedFile2.sub

sbatch < generatedFile2.sub
echo "Second Python script finished."
