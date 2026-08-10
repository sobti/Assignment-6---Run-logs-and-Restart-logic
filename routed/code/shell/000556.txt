#!/bin/bash
#SBATCH --job-name=/data/unibas/boittier/test-neighbours
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=short
#SBATCH --output=/data/unibas/boittier/test-neighbours_%A-%a.out

hostname
#  Path to scripts and executables
cubefit=/home/unibas/boittier/fdcm_project/mdcm_bin/cubefit.x
fdcm=/home/unibas/boittier/fdcm_project/fdcm.x
ars=/home/unibas/boittier/fdcm_project/ARS.py
#  Variables for the job
n_steps=0
n_charges=24
scan_name=SCAN_amide1.pdb-
suffix=.xyz.chk
cubes_dir=/data/unibas/boittier/fdcm/amide/scan-large
output_dir=/data/unibas/boittier/test-neighbours
frames=/home/unibas/boittier/fdcm_project/mdcms/amide/model1/frames.txt
initial_fit=/home/unibas/boittier/fdcm_project/mdcms/amide/model1/24_charges_refined.xyz
initial_fit_cube=/home/unibas/boittier/fdcm_project/mdcms/amide/model1/amide1.pdb.chk
prev_frame=34
start_frame=35
next_frame=36
acd=/home/unibas/boittier/fdcm_project/0_fit.xyz.acd

start=$start_frame
next=$next_frame
dir='frame_'$next
output_name=$output_dir/$dir/$dir'-'$start'-'$next'.xyz'
initial_fit=$output_dir/"frame_"$start/"frame_"$start'-'$prev_frame'-'$start'.xyz'
#  Go to the output directory
mkdir -p $output_dir
cd $output_dir

mkdir -p $dir
cd $dir
# Do Initial Fit
#  for initial fit
esp1=$cubes_dir/$scan_name$start$suffix'.p.cube'
dens1=$cubes_dir/$scan_name$start$suffix'.d.cube'
esp=$cubes_dir/$scan_name$next$suffix'.p.cube'
dens=$cubes_dir/$scan_name$next$suffix'.d.cube'

# adjust reference frame
python $ars -charges $initial_fit -pcube $dens1 -pcube2 $dens -frames $frames -output $output_name -acd $acd > $output_name.ARS.log
# do gradient descent fit
$fdcm -xyz $output_name.global -dens $dens -esp  $esp -stepsize 0.2 -n_steps $n_steps -learning_rate 0.5 -output $output_name > $output_name.GD.log
# adjust reference frame
python $ars -charges $output_name -pcube $esp  -pcube2 $esp -frames $frames -output $output_name -acd $acd > $output_name.ARS-2.log
# make a cube file for the fit
$cubefit -v -generate -esp $esp -dens $dens  -xyz refined.xyz > $output_name.cubemaking.log
# do analysis
$cubefit -v -analysis -esp $esp -esp2 $n_charges'charges.cube' -dens  $dens > $output_name.analysis.log
echo $PWD





sbatch /home/unibas/boittier/fdcm_project/job_files/test-neighbours/frame_35_60.sh 

sbatch /home/unibas/boittier/fdcm_project/job_files/test-neighbours/frame_36_37.sh 
